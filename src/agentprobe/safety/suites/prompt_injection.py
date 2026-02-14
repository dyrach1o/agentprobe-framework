"""Prompt injection safety test suite.

Tests an agent's resistance to prompt injection attacks by sending
adversarial payloads and checking for canary tokens or forbidden
phrases in the output.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from agentprobe.core.protocols import AdapterProtocol
from agentprobe.safety.scanner import SafetySuite, SafetySuiteResult, register_suite

logger = logging.getLogger(__name__)

_DEFAULT_PAYLOADS_PATH = Path(__file__).parent.parent / "payloads" / "prompt_injection.yaml"


@register_suite
class PromptInjectionSuite(SafetySuite):
    """Tests an agent's resistance to prompt injection attacks.

    Loads adversarial payloads from a YAML file, sends each to the
    agent adapter, and checks for canary tokens or forbidden phrases
    in the agent's response.
    """

    def __init__(self, payloads_path: str | Path | None = None) -> None:
        """Initialize the prompt injection suite.

        Args:
            payloads_path: Path to YAML payloads file.
                Defaults to the bundled payloads.
        """
        self._payloads_path = Path(payloads_path) if payloads_path else _DEFAULT_PAYLOADS_PATH
        self._payloads: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        """Return the suite name."""
        return "prompt-injection"

    def _load_payloads(self) -> list[dict[str, Any]]:
        """Load payloads from the YAML file."""
        if not self._payloads_path.exists():
            logger.warning("Payloads file not found: %s", self._payloads_path)
            return []

        try:
            raw = yaml.safe_load(self._payloads_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return list(raw.get("payloads", []))
            return []
        except Exception:
            logger.exception("Failed to load payloads from %s", self._payloads_path)
            return []

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        """Execute all prompt injection payloads against the adapter.

        Args:
            adapter: The agent adapter to test.

        Returns:
            Suite results with per-payload details.
        """
        payloads = self._load_payloads()
        if not payloads:
            return SafetySuiteResult(suite_name=self.name)

        results: list[dict[str, Any]] = []
        passed = 0
        failed = 0

        for payload in payloads:
            payload_name = payload.get("name", "unnamed")
            input_text = payload.get("input", "")
            canary_tokens: list[str] = payload.get("canary_tokens", [])
            forbidden_phrases: list[str] = payload.get("forbidden_phrases", [])

            try:
                trace = await adapter.invoke(input_text)
                output = trace.output_text.lower()

                canary_found = any(token.lower() in output for token in canary_tokens)
                forbidden_found = any(phrase.lower() in output for phrase in forbidden_phrases)

                test_passed = not canary_found and not forbidden_found

                if test_passed:
                    passed += 1
                else:
                    failed += 1

                results.append(
                    {
                        "name": payload_name,
                        "passed": test_passed,
                        "canary_found": canary_found,
                        "forbidden_found": forbidden_found,
                        "output_preview": trace.output_text[:200],
                    }
                )

            except Exception as exc:
                failed += 1
                results.append(
                    {
                        "name": payload_name,
                        "passed": False,
                        "error": str(exc),
                    }
                )

        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=len(payloads),
            passed=passed,
            failed=failed,
            results=tuple(results),
        )
