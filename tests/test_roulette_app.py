"""
Comprehensive Test Suite for WiFi Time Roulette / Bandwidth Casino.
Tests API, Device Management, Roulette Spin Math, All-In BUST Wi-Fi Cutoff, and Admin Pardon.
"""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection, init_db

class TestRouletteApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

        # Ensure database is initialized
        init_db()

        # Seed mock test devices if none exist (e.g. in CI or isolated sandbox)
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT count(*) FROM devices")
        count = c.fetchone()[0]

        now_iso = datetime.now(timezone.utc).isoformat()
        if count == 0:
            # Seed Gateway (Protected)
            c.execute("""
            INSERT INTO devices (
                mac, ip, hostname, custom_name, vendor, device_type,
                is_gateway, is_host, is_protected, status,
                base_allowance_hours, remaining_seconds, reset_interval,
                last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "00:11:22:33:44:55", "192.168.1.1", "gateway.local", "Main Router",
                "Ubiquiti", "router", 1, 0, 1, "PROTECTED",
                168.0, 604800.0, "monthly", now_iso, now_iso, now_iso
            ))

            # Seed Active Device
            c.execute("""
            INSERT INTO devices (
                mac, ip, hostname, custom_name, vendor, device_type,
                is_gateway, is_host, is_protected, status,
                base_allowance_hours, remaining_seconds, reset_interval,
                last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "aa:bb:cc:dd:ee:01", "192.168.1.100", "test-phone", "Kid's iPhone",
                "Apple", "smartphone", 0, 0, 0, "ACTIVE",
                168.0, 604800.0, "monthly", now_iso, now_iso, now_iso
            ))
            conn.commit()

        conn.close()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_01_static_assets(self):
        """Verify frontend assets load correctly."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("WiFi Time Roulette", resp.text)

        for asset in [
            "/static/css/custom.css",
            "/static/js/audio.js",
            "/static/js/roulette_wheel.js",
            "/static/js/roulette_table.js",
            "/static/js/app.js"
        ]:
            r = self.client.get(asset)
            self.assertEqual(r.status_code, 200, f"Asset failed: {asset}")
            self.assertGreater(len(r.content), 500)
        print("✓ Static frontend assets loaded successfully.")

    def test_02_device_discovery_and_protection(self):
        """Verify network devices are populated and gateway/host are protected."""
        resp = self.client.get("/api/devices")
        self.assertEqual(resp.status_code, 200)
        devices = resp.json()
        self.assertGreater(len(devices), 0)

        # Check that at least one device is protected (Gateway or Host)
        protected_devs = [d for d in devices if d["is_protected"]]
        self.assertGreater(len(protected_devs), 0)
        print(f"✓ Discovered {len(devices)} devices ({len(protected_devs)} protected).")

    def test_03_spin_protection_check(self):
        """Verify protected devices cannot be gambled."""
        resp = self.client.get("/api/devices")
        devices = resp.json()
        protected = next(d for d in devices if d["is_protected"])

        spin_resp = self.client.post("/api/spin", json={
            "device_mac": protected["mac"],
            "bets": [{"bet_type": "color", "bet_selection": "red", "wager_seconds": 3600, "wager_hours": 1.0}]
        })
        self.assertEqual(spin_resp.status_code, 400)
        self.assertIn("PROTECTED", spin_resp.json()["detail"])
        print("✓ Protected device immunity verified.")

    def test_04_roulette_bet_and_payout(self):
        """Place a bet on an active device and verify balance changes."""
        resp = self.client.get("/api/devices")
        devices = resp.json()
        gambler = next(d for d in devices if not d["is_protected"] and d["status"] == "ACTIVE")
        mac = gambler["mac"]
        initial_balance = gambler["remaining_hours"]

        # Place 2 hours on Red
        wager = 2.0
        spin_resp = self.client.post("/api/spin", json={
            "device_mac": mac,
            "bets": [{"bet_type": "color", "bet_selection": "red", "wager_seconds": wager * 3600, "wager_hours": wager}]
        })
        self.assertEqual(spin_resp.status_code, 200)
        data = spin_resp.json()
        self.assertIn(data["winning_color"], ["red", "black", "green"])
        self.assertGreaterEqual(data["winning_number"], 0)
        self.assertLessEqual(data["winning_number"], 36)

        # Verify mathematical consistency
        if data["winning_color"] == "red":
            self.assertEqual(data["net_profit_hours"], wager)
            self.assertEqual(data["balance_after_hours"], round(initial_balance + wager, 2))
            print(f"✓ Spin WON! Landed on {data['winning_number']} Red. Balance increased by {wager}h.")
        else:
            self.assertEqual(data["net_profit_hours"], -wager)
            self.assertEqual(data["balance_after_hours"], round(initial_balance - wager, 2))
            print(f"✓ Spin LOST! Landed on {data['winning_number']} {data['winning_color']}. Balance decreased by {wager}h.")

    def test_05_bust_and_wifi_cutoff_enforcement(self):
        """Test BUST logic: wagering remaining time, zeroing out, triggering Wi-Fi cutoff and lock out."""
        # Find an active, non-protected device or reset target device to ACTIVE
        resp = self.client.get("/api/devices")
        devices = resp.json()
        target = next((d for d in devices if not d["is_protected"] and d["status"] == "ACTIVE"), None)
        if not target:
            target = next(d for d in devices if not d["is_protected"])
            # Emergency unblock first to make sure it's active
            self.client.post(f"/api/devices/{target['mac']}/emergency-unblock", json={"hours_to_add": 5.0, "reason": "Test setup"})

        test_mac = target["mac"]

        # Set balance to exactly 5.0 hours for clean testing
        self.client.put(f"/api/devices/{test_mac}", json={"remaining_seconds": 5.0 * 3600.0, "is_protected": False})

        # Wager ALL-IN 5.0 hours on straight number 13 until bust
        busted = False
        for _ in range(10):
            d_info = self.client.get(f"/api/devices/{test_mac}").json()
            rem = d_info["remaining_hours"]
            if rem <= 0:
                busted = True
                break

            s_resp = self.client.post("/api/spin", json={
                "device_mac": test_mac,
                "bets": [{"bet_type": "straight", "bet_selection": "13", "wager_seconds": rem * 3600, "wager_hours": rem}]
            })
            s_data = s_resp.json()
            if s_data["is_busted"]:
                busted = True
                self.assertEqual(s_data["status"], "LOCKED_OUT")
                self.assertIn("DISCONNECTED", s_data["message"])
                break

        self.assertTrue(busted, "Device should have busted")

        # Verify device in DB is LOCKED_OUT
        d_updated = self.client.get(f"/api/devices/{test_mac}").json()
        self.assertEqual(d_updated["status"], "LOCKED_OUT")
        self.assertEqual(d_updated["remaining_hours"], 0.0)

        # Verify attempting to spin again fails with 403 Forbidden
        err_resp = self.client.post("/api/spin", json={
            "device_mac": test_mac,
            "bets": [{"bet_type": "color", "bet_selection": "red", "wager_seconds": 3600, "wager_hours": 1.0}]
        })
        self.assertEqual(err_resp.status_code, 403)
        self.assertIn("BUSTED", err_resp.json()["detail"])
        print(f"✓ Wi-Fi CUTOFF verified! Device {test_mac} successfully locked out on bust.")

        # Test Admin Pardon / Emergency Unblock
        unblock_resp = self.client.post(f"/api/devices/{test_mac}/emergency-unblock", json={
            "hours_to_add": 168.0,
            "reason": "Testing restore"
        })
        self.assertEqual(unblock_resp.status_code, 200)

        d_restored = self.client.get(f"/api/devices/{test_mac}").json()
        self.assertEqual(d_restored["status"], "ACTIVE")
        self.assertGreaterEqual(d_restored["remaining_hours"], 168.0)
        print(f"✓ Admin Pardon verified! Wi-Fi restored with {d_restored['remaining_hours']}h.")

    def test_06_enforcement_driver_testing(self):
        """Test enforcement driver ping/test."""
        res = self.client.post("/api/settings/test-driver", json={})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        print(f"✓ Enforcement driver verified: {data['message']}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
