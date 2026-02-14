"""Structured audit logging for security events.

Records security-relevant events (PII scans, redactions, data access)
in a structured JSON format using stdlib logging.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AuditEventType(StrEnum):
    """Types of auditable security events."""

    PII_SCAN = "pii_scan"
    PII_REDACTION = "pii_redaction"
    TRACE_ACCESS = "trace_access"
    RESULT_ACCESS = "result_access"


class AuditSeverity(StrEnum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditLogger:
    """Logs structured security audit events.

    Uses stdlib logging with JSON-formatted messages for integration
    with log aggregation systems.

    Attributes:
        logger_name: Name of the underlying logger.
    """

    def __init__(self, logger_name: str = "agentprobe.security.audit") -> None:
        """Initialize the audit logger.

        Args:
            logger_name: Name for the underlying Python logger.
        """
        self._logger = logging.getLogger(logger_name)
        self._logger_name = logger_name

    @property
    def logger_name(self) -> str:
        """Return the configured logger name."""
        return self._logger_name

    def log_event(
        self,
        event_type: AuditEventType,
        *,
        details: dict[str, Any] | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> dict[str, Any]:
        """Log a structured security audit event.

        Args:
            event_type: The type of security event.
            details: Optional additional context as key-value pairs.
            severity: Severity level of the event.

        Returns:
            The structured event record that was logged.
        """
        record: dict[str, Any] = {
            "event_type": event_type.value,
            "severity": severity.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "details": details or {},
        }

        log_level = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }[severity]

        self._logger.log(log_level, json.dumps(record))
        return record
