"""Factory functions for creating safety test objects."""

from __future__ import annotations

from typing import Any

from agentprobe.safety.scanner import SafetyScanResult, SafetySuiteResult


def make_safety_suite_result(
    *,
    suite_name: str = "prompt-injection",
    total_tests: int = 10,
    passed: int = 8,
    failed: int = 2,
    results: list[dict[str, Any]] | None = None,
) -> SafetySuiteResult:
    """Create a SafetySuiteResult with sensible defaults for testing."""
    return SafetySuiteResult(
        suite_name=suite_name,
        total_tests=total_tests,
        passed=passed,
        failed=failed,
        results=tuple(results or []),
    )


def make_safety_scan_result(
    *,
    suite_results: list[SafetySuiteResult] | None = None,
) -> SafetyScanResult:
    """Create a SafetyScanResult with sensible defaults for testing.

    Automatically computes aggregate totals from suite results.
    """
    resolved = suite_results or [make_safety_suite_result()]
    return SafetyScanResult(
        total_suites=len(resolved),
        total_tests=sum(s.total_tests for s in resolved),
        total_passed=sum(s.passed for s in resolved),
        total_failed=sum(s.failed for s in resolved),
        suite_results=tuple(resolved),
    )
