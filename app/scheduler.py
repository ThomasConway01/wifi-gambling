"""
Background scheduler for monthly balance resets, Wi-Fi unblocks, and time decay.
"""

import threading
import time
from datetime import datetime, timezone
from app.database import (
    get_connection,
    get_setting,
    calculate_next_monthly_reset,
    log_event
)
from app.enforcement.manager import enforce_unblock, enforce_block

_scheduler_running = False
_scheduler_thread = None

def scheduler_tick():
    """Single tick of the background scheduler."""
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    conn = get_connection()
    c = conn.cursor()

    # 1. Check for devices due for monthly/interval reset
    c.execute("""
    SELECT mac, ip, hostname, custom_name, base_allowance_hours, status, next_reset_at
    FROM devices
    WHERE next_reset_at IS NOT NULL AND next_reset_at <= ?
    """, (now_iso,))
    due_devices = c.fetchall()

    for d in due_devices:
        mac = d["mac"]
        ip = d["ip"]
        name = d["custom_name"] or d["hostname"] or ip
        base_hours = float(d["base_allowance_hours"])
        base_seconds = base_hours * 3600.0
        next_reset = calculate_next_monthly_reset()
        old_status = d["status"]

        new_status = "ACTIVE"
        if old_status == "PROTECTED":
            new_status = "PROTECTED"

        c.execute("""
        UPDATE devices
        SET remaining_seconds = ?,
            next_reset_at = ?,
            status = ?,
            locked_out_at = NULL,
            updated_at = ?
        WHERE mac = ?
        """, (base_seconds, next_reset, new_status, now_iso, mac))

        # If it was locked out, unblock network!
        if old_status == "LOCKED_OUT":
            enforce_unblock(mac, ip, d["hostname"], conn=conn)
            log_event(
                "RESET_TOPUP",
                f"Monthly reset reached for {name}! Restored {base_hours}h. Wi-Fi re-enabled.",
                device_mac=mac,
                details={"restored_hours": base_hours, "new_next_reset": next_reset},
                conn=conn
            )
        else:
            log_event(
                "RESET_TOPUP",
                f"Monthly balance reset for {name}: refreshed to {base_hours}h.",
                device_mac=mac,
                details={"restored_hours": base_hours},
                conn=conn
            )

    conn.commit()

    # 2. Check for active decay if enabled
    decay_global = bool(get_setting("active_decay_enabled", False))
    decay_multiplier = float(get_setting("decay_rate_multiplier", 1.0))

    if decay_global:
        elapsed_seconds = 10.0 * decay_multiplier  # scheduler runs every ~10s
        c.execute("""
        SELECT mac, ip, hostname, custom_name, remaining_seconds, status
        FROM devices
        WHERE status = 'ACTIVE' AND is_protected = 0
        """)
        active_devs = c.fetchall()

        for d in active_devs:
            mac = d["mac"]
            ip = d["ip"]
            name = d["custom_name"] or d["hostname"] or ip
            rem = max(0.0, float(d["remaining_seconds"]) - elapsed_seconds)

            if rem <= 0.0:
                # BUSTED via decay
                c.execute("""
                UPDATE devices
                SET remaining_seconds = 0.0,
                    status = 'LOCKED_OUT',
                    locked_out_at = ?,
                    updated_at = ?
                WHERE mac = ?
                """, (now_iso, now_iso, mac))

                enforce_block(mac, ip, d["hostname"], conn=conn)
                log_event(
                    "BUST_LOCKOUT",
                    f"Device {name} ran out of time from active usage! Wi-Fi severed until monthly reset.",
                    device_mac=mac,
                    details={"reason": "passive_drain"},
                    conn=conn
                )
            else:
                c.execute("""
                UPDATE devices
                SET remaining_seconds = ?,
                    updated_at = ?
                WHERE mac = ?
                """, (rem, now_iso, mac))

        conn.commit()

    conn.close()

def _worker_loop():
    global _scheduler_running
    while _scheduler_running:
        try:
            scheduler_tick()
        except Exception as e:
            print(f"[Scheduler Error] {e}")
        time.sleep(10)

def start_scheduler():
    global _scheduler_running, _scheduler_thread
    if not _scheduler_running:
        _scheduler_running = True
        _scheduler_thread = threading.Thread(target=_worker_loop, daemon=True)
        _scheduler_thread.start()
        print("[Scheduler] Background reset & decay worker started.")

def stop_scheduler():
    global _scheduler_running
    _scheduler_running = False
