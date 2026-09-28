"""
detect.py
Registry of known parsers + vendor auto-detection. Adding a new vendor is a
one-line addition here plus a new file in parsers/ — the rest of the system
(rule engine, reporting) never changes.
"""
from parsers.cisco import CiscoParser
from parsers.juniper import JuniperParser
from parsers.paloalto import PaloAltoParser
from models import CDM

PARSERS = [CiscoParser(), JuniperParser(), PaloAltoParser()]


def detect_and_parse(config_text: str):
    """
    Try each known parser in order. If none matches, fall back to a blank CDM
    and treat every non-empty line as unrecognized — this is what routes a
    genuinely new/unknown vendor into the AI training loop instead of failing.
    Returns (vendor_name, CDM, unrecognized_lines).
    """
    for parser in PARSERS:
        if parser.matches(config_text):
            cdm, unrecognized = parser.parse(config_text)
            return parser.vendor_name, cdm, unrecognized

    # Unknown vendor entirely
    cdm = CDM(vendor="unknown", os="unknown")
    lines = [l.strip() for l in config_text.splitlines() if l.strip() and not l.strip().startswith("#")]
    return "unknown", cdm, lines
