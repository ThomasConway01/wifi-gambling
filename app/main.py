"""
FastAPI application for WiFi Time Roulette / Bandwidth Casino.
"""

import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    init_db,
    get_connection,
    get_setting,
    set_setting,
    get_all_settings,
    calculate_next_monthly_reset,
    log_event
)
from app.models import (
    DeviceModel,
    DeviceUpdateRequest,
    SpinRequest,
    SpinResponse,
    SettingsUpdateRequest,
    AdminActionRequest,
    TestEnforcementRequest
)
from app.scanner import (
    scan_and_sync_network,
    get_host_ip,
    get_host_mac,
    get_default_gateway
)
from app.roulette import (
    spin_wheel,
    evaluate_bet,
    get_number_color,
    format_hours_minutes,
    RED_NUMBERS,
    BLACK_NUMBERS
)
from app.enforcement.manager import enforce_block, enforce_unblock, test_driver
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB & Seed
    init_db()
    # Scan network on startup
    try:
        scan_and_sync_network()
    except Exception as e:
        print(f"[Startup Scan Error] {e}")
    # Start background scheduler
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="WiFi Time Roulette",
    description="Gamble your remaining monthly WiFi hours on the roulette wheel.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# ----------------- Device Endpoints -----------------

@app.get("/api/me")
def get_current_device(request: Request):
    """
    Returns the device object for the device currently viewing/interacting with the app.
    Automatically resolves the host machine or visiting device on Wi-Fi.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    host_ip = get_host_ip()
    host_mac = get_host_mac()

    if client_ip in ["127.0.0.1", "localhost", "::1"] or client_ip == host_ip:
        target_ip = host_ip
        target_mac = host_mac
    else:
        target_ip = client_ip
        target_mac = None
        for d in scan_and_sync_network():
            if d["ip"] == target_ip:
                target_mac = d["mac"]
                break
        if not target_mac:
            target_mac = host_mac

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE mac = ? OR ip = ?", (target_mac, target_ip))
    row = c.fetchone()

    if not row:
        now_iso = datetime.now(timezone.utc).isoformat()
        default_hours = float(get_setting("default_allowance_hours", 168.0))
        next_reset = calculate_next_monthly_reset()
        c.execute("""
        INSERT INTO devices (
            mac, ip, hostname, custom_name, vendor, device_type,
            is_gateway, is_host, is_protected, status,
            base_allowance_hours, remaining_seconds, reset_interval,
            next_reset_at, last_seen_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            target_mac, target_ip, "This Device", "This Device", "Local Host", "desktop",
            0, 1, 0, "ACTIVE",
            default_hours, default_hours * 3600.0, "monthly",
            next_reset, now_iso, now_iso, now_iso
        ))
        conn.commit()
        c.execute("SELECT * FROM devices WHERE mac = ?", (target_mac,))
        row = c.fetchone()

    d = dict(row)
    # Enable gambling for this device
    d["is_protected"] = False
    d["is_host"] = True
    d["remaining_hours"] = round(d["remaining_seconds"] / 3600.0, 2)
    d["remaining_formatted"] = format_hours_minutes(d["remaining_seconds"])
    conn.close()
    return d

@app.get("/api/devices")
def list_devices():
    """Lists all tracked devices with balances and status."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM devices
    ORDER BY is_gateway DESC, is_host DESC, status DESC, ip ASC
    """)
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["is_gateway"] = bool(d["is_gateway"])
        d["is_host"] = bool(d["is_host"])
        d["is_protected"] = bool(d["is_protected"])
        d["decay_enabled"] = bool(d["decay_enabled"])
        d["remaining_hours"] = round(d["remaining_seconds"] / 3600.0, 2)
        d["remaining_formatted"] = format_hours_minutes(d["remaining_seconds"])
        result.append(d)
    return result

@app.post("/api/scan")
def trigger_scan():
    """Triggers an active network scan and device synchronization."""
    devices = scan_and_sync_network()
    return {"status": "success", "count": len(devices), "devices": devices}

@app.get("/api/devices/{mac}")
def get_device(mac: str):
    clean_mac = mac.lower().replace("-", ":")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE mac = ?", (clean_mac,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    d = dict(row)
    d["is_gateway"] = bool(d["is_gateway"])
    d["is_host"] = bool(d["is_host"])
    d["is_protected"] = bool(d["is_protected"])
    d["decay_enabled"] = bool(d["decay_enabled"])
    d["remaining_hours"] = round(d["remaining_seconds"] / 3600.0, 2)
    d["remaining_formatted"] = format_hours_minutes(d["remaining_seconds"])

    # Recent bets for this device
    c.execute("SELECT * FROM bets WHERE device_mac = ? ORDER BY id DESC LIMIT 20", (clean_mac,))
    d["recent_bets"] = [dict(b) for b in c.fetchall()]
    conn.close()
    return d

@app.put("/api/devices/{mac}")
def update_device(mac: str, update: DeviceUpdateRequest):
    clean_mac = mac.lower().replace("-", ":")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE mac = ?", (clean_mac,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    fields = []
    params = []

    if update.custom_name is not None:
        fields.append("custom_name = ?")
        params.append(update.custom_name)
    if update.is_protected is not None:
        fields.append("is_protected = ?")
        params.append(1 if update.is_protected else 0)
        if update.is_protected:
            fields.append("status = 'PROTECTED'")
    if update.base_allowance_hours is not None:
        fields.append("base_allowance_hours = ?")
        params.append(update.base_allowance_hours)
    if update.remaining_seconds is not None:
        fields.append("remaining_seconds = ?")
        params.append(max(0.0, update.remaining_seconds))
    if update.decay_enabled is not None:
        fields.append("decay_enabled = ?")
        params.append(1 if update.decay_enabled else 0)
    if update.device_type is not None:
        fields.append("device_type = ?")
        params.append(update.device_type)

    if fields:
        fields.append("updated_at = ?")
        params.append(now_iso)
        params.append(clean_mac)
        c.execute(f"UPDATE devices SET {', '.join(fields)} WHERE mac = ?", params)
        conn.commit()

    conn.close()
    return {"status": "success", "message": "Device updated"}

@app.post("/api/devices/{mac}/emergency-unblock")
def emergency_unblock(mac: str, req: AdminActionRequest):
    """Admin override to unblock device and restore Wi-Fi immediately."""
    clean_mac = mac.lower().replace("-", ":")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE mac = ?", (clean_mac,))
    device = c.fetchone()
    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    add_seconds = max(3600.0, (req.hours_to_add or 0.0) * 3600.0)  # at least 1 hour
    new_balance = float(device["remaining_seconds"]) + add_seconds

    c.execute("""
    UPDATE devices
    SET status = 'ACTIVE',
        remaining_seconds = ?,
        locked_out_at = NULL,
        updated_at = ?
    WHERE mac = ?
    """, (new_balance, now_iso, clean_mac))

    # Trigger unblock via active enforcement driver
    enforce_unblock(clean_mac, device["ip"], device["hostname"], conn=conn)
    name = device["custom_name"] or device["hostname"] or device["ip"]
    log_event(
        "ADMIN_RESTORE",
        f"Admin Pardon granted for {name} ({clean_mac}). Added {add_seconds/3600:.1f}h. Wi-Fi restored.",
        device_mac=clean_mac,
        details={"reason": req.reason, "added_seconds": add_seconds},
        conn=conn
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Device unblocked. Restored with {new_balance/3600:.1f} hours."}

@app.post("/api/devices/{mac}/force-block")
def force_block(mac: str, req: AdminActionRequest):
    """Admin manual action to cut off a device for testing or discipline."""
    clean_mac = mac.lower().replace("-", ":")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE mac = ?", (clean_mac,))
    device = c.fetchone()
    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    if device["is_protected"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot block a protected device or gateway!")

    now_iso = datetime.now(timezone.utc).isoformat()
    c.execute("""
    UPDATE devices
    SET status = 'LOCKED_OUT',
        remaining_seconds = 0.0,
        locked_out_at = ?,
        updated_at = ?
    WHERE mac = ?
    """, (now_iso, now_iso, clean_mac))

    enforce_block(clean_mac, device["ip"], device["hostname"], conn=conn)
    name = device["custom_name"] or device["hostname"] or device["ip"]
    log_event(
        "ADMIN_ACTION",
        f"Admin forced Wi-Fi cutoff on {name} ({clean_mac}). Balance zeroed.",
        device_mac=clean_mac,
        details={"reason": req.reason},
        conn=conn
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Device {name} Wi-Fi severed."}

# ----------------- The Roulette Spin Engine -----------------

@app.post("/api/spin", response_model=SpinResponse)
def execute_spin(req: SpinRequest, request: Request):
    """
    Executes a roulette spin with the device's wagered hours.
    Applies real casino payouts.
    If balance hits 0h: immediately initiates Wi-Fi cutoff until monthly reset!
    """
    clean_mac = (req.device_mac or "").lower().replace("-", ":")
    host_ip = get_host_ip()
    host_mac = get_host_mac()
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not clean_mac or clean_mac in ["me", "current", "this_device"]:
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            clean_mac = host_mac
        else:
            for d in scan_and_sync_network():
                if d["ip"] == client_ip:
                    clean_mac = d["mac"]
                    break
            if not clean_mac:
                clean_mac = host_mac

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE mac = ? OR ip = ? OR ip = ?", (clean_mac, host_ip, client_ip))
    device = c.fetchone()

    if not device:
        # Fallback to any host device
        c.execute("SELECT * FROM devices WHERE is_host = 1")
        device = c.fetchone()

    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found.")

    if device["status"] == "LOCKED_OUT":
        conn.close()
        raise HTTPException(
            status_code=403,
            detail=f"This device has BUSTED and is locked out of Wi-Fi until the monthly reset ({device['next_reset_at']})!"
        )

    if device["is_gateway"]:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="The router gateway is PROTECTED and cannot be gambled away!"
        )

    if not req.bets:
        conn.close()
        raise HTTPException(status_code=400, detail="No bets provided.")

    # Calculate total wager in seconds and hours
    total_wager_hours = sum(b.wager_hours for b in req.bets)
    total_wager_seconds = total_wager_hours * 3600.0
    current_balance_seconds = float(device["remaining_seconds"])
    current_balance_hours = current_balance_seconds / 3600.0

    if total_wager_hours <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Wager must be greater than zero.")

    # Allow tiny floating precision tolerance
    if total_wager_seconds > (current_balance_seconds + 0.1):
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient time balance! You wagered {total_wager_hours:.2f}h but only have {current_balance_hours:.2f}h remaining."
        )

    # 1. Spin the European Roulette wheel
    winning_number = spin_wheel()
    winning_color = get_number_color(winning_number)
    is_even = (winning_number != 0 and winning_number % 2 == 0)
    is_odd = (winning_number != 0 and winning_number % 2 == 1)
    is_low = (1 <= winning_number <= 18)
    is_high = (19 <= winning_number <= 36)

    dozen = 0
    if 1 <= winning_number <= 12:
        dozen = 1
    elif 13 <= winning_number <= 24:
        dozen = 2
    elif 25 <= winning_number <= 36:
        dozen = 3

    column = 0
    if winning_number in {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34}:
        column = 1
    elif winning_number in {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}:
        column = 2
    elif winning_number in {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}:
        column = 3

    # 2. Evaluate all placed bets
    bets_outcomes = []
    total_won_hours = 0.0
    net_profit_hours = 0.0

    for bet in req.bets:
        outcome = evaluate_bet(bet, winning_number)
        bets_outcomes.append(outcome)
        if outcome.is_win:
            total_won_hours += outcome.total_returned_hours
            net_profit_hours += outcome.profit_hours
        else:
            net_profit_hours -= bet.wager_hours

    # 3. Compute new balance
    # If net_profit_hours >= 0, balance increases by net_profit_hours
    # If net_profit_hours < 0, balance decreases by abs(net_profit_hours)
    new_balance_seconds = max(0.0, current_balance_seconds + (net_profit_hours * 3600.0))
    new_balance_hours = round(new_balance_seconds / 3600.0, 2)
    is_busted = (new_balance_seconds <= 1.0)

    now_iso = datetime.now(timezone.utc).isoformat()
    dev_name = device["custom_name"] or device["hostname"] or device["ip"]
    new_status = "LOCKED_OUT" if is_busted else "ACTIVE"
    locked_out_at = now_iso if is_busted else None

    # Update device in SQLite
    c.execute("""
    UPDATE devices
    SET remaining_seconds = ?,
        status = ?,
        locked_out_at = ?,
        updated_at = ?
    WHERE mac = ?
    """, (new_balance_seconds, new_status, locked_out_at, now_iso, clean_mac))

    # Insert Bet Records
    for outcome in bets_outcomes:
        c.execute("""
        INSERT INTO bets (
            device_mac, device_name, bet_type, bet_selection,
            wager_seconds, wager_hours, winning_number, is_win,
            payout_multiplier, payout_seconds, payout_hours,
            balance_before_seconds, balance_after_seconds,
            result_busted, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clean_mac, dev_name, outcome.bet_type, outcome.bet_selection,
            outcome.wager_hours * 3600.0, outcome.wager_hours, winning_number,
            1 if outcome.is_win else 0, outcome.payout_multiplier,
            outcome.total_returned_hours * 3600.0, outcome.total_returned_hours,
            current_balance_seconds, new_balance_seconds,
            1 if is_busted else 0, now_iso
        ))

    # Log Spin Outcome
    if net_profit_hours > 0:
        msg = f"🎰 WINNER! {dev_name} won +{net_profit_hours:.1f}h on {winning_number} ({winning_color.upper()})! New balance: {new_balance_hours:.1f}h"
        log_event("BET_WIN", msg, device_mac=clean_mac, details={"profit_hours": net_profit_hours, "num": winning_number}, conn=conn)
    else:
        msg = f"💀 LOSS! {dev_name} lost {abs(net_profit_hours):.1f}h on {winning_number} ({winning_color.upper()}). Remaining: {new_balance_hours:.1f}h"
        log_event("BET_LOSS", msg, device_mac=clean_mac, details={"loss_hours": abs(net_profit_hours), "num": winning_number}, conn=conn)

    # 4. HARD CUTOFF ENFORCEMENT ON BUST!
    if is_busted:
        bust_msg = f"🚨 BUSTED! {dev_name} gambled away their final hours! Wi-Fi SEVERED until monthly reset ({device['next_reset_at']})."
        log_event("BUST_LOCKOUT", bust_msg, device_mac=clean_mac, details={"reset_date": device["next_reset_at"]}, conn=conn)
        # Execute actual network disconnect
        enforce_block(clean_mac, device["ip"], device["hostname"], conn=conn)
        message = f"BUSTED! Ball landed on {winning_number} ({winning_color.upper()}). Device lost all remaining hours and has been DISCONNECTED from Wi-Fi until reset!"
    else:
        if net_profit_hours > 0:
            message = f"JACKPOT! Ball landed on {winning_number} ({winning_color.upper()})! You won +{net_profit_hours:.1f} hours! New balance: {format_hours_minutes(new_balance_seconds)}"
        else:
            message = f"Landed on {winning_number} ({winning_color.upper()}). Lost {abs(net_profit_hours):.1f} hours. Balance: {format_hours_minutes(new_balance_seconds)}"

    conn.commit()
    conn.close()

    return SpinResponse(
        winning_number=winning_number,
        winning_color=winning_color,
        is_even=is_even,
        is_odd=is_odd,
        is_low=is_low,
        is_high=is_high,
        dozen=dozen,
        column=column,
        total_wager_hours=round(total_wager_hours, 2),
        total_won_hours=round(total_won_hours, 2),
        net_profit_hours=round(net_profit_hours, 2),
        balance_before_hours=round(current_balance_hours, 2),
        balance_after_hours=round(new_balance_hours, 2),
        balance_after_formatted=format_hours_minutes(new_balance_seconds),
        is_busted=is_busted,
        status=new_status,
        bets_breakdown=bets_outcomes,
        message=message
    )

# ----------------- History, Stats, and Logs -----------------

@app.get("/api/bets/history")
def get_bets_history(limit: int = 50):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bets ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()

    # Get recent numbers
    c.execute("SELECT winning_number FROM bets ORDER BY id DESC LIMIT 15")
    recent_numbers = [r["winning_number"] for r in c.fetchall()]

    # Hot & cold numbers
    c.execute("""
    SELECT winning_number, COUNT(*) as cnt
    FROM bets
    GROUP BY winning_number
    ORDER BY cnt DESC
    LIMIT 5
    """)
    hot = [dict(r) for r in c.fetchall()]

    c.execute("""
    SELECT winning_number, COUNT(*) as cnt
    FROM bets
    GROUP BY winning_number
    ORDER BY cnt ASC
    LIMIT 5
    """)
    cold = [dict(r) for r in c.fetchall()]

    conn.close()
    return {
        "bets": [dict(r) for r in rows],
        "recent_numbers": recent_numbers,
        "hot_numbers": hot,
        "cold_numbers": cold
    }

@app.get("/api/stats")
def get_casino_stats():
    conn = get_connection()
    c = conn.cursor()

    # Total bets count
    c.execute("SELECT COUNT(*), SUM(wager_hours) FROM bets")
    row_bets = c.fetchone()
    total_spins = row_bets[0] or 0
    total_wagered = round(row_bets[1] or 0.0, 1)

    # Total house profit (hours lost - hours won)
    c.execute("SELECT SUM(wager_hours) FROM bets WHERE is_win = 0")
    hours_lost = round((c.fetchone()[0] or 0.0), 1)

    c.execute("SELECT SUM(payout_hours - wager_hours) FROM bets WHERE is_win = 1")
    hours_won = round((c.fetchone()[0] or 0.0), 1)

    # Locked out devices count
    c.execute("SELECT COUNT(*) FROM devices WHERE status = 'LOCKED_OUT'")
    locked_count = c.fetchone()[0] or 0

    # Total active devices count
    c.execute("SELECT COUNT(*) FROM devices")
    total_devices = c.fetchone()[0] or 0

    conn.close()
    return {
        "total_spins": total_spins,
        "total_wagered_hours": total_wagered,
        "hours_claimed_by_house": hours_lost,
        "hours_paid_to_players": hours_won,
        "busted_devices_count": locked_count,
        "total_devices_count": total_devices
    }

@app.get("/api/audit")
def get_audit_logs(limit: int = 60):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- Settings & Enforcement -----------------

@app.get("/api/settings")
def get_settings():
    return get_all_settings()

@app.put("/api/settings")
def update_settings(update: SettingsUpdateRequest):
    d = update.model_dump(exclude_unset=True)
    for k, v in d.items():
        set_setting(k, v)
    return {"status": "success", "settings": get_all_settings()}

@app.post("/api/settings/test-driver")
def test_driver_endpoint():
    success, message = test_driver()
    return {"success": success, "message": message}

# ----------------- Static Frontend -----------------

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
