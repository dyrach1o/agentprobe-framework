"""PII detection and redaction utilities.

Provides pattern-based scanning for common PII types (email, phone,
SSN, credit card, IP address) with scan and redact operations.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field


class PIIMatch(BaseModel):
    """A single PII detection match.

    Attributes:
        pii_type: Category of PII detected.
        value: The matched text.
        start: Start index in the source text.
        end: End index in the source text.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    pii_type: str
    value: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)


# ── Regex patterns for common PII types ──

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone_us": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

_REDACTION_LABELS: dict[str, str] = {
    "email": "[EMAIL]",
    "phone_us": "[PHONE]",
    "ssn": "[SSN]",
    "credit_card": "[CREDIT_CARD]",
    "ipv4": "[IP_ADDRESS]",
}


class PIIRedactor:
    """Scans text for PII and optionally redacts matches.

    Supports configurable PII types and custom patterns.

    Attributes:
        enabled_types: Set of PII type names to detect.
    """

    def __init__(
        self,
        enabled_types: set[str] | None = None,
        custom_patterns: dict[str, re.Pattern[str]] | None = None,
    ) -> None:
        """Initialize the PII redactor.

        Args:
            enabled_types: PII types to enable. None enables all built-in types.
            custom_patterns: Additional named patterns to check.
        """
        self._patterns: dict[str, re.Pattern[str]] = {}

        if enabled_types is None:
            self._patterns.update(_PII_PATTERNS)
        else:
            for pii_type in enabled_types:
                if pii_type in _PII_PATTERNS:
                    self._patterns[pii_type] = _PII_PATTERNS[pii_type]

        if custom_patterns:
            self._patterns.update(custom_patterns)

    def scan(self, text: str) -> list[PIIMatch]:
        """Scan text for PII matches.

        Args:
            text: The text to scan.

        Returns:
            List of PII matches found, sorted by position.
        """
        matches: list[PIIMatch] = []

        for pii_type, pattern in self._patterns.items():
            matches.extend(
                PIIMatch(
                    pii_type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                )
                for match in pattern.finditer(text)
            )

        matches.sort(key=lambda m: m.start)
        return matches

    def redact(self, text: str) -> str:
        """Redact all detected PII from text.

        Replaces each match with a type-specific label (e.g. [EMAIL]).

        Args:
            text: The text to redact.

        Returns:
            Text with PII replaced by labels.
        """
        matches = self.scan(text)
        if not matches:
            return text

        # Process matches in reverse order to preserve indices
        result = text
        for match in reversed(matches):
            label = _REDACTION_LABELS.get(match.pii_type, f"[{match.pii_type.upper()}]")
            result = result[: match.start] + label + result[match.end :]

        return result

    def has_pii(self, text: str) -> bool:
        """Check if text contains any detectable PII.

        Args:
            text: The text to check.

        Returns:
            True if PII was detected.
        """
        return len(self.scan(text)) > 0
