"""
Base class for network enforcement drivers.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class BaseEnforcementDriver(ABC):
    @abstractmethod
    def block_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        """
        Disconnects / blocks the device from Wi-Fi / network.
        Returns (success: bool, message: str)
        """
        pass

    @abstractmethod
    def unblock_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        """
        Restores Wi-Fi / network connectivity to the device.
        Returns (success: bool, message: str)
        """
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Validates connectivity to the enforcement endpoint.
        Returns (success: bool, message: str)
        """
        pass
