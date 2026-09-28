"""
base.py
Defines the contract every vendor parser must follow. A parser's only job is:
raw config text -> (CDM, list of lines it could not interpret).
Unrecognized lines get handed to the NLP classifier / training loop, never dropped.
"""
from abc import ABC, abstractmethod
from models import CDM


class BaseParser(ABC):
    vendor_name = "generic"

    @abstractmethod
    def matches(self, config_text: str) -> bool:
        """Return True if this parser recognizes the config's dialect."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, config_text: str) -> tuple[CDM, list[str]]:
        """Return (populated CDM, list of unrecognized raw lines)."""
        raise NotImplementedError

    def _extract_hostname(self, config_text: str, patterns: list[str]) -> str:
        import re
        for pat in patterns:
            m = re.search(pat, config_text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip().rstrip(";")
        return "unknown-device"
