"""Integration test: SafetyScanner + custom suites + MockAdapter."""

from __future__ import annotations

import pytest

from agentprobe.core.protocols import AdapterProtocol
from agentprobe.safety.scanner import SafetyScanner, SafetySuite, SafetySuiteResult
from tests.fixtures.agents import MockAdapter


class _PassingSuite(SafetySuite):
    """A safety suite where all tests pass."""

    @property
    def name(self) -> str:
        return "passing-suite"

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        # Invoke the adapter with a test prompt
        await adapter.invoke("safe prompt")
        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=3,
            passed=3,
            failed=0,
            results=(
                {"test": "no_pii_leak", "passed": True},
                {"test": "no_jailbreak", "passed": True},
                {"test": "no_harmful_output", "passed": True},
            ),
        )


class _FailingSuite(SafetySuite):
    """A safety suite that detects issues."""

    @property
    def name(self) -> str:
        return "failing-suite"

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        trace = await adapter.invoke("malicious prompt")
        output = trace.output_text
        # Simulate detecting a problem in the output
        failed = 1 if "mock" in output.lower() else 0
        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=2,
            passed=2 - failed,
            failed=failed,
            results=(
                {"test": "injection_check", "passed": failed == 0},
                {"test": "boundary_check", "passed": True},
            ),
        )


class _ErrorSuite(SafetySuite):
    """A safety suite that raises an error."""

    @property
    def name(self) -> str:
        return "error-suite"

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        raise RuntimeError("Suite crashed")


@pytest.mark.integration
class TestSafetyFlow:
    """End-to-end safety scanning."""

    @pytest.mark.asyncio
    async def test_scan_all_passing(self) -> None:
        """All suites pass cleanly."""
        adapter = MockAdapter(name="safe-agent", output="Perfectly safe response.")
        scanner = SafetyScanner(suites=[_PassingSuite()])

        result = await scanner.scan(adapter)

        assert result.total_suites == 1
        assert result.total_tests == 3
        assert result.total_passed == 3
        assert result.total_failed == 0

    @pytest.mark.asyncio
    async def test_scan_with_failures(self) -> None:
        """One suite detects an issue."""
        adapter = MockAdapter(name="leaky-agent", output="mock output with data")
        scanner = SafetyScanner(suites=[_PassingSuite(), _FailingSuite()])

        result = await scanner.scan(adapter)

        assert result.total_suites == 2
        assert result.total_failed >= 1
        assert result.total_passed >= 3  # passing suite contributes 3

    @pytest.mark.asyncio
    async def test_scan_error_isolation(self) -> None:
        """A crashing suite doesn't break the scan."""
        adapter = MockAdapter(name="ok-agent", output="fine")
        scanner = SafetyScanner(suites=[_ErrorSuite(), _PassingSuite()])

        result = await scanner.scan(adapter)

        assert result.total_suites == 2
        # Error suite contributes 0 tests; passing suite contributes 3
        assert result.total_tests == 3
        assert result.total_passed == 3

    @pytest.mark.asyncio
    async def test_scan_empty_suites(self) -> None:
        """Scanner with no suites returns empty result."""
        adapter = MockAdapter(name="any-agent")
        scanner = SafetyScanner(suites=[])

        result = await scanner.scan(adapter)

        assert result.total_suites == 0
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_scan_multiple_suites_aggregate(self) -> None:
        """Results are properly aggregated across suites."""
        adapter = MockAdapter(name="test-agent", output="mock output")
        scanner = SafetyScanner(suites=[_PassingSuite(), _PassingSuite(), _FailingSuite()])

        result = await scanner.scan(adapter)

        assert result.total_suites == 3
        assert result.total_tests == 8  # 3 + 3 + 2
        assert len(result.suite_results) == 3
