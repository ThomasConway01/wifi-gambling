"""
High-performance Network scanner for discovering LAN devices,
resolving hostnames & vendors, and syncing with the SQLite device registry.
"""

import subprocess
import re
import socket
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.database import (
    get_connection,
    get_setting,
    calculate_next_monthly_reset,
    log_event
)
from app.vendor_db import lookup_vendor, guess_device_type
from app.roulette import format_hours_minutes

try:
    import dns.resolver
    import dns.reversename
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False

_DNS_RESOLVER = None

def get_resolver(gateway_ip: str = "192.168.1.1"):
    global _DNS_RESOLVER
    if _DNS_RESOLVER is None and HAS_DNSPYTHON:
        try:
            _DNS_RESOLVER = dns.resolver.Resolver(configure=False)
            _DNS_RESOLVER.nameservers = [gateway_ip, "192.168.1.1"]
            _DNS_RESOLVER.timeout = 0.2
            _DNS_RESOLVER.lifetime = 0.2
        except Exception:
            _DNS_RESOLVER = None
    return _DNS_RESOLVER

def get_host_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        host_ip = s.getsockname()[0]
    except Exception:
        host_ip = "127.0.0.1"
    finally:
        s.close()
    return host_ip

def get_default_gateway() -> str:
    try:
        out = subprocess.check_output("ipconfig", shell=True, text=True)
        gateways = re.findall(r"Default Gateway[ .:]+: ([0-9.]+)", out)
        if gateways and gateways[0] != "0.0.0.0":
            return gateways[0]
    except Exception:
        pass
    return "192.168.1.1"

def get_host_mac() -> str:
    try:
        raw_mac = uuid.getnode()
        mac = ":".join(f"{(raw_mac >> ele) & 0xff:02x}" for ele in range(0, 8 * 6, 8))[::-1]
        return mac.lower()
    except Exception:
        return "00:00:00:00:00:00"

def resolve_hostname(ip: str, gateway_ip: str = "192.168.1.1") -> str:
    """Fast non-blocking reverse DNS hostname resolution directly via gateway."""
    res = get_resolver(gateway_ip)
    if res:
        try:
            rev_name = dns.reversename.from_address(ip)
            answers = res.resolve(rev_name, 'PTR')
            h = str(answers[0]).rstrip('.')
            if h.endswith(".localdomain"):
                h = h[:-12]
            return h
        except Exception:
            return ""
    return ""

def scan_arp_table(host_ip: str) -> List[Dict[str, str]]:
    """Parses local ARP table for dynamic devices on the local subnet."""
    try:
        output = subprocess.check_output("arp -a", shell=True, text=True)
    except Exception:
        return []

    # Get subnet prefix, e.g. "192.168.1."
    subnet_prefix = ".".join(host_ip.split(".")[:3]) + "."

    devices = []
    seen_macs = set()

    for line in output.splitlines():
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+(\w+)", line)
        if not match:
            continue

        ip, raw_mac, kind = match.groups()
        mac = raw_mac.replace("-", ":").lower()

        # ONLY accept unicast addresses in the local subnet
        if not ip.startswith(subnet_prefix):
            continue

        if (
            ip.endswith(".255")
            or mac == "ff:ff:ff:ff:ff:ff"
            or mac.startswith("01:00:5e")  # Multicast MAC
            or mac in seen_macs
        ):
            continue

        seen_macs.add(mac)
        devices.append({"ip": ip, "mac": mac, "kind": kind})

    return devices

def scan_and_sync_network() -> List[Dict[str, Any]]:
    """
    Scans the local network, resolves vendors and hostnames,
    updates the database, and returns all registered devices.
    """
    host_ip = get_host_ip()
    host_mac = get_host_mac()
    gateway_ip = get_default_gateway()

    arp_devs = scan_arp_table(host_ip)
    now_iso = datetime.now(timezone.utc).isoformat()
    default_hours = float(get_setting("default_allowance_hours", 168.0))
    default_seconds = default_hours * 3600.0
    next_reset = calculate_next_monthly_reset()

    # Fast sequential DNS resolution (0.001s each directly from gateway cache)
    for d in arp_devs:
        d["hostname"] = resolve_hostname(d["ip"], gateway_ip)

    conn = get_connection()
    c = conn.cursor()

    for d in arp_devs:
        mac = d["mac"]
        ip = d["ip"]
        hostname = d.get("hostname", "")
        vendor = lookup_vendor(mac)
        dev_type = guess_device_type(hostname, vendor)

        is_gateway = 1 if ip == gateway_ip else 0
        is_host = 1 if (ip == host_ip or mac == host_mac) else 0
        is_protected = 1 if (is_gateway or is_host) else 0

        # Check if already in DB
        c.execute("SELECT * FROM devices WHERE mac = ?", (mac,))
        existing = c.fetchone()

        if existing:
            # Update IP, hostname, last seen
            c.execute("""
            UPDATE devices
            SET ip = ?, hostname = COALESCE(NULLIF(?, ''), hostname),
                vendor = ?, last_seen_at = ?, updated_at = ?
            WHERE mac = ?
            """, (ip, hostname, vendor, now_iso, now_iso, mac))
        else:
            # Insert fresh device with full monthly allowance
            initial_status = "PROTECTED" if is_protected else "ACTIVE"
            c.execute("""
            INSERT INTO devices (
                mac, ip, hostname, custom_name, vendor, device_type,
                is_gateway, is_host, is_protected, status,
                base_allowance_hours, remaining_seconds, reset_interval,
                next_reset_at, last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mac, ip, hostname, "", vendor, dev_type,
                is_gateway, is_host, is_protected, initial_status,
                default_hours, default_seconds, "monthly",
                next_reset, now_iso, now_iso, now_iso
            ))
            log_event(
                "DEVICE_DISCOVERED",
                f"Discovered new device {hostname or ip} ({mac}) - {vendor}",
                device_mac=mac,
                details={"ip": ip, "vendor": vendor, "type": dev_type},
                conn=conn
            )

    conn.commit()

    # Fetch all devices
    c.execute("""
    SELECT * FROM devices
    ORDER BY is_gateway DESC, is_host DESC, status DESC, ip ASC
    """)
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        d_dict = dict(r)
        d_dict["is_gateway"] = bool(d_dict["is_gateway"])
        d_dict["is_host"] = bool(d_dict["is_host"])
        d_dict["is_protected"] = bool(d_dict["is_protected"])
        d_dict["decay_enabled"] = bool(d_dict["decay_enabled"])
        d_dict["remaining_hours"] = round(d_dict["remaining_seconds"] / 3600.0, 2)
        d_dict["remaining_formatted"] = format_hours_minutes(d_dict["remaining_seconds"])
        result.append(d_dict)

    return result
