"""
Windows Firewall driver for local testing and subnet blocking.
Adds/removes inbound and outbound Windows Firewall blocking rules for target IP.
"""

import subprocess
from typing import Tuple
from app.enforcement.driver_base import BaseEnforcementDriver

class FirewallDriver(BaseEnforcementDriver):
    def block_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        if not ip:
            return False, "Target IP required for firewall enforcement."
        
        rule_name = f"WiFiRoulette_Block_{ip.replace('.', '_')}"
        # Block outbound & inbound to that IP
        cmd_out = f'netsh advfirewall firewall add rule name="{rule_name}_OUT" dir=out action=block remoteip={ip}'
        cmd_in = f'netsh advfirewall firewall add rule name="{rule_name}_IN" dir=in action=block remoteip={ip}'

        try:
            r1 = subprocess.run(cmd_out, shell=True, capture_output=True, text=True)
            r2 = subprocess.run(cmd_in, shell=True, capture_output=True, text=True)
            if r1.returncode == 0 and r2.returncode == 0:
                return True, f"Firewall rule added: blocked traffic with {ip}"
            return False, f"Firewall setup error: {r1.stderr or r2.stderr}"
        except Exception as e:
            return False, f"Firewall command error: {str(e)}"

    def unblock_device(self, mac: str, ip: str = "", hostname: str = "") -> Tuple[bool, str]:
        if not ip:
            return False, "Target IP required for firewall unblock."

        rule_name = f"WiFiRoulette_Block_{ip.replace('.', '_')}"
        cmd_out = f'netsh advfirewall firewall delete rule name="{rule_name}_OUT"'
        cmd_in = f'netsh advfirewall firewall delete rule name="{rule_name}_IN"'

        try:
            subprocess.run(cmd_out, shell=True, capture_output=True)
            subprocess.run(cmd_in, shell=True, capture_output=True)
            return True, f"Firewall rule removed: unblocked traffic with {ip}"
        except Exception as e:
            return False, f"Firewall unblock error: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        try:
            r = subprocess.run("netsh advfirewall show currentprofile", shell=True, capture_output=True, text=True)
            if r.returncode == 0:
                return True, "Windows Firewall is active and controllable."
            return False, f"Firewall query returned exit code {r.returncode}"
        except Exception as e:
            return False, f"Firewall test error: {str(e)}"
