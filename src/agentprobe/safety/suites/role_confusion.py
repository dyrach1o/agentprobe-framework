"""Role confusion safety test suite.

Tests agent resistance to role boundary violations including
role switching, identity confusion, and authority escalation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from agentprobe.core.protocols import AdapterProtocol
from agentprobe.safety.scanner import SafetySuite, SafetySuiteResult, register_suite

logger = logging.getLogger(__name__)

_DEFAULT_PAYLOADS_PATH = Path(__file__).parent.parent / "payloads" / "role_confusion.yaml"


@register_suite
class RoleConfusionSuite(SafetySuite):
    """Tests agent resistance to role confusion attacks."""

    def __init__(self, payloads_path: str | Path | None = None) -> None:
        self._payloads_path = Path(payloads_path) if payloads_path else _DEFAULT_PAYLOADS_PATH

    @property
    def name(self) -> str:
        return "role-confusion"

    def _load_payloads(self) -> list[dict[str, Any]]:
        if not self._payloads_path.exists():
            return []
        try:
            raw = yaml.safe_load(self._payloads_path.read_text(encoding="utf-8"))
            return list(raw.get("payloads", [])) if isinstance(raw, dict) else []
        except Exception:
            logger.exception("Failed to load role confusion payloads")
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
            canary_tokens: list[str] = payload.get("canary_tokens", [])
            forbidden: list[str] = payload.get("forbidden_phrases", [])

            try:
                trace = await adapter.invoke(input_text)
                output = trace.output_text.lower()
                canary_found = any(t.lower() in output for t in canary_tokens)
                forbidden_found = any(p.lower() in output for p in forbidden)
                test_passed = not canary_found and not forbidden_found

                if test_passed:
                    passed += 1
                else:
                    failed += 1
                results.append(
                    {
                        "name": name,
                        "passed": test_passed,
                        "canary_found": canary_found,
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
