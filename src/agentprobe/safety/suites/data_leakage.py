"""Data leakage safety test suite.

Tests agent resistance to system prompt extraction, PII leakage,
and secret exposure attacks.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from agentprobe.core.protocols import AdapterProtocol
from agentprobe.safety.scanner import SafetySuite, SafetySuiteResult, register_suite

logger = logging.getLogger(__name__)

_DEFAULT_PAYLOADS_PATH = Path(__file__).parent.parent / "payloads" / "data_leakage.yaml"


@register_suite
class DataLeakageSuite(SafetySuite):
    """Tests agent resistance to data leakage attacks."""

    def __init__(self, payloads_path: str | Path | None = None) -> None:
        self._payloads_path = Path(payloads_path) if payloads_path else _DEFAULT_PAYLOADS_PATH

    @property
    def name(self) -> str:
        return "data-leakage"

    def _load_payloads(self) -> list[dict[str, Any]]:
        if not self._payloads_path.exists():
            return []
        try:
            raw = yaml.safe_load(self._payloads_path.read_text(encoding="utf-8"))
            return list(raw.get("payloads", [])) if isinstance(raw, dict) else []
        except Exception:
            logger.exception("Failed to load data leakage payloads")
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
            forbidden: list[str] = payload.get("forbidden_phrases", [])

            try:
                trace = await adapter.invoke(input_text)
                output = trace.output_text.lower()
                forbidden_found = any(p.lower() in output for p in forbidden)
                test_passed = not forbidden_found

                if test_passed:
                    passed += 1
                else:
                    failed += 1
                results.append(
                    {
                        "name": name,
                        "passed": test_passed,
                        "forbidden_found": forbidden_found,
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
