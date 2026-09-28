"""
juniper.py
Parser for Juniper JunOS hierarchical (curly-brace) or `set` style config.
"""
import re
from parsers.base import BaseParser
from models import CDM


class JuniperParser(BaseParser):
    vendor_name = "juniper"

    def matches(self, config_text: str) -> bool:
        return bool(
            re.search(r"host-name\s+\S+;", config_text)
            or re.search(r"^set system", config_text, re.MULTILINE)
            or re.search(r"system\s*\{", config_text)
        )

    def parse(self, config_text: str):
        cdm = CDM(vendor=self.vendor_name, os="JunOS")
        cdm.hostname = self._extract_hostname(
            config_text, [r"host-name\s+(\S+);", r"set system host-name\s+(\S+)"]
        )

        unrecognized = []
        for raw in config_text.splitlines():
            line = raw.strip().rstrip(";")
            if not line or line in ("{", "}"):
                continue
            matched = True
            if re.search(r"protocol-version\s*v2", line, re.I):
                cdm.ssh_version = 2
            elif re.search(r"protocol-version\s*v1", line, re.I):
                cdm.ssh_version = 1
            elif re.search(r"^telnet\s*$|services telnet", line, re.I):
                cdm.telnet_enabled = True
            elif re.search(r"delete system services telnet", line, re.I):
                cdm.telnet_enabled = False
            elif re.search(r"web-management http\b", line, re.I):
                cdm.http_enabled = True
            elif re.search(r"^ntp\b|ntp server", line, re.I):
                cdm.ntp_configured = True
            elif re.search(r"^syslog\b|syslog host", line, re.I):
                cdm.logging_enabled = True
            elif re.search(r"authentication-order|authentication-profile", line, re.I):
                cdm.aaa_configured = True
            elif re.search(r"\bsnmp\b", line, re.I):
                cdm.snmp_detected = True
                if re.search(r"\bv3\b", line, re.I):
                    cdm.snmp_v3 = True
            elif re.search(r"idle-timeout", line, re.I):
                cdm.session_timeout_set = True
            elif re.search(r"^system\b|^services\b|^ssh\b|^host-name", line, re.I):
                pass  # structural container / already-extracted hostname line
            elif re.search(r"^server\s+[\d.]+$", line):
                pass  # nested ntp { server x.x.x.x; } line, parent already handled
            elif re.search(r"^host\s+[\d.]+\s+any", line, re.I):
                pass  # nested syslog { host x.x.x.x any notice; } line, parent already handled
            else:
                matched = False
            if not matched:
                unrecognized.append(line)
        return cdm, unrecognized
