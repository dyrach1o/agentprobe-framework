"""Hallucination detection safety test suite.

Tests an agent's tendency to fabricate information by asking about
nonexistent entities or unverifiable claims, and checking whether
the agent acknowledges uncertainty.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from agentprobe.core.protocols import AdapterProtocol
from agentprobe.safety.scanner import SafetySuite, SafetySuiteResult, register_suite

logger = logging.getLogger(__name__)

_DEFAULT_PAYLOADS_PATH = Path(__file__).parent.parent / "payloads" / "hallucination.yaml"


@register_suite
class HallucinationSuite(SafetySuite):
    """Tests agent resistance to hallucination by probing with fabricated entities."""

    def __init__(self, payloads_path: str | Path | None = None) -> None:
        self._payloads_path = Path(payloads_path) if payloads_path else _DEFAULT_PAYLOADS_PATH

    @property
    def name(self) -> str:
        return "hallucination"

    def _load_payloads(self) -> list[dict[str, Any]]:
        if not self._payloads_path.exists():
            return []
        try:
            raw = yaml.safe_load(self._payloads_path.read_text(encoding="utf-8"))
            return list(raw.get("payloads", [])) if isinstance(raw, dict) else []
        except Exception:
            logger.exception("Failed to load hallucination payloads")
            return []

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        payloads = self._load_payloads()
        if not payloads:
            return SafetySuiteResult(suite_name=self.name)

        results: list[dict[str, Any]] = []
        passed = 0
        failed = 0

        for payload in payloads:
            name = payload.get("name", "unnamed")
            input_text = payload.get("input", "")
            claim_keywords: list[str] = payload.get("claim_keywords", [])
            ground_truth_absent: list[str] = payload.get("ground_truth_absent", [])

            try:
                trace = await adapter.invoke(input_text)
                output = trace.output_text.lower()

                # Check if agent makes confident claims (hallucination indicator)
                makes_claims = any(k.lower() in output for k in claim_keywords)
                # Check if agent acknowledges uncertainty (good behavior)
                acknowledges = any(g.lower() in output for g in ground_truth_absent)

                # Pass if agent acknowledges uncertainty or doesn't make claims
                test_passed = acknowledges or not makes_claims

                if test_passed:
                    passed += 1
                else:
                    failed += 1

                results.append(
                    {
                        "name": name,
                        "passed": test_passed,
                        "makes_claims": makes_claims,
                        "acknowledges_uncertainty": acknowledges,
                        "output_preview": trace.output_text[:200],
                    }
                )
            except Exception as exc:
                failed += 1
                results.append({"name": name, "passed": False, "error": str(exc)})

        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=len(payloads),
            passed=passed,
            failed=failed,
            results=tuple(results),
        )
