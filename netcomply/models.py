"""
models.py
The vendor-neutral Common Data Model (CDM) — called the "Security Baseline Model"
in the problem statement. Every vendor parser normalizes its raw config into this
single shape, so the rule engine never has to know which vendor produced it.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import random
import string


@dataclass
class CDM:
    hostname: str = "unknown-device"
    serial: str = ""
    vendor: str = "unknown"
    os: str = "unknown"

    ssh_version: Optional[int] = None
    telnet_enabled: bool = False
    http_enabled: bool = False
    password_encryption: bool = False
    ntp_configured: bool = False
    logging_enabled: bool = False
    aaa_configured: bool = False
    snmp_detected: bool = False
    snmp_v3: bool = False
    session_timeout_set: bool = False

    def __post_init__(self):
        if not self.serial:
            self.serial = "SN-" + "".join(
                random.choices(string.ascii_uppercase + string.digits, k=8)
            )

    def as_dict(self):
        return asdict(self)


@dataclass
class Finding:
    rule_id: str
    title: str
    framework: str
    severity: str          # HIGH / MEDIUM / LOW
    passed: bool
    why: str
    remediation: str


@dataclass
class Device:
    id: str
    filename: str
    vendor: str
    cdm: CDM
    findings: list = field(default_factory=list)
    unrecognized_lines: list = field(default_factory=list)
    raw_config: str = ""

    @property
    def score(self) -> int:
        if not self.findings:
            return 0
        passed = sum(1 for f in self.findings if f.passed)
        return round(100 * passed / len(self.findings))
