"""
Custom command and HTTP Webhook enforcement driver.
Allows executing user-provided commands (e.g. SSH to router, PowerShell, curl) or HTTP webhooks.
"""

import subprocess
import requests
from typing import Tuple
from app.enforcement.driver_base import BaseEnforcementDriver

class WebhookDriver(BaseEnforcementDriver):
    def __init__(self, block_cmd: str = "", unblock_cmd: str = ""):
        self.block_cmd = block_cmd
        self.unblock_cmd = unblock_cmd

    def _execute(self, template: str, mac: str, ip: str, hostname: str) -> Tuple[bool, str]:
        if not template.strip():
            return False, "No command or webhook URL configured in Settings."

        # Interpolate variables
        formatted = template.replace("{mac}", mac).replace("{ip}", ip).replace("{hostname}", hostname)

        # Check if HTTP webhook URL
        if formatted.startswith("http://") or formatted.startswith("https://"):
            try:
                resp = requests.post(formatted, json={"mac": mac, "ip": ip, "hostname": hostname}, timeout=5)
                return resp.status_code in [200, 201, 204], f"Webhook returned HTTP {resp.status_code}"
            except Exception as e:
                return False, f"Webhook request failed: {str(e)}"

        # Otherwise execute as shell command
        try:
            res = subprocess.run(formatted, shell=True, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return True, f"Command executed successfully: {res.stdout.strip() or 'OK'}"
            return False, f"Command failed (exit {res.returncode}): {res.stderr.strip()}"
        except Exception as e:
            return False, f"Command execution error: {str(e)}"

    def block_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        return self._execute(self.block_cmd, mac, ip, hostname)

    def unblock_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        return self._execute(self.unblock_cmd, mac, ip, hostname)

    def test_connection(self) -> Tuple[bool, str]:
        if not self.block_cmd and not self.unblock_cmd:
            return False, "Custom command / webhook is empty. Configure it in Settings."
        return True, "Custom webhook driver ready."
