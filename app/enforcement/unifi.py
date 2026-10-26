"""
UniFi Network Gateway enforcement driver.
Communicates with UniFi Controller / Gateway API to block/unblock client STAs on Wi-Fi.
"""

import requests
import urllib3
from typing import Tuple, Optional
from app.enforcement.driver_base import BaseEnforcementDriver

# Suppress insecure HTTPS warnings when using self-signed cert on router
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UniFiDriver(BaseEnforcementDriver):
    def __init__(
        self,
        host: str = "https://192.168.1.1",
        username: str = "",
        password: str = "",
        site: str = "default",
        verify_ssl: bool = False
    ):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.site = site or "default"
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.csrf_token: Optional[str] = None
        self.is_unifi_os = True

    def _login(self) -> Tuple[bool, str]:
        if not self.username or not self.password:
            return False, "UniFi credentials missing. Enter username and password in Settings."

        # Attempt UniFi OS login first
        try:
            login_url = f"{self.host}/api/auth/login"
            resp = self.session.post(
                login_url,
                json={"username": self.username, "password": self.password},
                timeout=5
            )
            if resp.status_code == 200:
                self.is_unifi_os = True
                self.csrf_token = resp.headers.get("x-csrf-token")
                return True, "Authenticated with UniFi OS Gateway"
        except Exception as e:
            pass

        # Attempt Classic Controller login (fallback)
        try:
            classic_url = f"{self.host}/api/login"
            resp = self.session.post(
                classic_url,
                json={"username": self.username, "password": self.password},
                timeout=5
            )
            if resp.status_code == 200:
                self.is_unifi_os = False
                return True, "Authenticated with Classic UniFi Controller"
            return False, f"UniFi login rejected (HTTP {resp.status_code}). Check username/password."
        except Exception as e:
            return False, f"Could not reach UniFi host at {self.host}: {str(e)}"

    def _execute_sta_cmd(self, cmd: str, mac: str) -> Tuple[bool, str]:
        clean_mac = mac.lower().replace("-", ":")
        login_ok, login_msg = self._login()
        if not login_ok:
            return False, login_msg

        headers = {}
        if self.csrf_token:
            headers["x-csrf-token"] = self.csrf_token

        if self.is_unifi_os:
            url = f"{self.host}/proxy/network/api/s/{self.site}/cmd/stamgr"
        else:
            url = f"{self.host}/api/s/{self.site}/cmd/stamgr"

        payload = {"cmd": cmd, "mac": clean_mac}

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=6)
            if resp.status_code == 200:
                action_name = "Blocked from Wi-Fi" if "block" in cmd else "Unblocked and restored"
                return True, f"UniFi {action_name}: {clean_mac}"
            return False, f"UniFi API error HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, f"UniFi command error: {str(e)}"

    def block_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        return self._execute_sta_cmd("block-sta", mac)

    def unblock_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        return self._execute_sta_cmd("unblock-sta", mac)

    def test_connection(self) -> Tuple[bool, str]:
        login_ok, msg = self._login()
        return login_ok, msg
