"""
nlp_classifier.py
Implements the "Dynamic Adaptation" / training loop from the problem statement.

Deliberately NOT an LLM call: a compliance PASS/FAIL decision must stay
deterministic and auditable, so the classifier only ever *suggests* a category
for a human to confirm via the Interactive Training Interface. Once confirmed,
the mapping is persisted to data/learned_mappings.json and applied automatically
to every future config containing that keyword -- this is the "heuristics
update without redeploying code" the problem statement asks for.

Swap KEYWORD_RULES for a real embedding-similarity model (e.g. sentence-transformers)
without changing any other module -- classify_line()'s return shape is the contract.
"""
import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "learned_mappings.json")
KEYWORD_RULES = [
    {"pattern": r"idle-timeout|idle timeout|session.*timeout",
     "field": "session_timeout_set", "value": True,
     "category": "Session Timeout (Authentication / Session Security)"},
    {"pattern": r"secure-shell|\bssh\b",
     "field": "ssh_version", "value": 2,
     "category": "SSH Configuration"},
    {"pattern": r"http-legacy|\bhttp\b",
     "field": "http_enabled", "value": True,
     "category": "HTTP Management Interface"},
    {"pattern": r"audit-stream|syslog|\blog\b",
     "field": "logging_enabled", "value": True,
     "category": "Logging / Audit"},
    {"pattern": r"\btelnet\b",
     "field": "telnet_enabled", "value": True,
     "category": "Telnet Access"},
    {"pattern": r"\bntp\b|time.?sync",
     "field": "ntp_configured", "value": True,
     "category": "Time Synchronization (NTP)"},
    {"pattern": r"\baaa\b|authentication|radius|tacacs",
     "field": "aaa_configured", "value": True,
     "category": "AAA / Centralized Authentication"},
    {"pattern": r"\bsnmp\b",
     "field": "snmp_detected", "value": True,
     "category": "SNMP"},
]


def _load_learned() -> dict:
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def _save_learned(mappings: dict):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(mappings, f, indent=2)


def classify_line(line: str):
    """
    Returns a dict describing the best-guess classification, or None.
    {"auto": bool, "field": str, "value": Any, "category": str}
    auto=True means a previously *confirmed* mapping matched -> safe to apply
    without asking again. auto=False means it's a fresh suggestion that still
    needs a human to confirm via the training interface.
    """
    learned = _load_learned()
    lower = line.lower()

    for keyword, mapping in learned.items():
        if keyword.lower() in lower:
            return {"auto": True, **mapping}

    for rule in KEYWORD_RULES:
        if re.search(rule["pattern"], line, re.I):
            return {
                "auto": False,
                "field": rule["field"],
                "value": rule["value"],
                "category": rule["category"],
            }
    return None


def confirm_mapping(line: str, field: str, value, category: str):
    """Called when an admin confirms a suggestion in the training UI."""
    learned = _load_learned()
    tokens = [t for t in re.split(r"\s+", line) if len(t) > 3]
    keyword = tokens[0] if tokens else line[:12]
    learned[keyword] = {"field": field, "value": value, "category": category}
    _save_learned(learned)
    return keyword


def all_learned_mappings() -> dict:
    return _load_learned()
