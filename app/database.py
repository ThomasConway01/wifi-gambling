"""
Database layer for WiFi Time Roulette (SQLite).
"""

import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "roulette.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Devices table
    c.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT NOT NULL,
        hostname TEXT DEFAULT '',
        custom_name TEXT DEFAULT '',
        vendor TEXT DEFAULT '',
        device_type TEXT DEFAULT 'device',
        is_gateway INTEGER DEFAULT 0,
        is_host INTEGER DEFAULT 0,
        is_protected INTEGER DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE',
        base_allowance_hours REAL DEFAULT 168.0,
        remaining_seconds REAL DEFAULT 604800.0,
        reset_interval TEXT DEFAULT 'monthly',
        next_reset_at TEXT,
        last_seen_at TEXT,
        locked_out_at TEXT,
        decay_enabled INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Bets history table
    c.execute("""
    CREATE TABLE IF NOT EXISTS bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_mac TEXT NOT NULL,
        device_name TEXT NOT NULL,
        bet_type TEXT NOT NULL,
        bet_selection TEXT NOT NULL,
        wager_seconds REAL NOT NULL,
        wager_hours REAL NOT NULL,
        winning_number INTEGER NOT NULL,
        is_win INTEGER NOT NULL,
        payout_multiplier REAL NOT NULL,
        payout_seconds REAL NOT NULL,
        payout_hours REAL NOT NULL,
        balance_before_seconds REAL NOT NULL,
        balance_after_seconds REAL NOT NULL,
        result_busted INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # Audit / Event Log
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        device_mac TEXT,
        message TEXT NOT NULL,
        details_json TEXT DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """)

    # App Settings
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Seed default settings if not exists
    default_settings = {
        "enforcement_mode": "simulation",  # 'simulation', 'unifi', 'webhook', 'firewall'
        "default_allowance_hours": 168.0,
        "reset_interval": "monthly",       # 'monthly', 'weekly', 'biweekly'
        "reset_day_of_month": 1,
        "active_decay_enabled": False,     # Drain time passively in real-time or purely casino
        "decay_rate_multiplier": 1.0,      # 1 second of real time = 1 second of balance
        "unifi_host": "https://192.168.1.1",
        "unifi_username": "",
        "unifi_password": "",
        "unifi_site": "default",
        "unifi_verify_ssl": False,
        "webhook_block_cmd": "",
        "webhook_unblock_cmd": "",
        "admin_pin": "1234",
    }

    for key, val in default_settings.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(val)))

    conn.commit()
    conn.close()

def get_setting(key: str, default: Any = None) -> Any:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]
    return default

def set_setting(key: str, value: Any):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO settings (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, json.dumps(value)))
    conn.commit()
    conn.close()

def get_all_settings() -> Dict[str, Any]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    rows = c.fetchall()
    conn.close()
    result = {}
    for r in rows:
        try:
            result[r["key"]] = json.loads(r["value"])
        except Exception:
            result[r["key"]] = r["value"]
    return result

def calculate_next_monthly_reset() -> str:
    """Calculates ISO string for 1st of next month at 00:00:00 UTC."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    else:
        next_month = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return next_month.isoformat()

def log_event(event_type: str, message: str, device_mac: Optional[str] = None, details: Optional[Dict[str, Any]] = None, conn: Optional[sqlite3.Connection] = None):
    now = datetime.now(timezone.utc).isoformat()
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
    c = conn.cursor()
    c.execute("""
    INSERT INTO audit_logs (event_type, device_mac, message, details_json, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (event_type, device_mac, message, json.dumps(details or {}), now))
    if should_close:
        conn.commit()
        conn.close()
