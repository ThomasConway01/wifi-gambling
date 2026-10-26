"""
Enforcement Manager: instantiates and coordinates the active network enforcement driver.
"""

from typing import Tuple, Optional
import sqlite3
from app.database import get_setting, get_all_settings, log_event
from app.enforcement.driver_base import BaseEnforcementDriver
from app.enforcement.simulator import SimulationDriver
from app.enforcement.unifi import UniFiDriver
from app.enforcement.webhook import WebhookDriver
from app.enforcement.firewall import FirewallDriver

def get_active_driver() -> BaseEnforcementDriver:
    settings = get_all_settings()
    mode = settings.get("enforcement_mode", "simulation").lower()

    if mode == "unifi":
        return UniFiDriver(
            host=settings.get("unifi_host", "https://192.168.1.1"),
            username=settings.get("unifi_username", ""),
            password=settings.get("unifi_password", ""),
            site=settings.get("unifi_site", "default"),
            verify_ssl=bool(settings.get("unifi_verify_ssl", False))
        )
    elif mode == "webhook":
        return WebhookDriver(
            block_cmd=settings.get("webhook_block_cmd", ""),
            unblock_cmd=settings.get("webhook_unblock_cmd", "")
        )
    elif mode == "firewall":
        return FirewallDriver()
    else:
        return SimulationDriver()

def enforce_block(mac: str, ip: str = "", hostname: str = "", conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
    driver = get_active_driver()
    success, message = driver.block_device(mac, ip, hostname)
    log_event(
        "ENFORCEMENT_ACTION",
        f"Block action: {message}",
        device_mac=mac,
        details={"action": "block", "ip": ip, "hostname": hostname, "success": success},
        conn=conn
    )
    return success, message

def enforce_unblock(mac: str, ip: str = "", hostname: str = "", conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
    driver = get_active_driver()
    success, message = driver.unblock_device(mac, ip, hostname)
    log_event(
        "ENFORCEMENT_ACTION",
        f"Unblock action: {message}",
        device_mac=mac,
        details={"action": "unblock", "ip": ip, "hostname": hostname, "success": success},
        conn=conn
    )
    return success, message

def test_driver() -> Tuple[bool, str]:
    driver = get_active_driver()
    return driver.test_connection()
