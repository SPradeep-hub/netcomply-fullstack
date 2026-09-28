"""
paloalto.py
Parser for Palo Alto PAN-OS `set` style configuration.
"""
import re
from parsers.base import BaseParser
from models import CDM


class PaloAltoParser(BaseParser):
    vendor_name = "paloalto"

    def matches(self, config_text: str) -> bool:
        return bool(re.search(r"^set (deviceconfig|shared|network|rulebase)", config_text, re.MULTILINE))

    def parse(self, config_text: str):
        cdm = CDM(vendor=self.vendor_name, os="PAN-OS")
        cdm.hostname = self._extract_hostname(config_text, [r"set deviceconfig system hostname\s+(\S+)"])

        unrecognized = []
        for raw in config_text.splitlines():
            line = raw.strip()
            if not line:
                continue
            matched = True
            if re.search(r"ssh protocol-version v2", line, re.I):
                cdm.ssh_version = 2
            elif re.search(r"ssh protocol-version v1", line, re.I):
                cdm.ssh_version = 1
            elif re.search(r"disable-telnet\s+no", line, re.I):
                cdm.telnet_enabled = True
            elif re.search(r"disable-telnet\s+yes", line, re.I):
                cdm.telnet_enabled = False
            elif re.search(r"disable-http\s+no", line, re.I):
                cdm.http_enabled = True
            elif re.search(r"disable-http\s+yes", line, re.I):
                cdm.http_enabled = False
            elif re.search(r"ntp-servers", line, re.I):
                cdm.ntp_configured = True
            elif re.search(r"log-settings", line, re.I):
                cdm.logging_enabled = True
            elif re.search(r"authentication-profile", line, re.I):
                cdm.aaa_configured = True
            elif re.search(r"snmp-setting|snmp-system", line, re.I):
                cdm.snmp_detected = True
                if re.search(r"snmpv3", line, re.I):
                    cdm.snmp_v3 = True
            elif re.search(r"idle-timeout", line, re.I):
                cdm.session_timeout_set = True
            elif re.search(r"deviceconfig system hostname", line, re.I):
                pass  # already captured via _extract_hostname
            else:
                matched = False
            if not matched:
                unrecognized.append(line)
        return cdm, unrecognized
