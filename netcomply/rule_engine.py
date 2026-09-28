"""
rule_engine.py
The "Deviation Analysis" stage: rules are written once against the CDM and
therefore work identically for every vendor. This is a CIS-benchmark-style
subset; extend RULES with NIST/STIG/ISO entries by adding a `framework` value
-- the engine itself never needs to change per framework.
"""
from models import CDM, Finding
REMEDIATION = {
    "ssh_version": {
        "cisco": "ip ssh version 2",
        "juniper": "set system services ssh protocol-version v2",
        "paloalto": "set deviceconfig system ssh protocol-version v2",
        "generic": "Configure SSH protocol version 2",
    },
    "telnet_disabled": {
        "cisco": "line vty 0 4\n transport input ssh",
        "juniper": "delete system services telnet",
        "paloalto": "set deviceconfig system service disable-telnet yes",
        "generic": "Disable Telnet management access",
    },
    "http_mgmt_disabled": {
        "cisco": "no ip http server",
        "juniper": "delete system services web-management http",
        "paloalto": "set deviceconfig system service disable-http yes",
        "generic": "Disable HTTP admin interface, use HTTPS only",
    },
    "password_encryption": {
        "cisco": "service password-encryption",
        "juniper": "(passwords are hashed by default -- verify $9$ hash present)",
        "paloalto": "set deviceconfig system password-complexity enabled yes",
        "generic": "Enable password/secret encryption",
    },
    "ntp_configured": {
        "cisco": "ntp server 10.0.0.1",
        "juniper": "set system ntp server 10.0.0.1",
        "paloalto": "set deviceconfig system ntp-servers primary-ntp-server ntp-server-address 10.0.0.1",
        "generic": "Configure at least one NTP server",
    },
    "logging_enabled": {
        "cisco": "logging host 10.0.0.5\nlogging trap informational",
        "juniper": "set system syslog host 10.0.0.5 any notice",
        "paloalto": "set shared log-settings syslog",
        "generic": "Send logs to a central syslog collector",
    },
    "aaa_enabled": {
        "cisco": "aaa new-model",
        "juniper": "set system authentication-order [ tacplus password ]",
        "paloalto": "set shared authentication-profile",
        "generic": "Enable centralized AAA (TACACS+/RADIUS)",
    },
    "snmp_v3": {
        "cisco": "snmp-server group V3GROUP v3 priv",
        "juniper": "set snmp v3",
        "paloalto": "set deviceconfig system snmp-setting snmp-system snmpv3",
        "generic": "Migrate SNMP to v3 with auth+priv",
    },
    "session_timeout": {
        "cisco": "line vty 0 4\n exec-timeout 10 0",
        "juniper": "set system login idle-timeout 10",
        "paloalto": "set deviceconfig system idle-timeout 10",
        "generic": "Set idle timeout to 10 minutes or less",
    },
}

RULES = [
    {"id": "ssh_version", "framework": "CIS", "severity": "HIGH",
     "title": "SSH must use version 2",
     "check": lambda c: c.ssh_version == 2,
     "why": "SSHv1 has known cryptographic weaknesses and is vulnerable to MITM attacks."},
    {"id": "telnet_disabled", "framework": "CIS", "severity": "HIGH",
     "title": "Telnet must be disabled on management lines",
     "check": lambda c: not c.telnet_enabled,
     "why": "Telnet transmits credentials and session data in plaintext."},
    {"id": "http_mgmt_disabled", "framework": "CIS", "severity": "MEDIUM",
     "title": "Unencrypted HTTP management must be disabled",
     "check": lambda c: not c.http_enabled,
     "why": "Plaintext HTTP exposes admin sessions to interception."},
    {"id": "password_encryption", "framework": "CIS", "severity": "HIGH",
     "title": "Password encryption service must be enabled",
     "check": lambda c: c.password_encryption,
     "why": "Without this, secrets may be stored/displayed in plaintext in the config."},
    {"id": "ntp_configured", "framework": "CIS", "severity": "MEDIUM",
     "title": "NTP time source must be configured",
     "check": lambda c: c.ntp_configured,
     "why": "Accurate timestamps are required for correlating logs during incident response."},
    {"id": "logging_enabled", "framework": "CIS", "severity": "MEDIUM",
     "title": "Centralized logging must be enabled",
     "check": lambda c: c.logging_enabled,
     "why": "Without logging, administrative access and changes cannot be audited."},
    {"id": "aaa_enabled", "framework": "CIS", "severity": "HIGH",
     "title": "AAA authentication must be enabled",
     "check": lambda c: c.aaa_configured,
     "why": "Local-only auth lacks centralized accounting and lockout policy."},
    {"id": "snmp_v3", "framework": "CIS", "severity": "MEDIUM",
     "title": "SNMP must use v3 (not v1/v2c with default community)",
     "check": lambda c: c.snmp_v3 or not c.snmp_detected,
     "why": "SNMP v1/v2c sends community strings in plaintext and is often left at 'public'."},
    {"id": "session_timeout", "framework": "CIS", "severity": "LOW",
     "title": "Administrative idle session timeout must be configured",
     "check": lambda c: c.session_timeout_set,
     "why": "Unattended sessions left open are a common lateral-movement vector."},
]


def evaluate(cdm: CDM, vendor: str) -> list:
    from models import Finding
    findings = []
    for rule in RULES:
        passed = rule["check"](cdm)
        fix = REMEDIATION[rule["id"]].get(vendor, REMEDIATION[rule["id"]]["generic"])
        findings.append(Finding(
            rule_id=rule["id"], title=rule["title"], framework=rule["framework"],
            severity=rule["severity"], passed=passed, why=rule["why"], remediation=fix,
        ))
    return findings
