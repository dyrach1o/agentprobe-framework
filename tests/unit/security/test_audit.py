"""Tests for the AuditLogger."""

from __future__ import annotations

import json
import logging

import pytest

from agentprobe.security.audit import AuditEventType, AuditLogger, AuditSeverity


class TestAuditLogger:
    """Tests for structured security audit logging."""

    @pytest.fixture
    def audit_logger(self) -> AuditLogger:
        return AuditLogger()

    def test_log_basic_event(self, audit_logger: AuditLogger) -> None:
        record = audit_logger.log_event(AuditEventType.PII_SCAN)
        assert record["event_type"] == "pii_scan"
        assert record["severity"] == "info"
        assert "timestamp" in record

    def test_log_event_with_details(self, audit_logger: AuditLogger) -> None:
        details = {"file": "trace.json", "matches": 3}
        record = audit_logger.log_event(AuditEventType.PII_REDACTION, details=details)
        assert record["details"] == details

    @pytest.mark.parametrize(
        "severity",
        [AuditSeverity.INFO, AuditSeverity.WARNING, AuditSeverity.CRITICAL],
    )
    def test_severity_levels(self, audit_logger: AuditLogger, severity: AuditSeverity) -> None:
        record = audit_logger.log_event(AuditEventType.TRACE_ACCESS, severity=severity)
        assert record["severity"] == severity.value

    @pytest.mark.parametrize(
        "event_type",
        list(AuditEventType),
    )
    def test_event_types(self, audit_logger: AuditLogger, event_type: AuditEventType) -> None:
        record = audit_logger.log_event(event_type)
        assert record["event_type"] == event_type.value

    def test_multiple_events(self, audit_logger: AuditLogger) -> None:
        r1 = audit_logger.log_event(AuditEventType.PII_SCAN)
        r2 = audit_logger.log_event(AuditEventType.RESULT_ACCESS)
        assert r1["event_type"] != r2["event_type"]

    def test_logger_name_hierarchy(self) -> None:
        custom_logger = AuditLogger(logger_name="agentprobe.security.audit.test")
        assert custom_logger.logger_name == "agentprobe.security.audit.test"

    def test_json_structure(
        self, audit_logger: AuditLogger, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="agentprobe.security.audit"):
            audit_logger.log_event(
                AuditEventType.PII_SCAN,
                details={"count": 5},
                severity=AuditSeverity.INFO,
            )

        assert len(caplog.records) == 1
        parsed = json.loads(caplog.records[0].message)
        assert parsed["event_type"] == "pii_scan"
        assert parsed["details"]["count"] == 5

    def test_default_details_empty_dict(self, audit_logger: AuditLogger) -> None:
        record = audit_logger.log_event(AuditEventType.TRACE_ACCESS)
        assert record["details"] == {}
