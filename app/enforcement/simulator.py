"""
Simulation enforcement driver. Safe for dry-runs and gameplay demonstrations.
"""

from typing import Tuple
from app.enforcement.driver_base import BaseEnforcementDriver

class SimulationDriver(BaseEnforcementDriver):
    def block_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        msg = f"[SIMULATION] Wi-Fi access severed for {hostname or ip} ({mac}). Packets dropped."
        return True, msg

    def unblock_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        msg = f"[SIMULATION] Wi-Fi access restored for {hostname or ip} ({mac}). Reconnected."
        return True, msg

    def test_connection(self) -> Tuple[bool, str]:
        return True, "Simulation driver is active and ready. All disconnects are logged safely."
