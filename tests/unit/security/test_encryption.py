"""Tests for the FieldEncryptor."""

from __future__ import annotations

import pytest

from agentprobe.security.encryption import FieldEncryptor


class TestFieldEncryptor:
    """Tests for hashing and masking utilities."""

    @pytest.fixture
    def encryptor(self) -> FieldEncryptor:
        return FieldEncryptor()

    def test_hash_deterministic(self, encryptor: FieldEncryptor) -> None:
        h1 = encryptor.hash_value("hello")
        h2 = encryptor.hash_value("hello")
        assert h1 == h2

    def test_hash_different_inputs_differ(self, encryptor: FieldEncryptor) -> None:
        h1 = encryptor.hash_value("hello")
        h2 = encryptor.hash_value("world")
        assert h1 != h2

    def test_hash_returns_hex_string(self, encryptor: FieldEncryptor) -> None:
        h = encryptor.hash_value("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_empty_string(self, encryptor: FieldEncryptor) -> None:
        h = encryptor.hash_value("")
        assert len(h) == 64

    def test_hash_unicode(self, encryptor: FieldEncryptor) -> None:
        h = encryptor.hash_value("caf\u00e9 \u2615")
        assert len(h) == 64

    def test_mask_default_visible(self, encryptor: FieldEncryptor) -> None:
        result = encryptor.mask_value("12345678")
        assert result == "****5678"

    def test_mask_custom_visible_chars(self, encryptor: FieldEncryptor) -> None:
        result = encryptor.mask_value("12345678", visible_chars=2)
        assert result == "******78"

    def test_mask_shorter_than_visible(self, encryptor: FieldEncryptor) -> None:
        result = encryptor.mask_value("ab", visible_chars=4)
        assert result == "**"

    def test_mask_empty_string(self, encryptor: FieldEncryptor) -> None:
        result = encryptor.mask_value("")
        assert result == ""

    def test_mask_exact_visible_length(self, encryptor: FieldEncryptor) -> None:
        result = encryptor.mask_value("abcd", visible_chars=4)
        assert result == "****"
