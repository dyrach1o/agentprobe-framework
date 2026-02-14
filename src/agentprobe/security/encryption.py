"""Field-level hashing and masking utilities.

Provides deterministic SHA-256 hashing for PII fingerprinting and
partial masking for display purposes. Uses only stdlib hashlib.
"""

from __future__ import annotations

import hashlib


class FieldEncryptor:
    """Hashes and masks field values for security purposes.

    Provides deterministic hashing for fingerprinting sensitive data
    and partial masking for safe display.
    """

    def hash_value(self, text: str) -> str:
        """Compute a deterministic SHA-256 hash of the input.

        Args:
            text: The plaintext value to hash.

        Returns:
            Hex-encoded SHA-256 hash string.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def mask_value(self, text: str, visible_chars: int = 4) -> str:
        """Partially mask a value, keeping only trailing characters visible.

        Args:
            text: The value to mask.
            visible_chars: Number of trailing characters to keep visible.

        Returns:
            Masked string with asterisks replacing hidden characters.
        """
        if len(text) <= visible_chars:
            return "*" * len(text)
        masked_len = len(text) - visible_chars
        return "*" * masked_len + text[-visible_chars:]
