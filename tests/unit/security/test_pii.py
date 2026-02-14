"""Tests for the PIIRedactor."""

from __future__ import annotations

import re

import pytest

from agentprobe.security.pii import PIIRedactor


class TestPIIRedactor:
    """Tests for PII scanning and redaction."""

    @pytest.fixture
    def redactor(self) -> PIIRedactor:
        return PIIRedactor()

    def test_detect_email(self, redactor: PIIRedactor) -> None:
        matches = redactor.scan("Contact john@example.com for details")
        assert len(matches) == 1
        assert matches[0].pii_type == "email"
        assert matches[0].value == "john@example.com"

    def test_detect_phone(self, redactor: PIIRedactor) -> None:
        matches = redactor.scan("Call 555-123-4567 for info")
        assert any(m.pii_type == "phone_us" for m in matches)

    def test_detect_ssn(self, redactor: PIIRedactor) -> None:
        matches = redactor.scan("SSN: 123-45-6789")
        assert any(m.pii_type == "ssn" for m in matches)

    def test_detect_credit_card(self, redactor: PIIRedactor) -> None:
        matches = redactor.scan("Card: 4111 1111 1111 1111")
        assert any(m.pii_type == "credit_card" for m in matches)

    def test_detect_ipv4(self, redactor: PIIRedactor) -> None:
        matches = redactor.scan("Server at 192.168.1.100")
        assert any(m.pii_type == "ipv4" for m in matches)

    def test_no_pii(self, redactor: PIIRedactor) -> None:
        matches = redactor.scan("This text has no personal info")
        assert len(matches) == 0

    def test_redact_email(self, redactor: PIIRedactor) -> None:
        result = redactor.redact("Email: john@example.com please")
        assert "[EMAIL]" in result
        assert "john@example.com" not in result

    def test_redact_ssn(self, redactor: PIIRedactor) -> None:
        result = redactor.redact("SSN is 123-45-6789")
        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_redact_multiple(self, redactor: PIIRedactor) -> None:
        text = "Email john@example.com, SSN 123-45-6789"
        result = redactor.redact(text)
        assert "[EMAIL]" in result
        assert "[SSN]" in result
        assert "john@example.com" not in result

    def test_no_pii_unchanged(self, redactor: PIIRedactor) -> None:
        text = "Nothing to redact here"
        assert redactor.redact(text) == text

    def test_has_pii_true(self, redactor: PIIRedactor) -> None:
        assert redactor.has_pii("My email is test@test.com")

    def test_has_pii_false(self, redactor: PIIRedactor) -> None:
        assert not redactor.has_pii("No PII here")

    def test_enabled_types_filter(self) -> None:
        redactor = PIIRedactor(enabled_types={"email"})
        email_matches = redactor.scan("john@example.com and 123-45-6789")
        assert all(m.pii_type == "email" for m in email_matches)

    def test_custom_pattern(self) -> None:
        custom = {"account_id": re.compile(r"ACCT-\d{6}")}
        redactor = PIIRedactor(enabled_types=set(), custom_patterns=custom)
        matches = redactor.scan("Account: ACCT-123456")
        assert len(matches) == 1
        assert matches[0].pii_type == "account_id"

    def test_match_positions(self, redactor: PIIRedactor) -> None:
        text = "Email: john@example.com here"
        matches = redactor.scan(text)
        assert len(matches) >= 1
        email_match = next(m for m in matches if m.pii_type == "email")
        assert text[email_match.start : email_match.end] == "john@example.com"


class TestPIIParametrized:
    """Parametrized edge case tests for PII detection."""

    @pytest.fixture
    def redactor(self) -> PIIRedactor:
        return PIIRedactor()

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",
            "first.last@company.org",
            "user+tag@example.co.uk",
            "test_user@sub.domain.com",
            "a@b.cd",
        ],
    )
    def test_email_variations(self, redactor: PIIRedactor, email: str) -> None:
        matches = redactor.scan(f"Contact {email} for details")
        assert any(m.pii_type == "email" and m.value == email for m in matches)

    @pytest.mark.parametrize(
        "phone",
        [
            "555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "5551234567",
        ],
    )
    def test_phone_variations(self, redactor: PIIRedactor, phone: str) -> None:
        matches = redactor.scan(f"Call {phone} now")
        assert any(m.pii_type == "phone_us" for m in matches)

    @pytest.mark.parametrize(
        "ssn",
        [
            "123-45-6789",
            "000-00-0000",
            "999-99-9999",
        ],
    )
    def test_ssn_variations(self, redactor: PIIRedactor, ssn: str) -> None:
        matches = redactor.scan(f"SSN: {ssn}")
        assert any(m.pii_type == "ssn" for m in matches)

    @pytest.mark.parametrize(
        "text,has_pii",
        [
            ("No personal info here", False),
            ("Just some regular text with numbers 42", False),
            ("My email is test@test.com", True),
            ("SSN: 123-45-6789", True),
        ],
    )
    def test_has_pii_parametrized(self, redactor: PIIRedactor, text: str, has_pii: bool) -> None:
        assert redactor.has_pii(text) == has_pii
