"""
cisco.py
Parser for Cisco IOS-style configuration (as pulled via Netmiko `show running-config`
in a real deployment). Line-by-line regex matching into the CDM.
"""
import re
from parsers.base import BaseParser
from models import CDM


class CiscoParser(BaseParser):
    vendor_name = "cisco"

    def matches(self, config_text: str) -> bool:
        return bool(
            re.search(r"^hostname\s+\S+", config_text, re.MULTILINE)
            or re.search(r"^line vty", config_text, re.MULTILINE)
            or re.search(r"^!", config_text, re.MULTILINE)
        )

    def parse(self, config_text: str):
        cdm = CDM(vendor=self.vendor_name, os="IOS")
        cdm.hostname = self._extract_hostname(config_text, [r"^hostname\s+(\S+)"])

        unrecognized = []
        for raw in config_text.splitlines():
            line = raw.strip()
            if not line or line in ("!",):
                continue
            matched = True
            if re.search(r"ip ssh version 2", line, re.I):
                cdm.ssh_version = 2
            elif re.search(r"ip ssh version 1", line, re.I):
                cdm.ssh_version = 1
            elif re.search(r"transport input telnet", line, re.I):
                cdm.telnet_enabled = True
            elif re.search(r"transport input ssh", line, re.I):
                cdm.telnet_enabled = False
            elif re.search(r"service password-encryption", line, re.I):
                cdm.password_encryption = True
            elif re.search(r"ip http server", line, re.I):
                cdm.http_enabled = True
            elif re.search(r"no ip http server", line, re.I):
                cdm.http_enabled = False
            elif re.search(r"^ntp server", line, re.I):
                cdm.ntp_configured = True
            elif re.search(r"^logging (host|trap)", line, re.I):
                cdm.logging_enabled = True
            elif re.search(r"aaa new-model", line, re.I):
                cdm.aaa_configured = True
            elif re.search(r"snmp-server", line, re.I):
                cdm.snmp_detected = True
                if re.search(r"\bv3\b", line, re.I):
                    cdm.snmp_v3 = True
            elif re.search(r"exec-timeout", line, re.I):
                cdm.session_timeout_set = True
            elif re.search(r"^line vty|^hostname", line, re.I):
                pass  # structural, not a compliance field
            else:
                matched = False
            if not matched:
                unrecognized.append(line)
        return cdm, unrecognized
