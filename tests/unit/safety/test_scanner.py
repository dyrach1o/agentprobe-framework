"""Tests for the SafetyScanner and SafetySuite."""

from __future__ import annotations

import pytest

from agentprobe.core.protocols import AdapterProtocol
from agentprobe.safety.scanner import (
    SafetyScanner,
    SafetySuite,
    SafetySuiteResult,
    get_registered_suites,
)
from tests.fixtures.agents import MockAdapter


class _PassingSuite(SafetySuite):
    """Suite where all tests pass."""

    @property
    def name(self) -> str:
        return "passing-suite"

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=3,
            passed=3,
            failed=0,
            results=(
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": True},
                {"name": "test3", "passed": True},
            ),
        )


class _FailingSuite(SafetySuite):
    """Suite where some tests fail."""

    @property
    def name(self) -> str:
        return "failing-suite"

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=2,
            passed=1,
            failed=1,
            results=(
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": False},
            ),
        )


class _BrokenSuite(SafetySuite):
    """Suite that raises an exception."""

    @property
    def name(self) -> str:
        return "broken-suite"

    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        msg = "suite broke"
        raise RuntimeError(msg)


class TestSafetyScanner:
    """Tests for the SafetyScanner orchestrator."""

    @pytest.mark.asyncio
    async def test_empty_scanner(self) -> None:
        scanner = SafetyScanner()
        adapter = MockAdapter()
        result = await scanner.scan(adapter)
        assert result.total_suites == 0
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_single_passing_suite(self) -> None:
        scanner = SafetyScanner(suites=[_PassingSuite()])
        adapter = MockAdapter()
        result = await scanner.scan(adapter)
        assert result.total_suites == 1
        assert result.total_tests == 3
        assert result.total_passed == 3
        assert result.total_failed == 0

    @pytest.mark.asyncio
    async def test_mixed_suites(self) -> None:
        scanner = SafetyScanner(suites=[_PassingSuite(), _FailingSuite()])
        adapter = MockAdapter()
        result = await scanner.scan(adapter)
        assert result.total_suites == 2
        assert result.total_tests == 5
        assert result.total_passed == 4
        assert result.total_failed == 1

    @pytest.mark.asyncio
    async def test_broken_suite_handled(self) -> None:
        scanner = SafetyScanner(suites=[_BrokenSuite()])
        adapter = MockAdapter()
        result = await scanner.scan(adapter)
        assert result.total_suites == 1
        assert result.total_tests == 0


class TestSafetySuiteAbstract:
    """Tests for SafetySuite abstract interface via concrete implementations."""

    def test_suite_name_returns_string(self) -> None:
        suite = _PassingSuite()
        assert isinstance(suite.name, str)
        assert suite.name == "passing-suite"

    def test_suite_name_unique_per_class(self) -> None:
        passing = _PassingSuite()
        failing = _FailingSuite()
        assert passing.name != failing.name

    @pytest.mark.asyncio
    async def test_suite_run_returns_suite_result(self) -> None:
        suite = _PassingSuite()
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert isinstance(result, SafetySuiteResult)
        assert result.suite_name == "passing-suite"
        assert result.total_tests == 3

    @pytest.mark.asyncio
    async def test_suite_run_failing_returns_failures(self) -> None:
        suite = _FailingSuite()
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert isinstance(result, SafetySuiteResult)
        assert result.suite_name == "failing-suite"
        assert result.failed == 1
        assert result.passed == 1

    @pytest.mark.asyncio
    async def test_suite_run_broken_raises_exception(self) -> None:
        suite = _BrokenSuite()
        adapter = MockAdapter()
        with pytest.raises(RuntimeError, match="suite broke"):
            await suite.run(adapter)


class TestSafetyScannerFromConfig:
    """Tests for SafetyScanner.from_config class method."""

    @pytest.mark.asyncio
    async def test_from_config_with_registered_suite_creates_scanner(self) -> None:
        # Ensure the prompt-injection suite is registered by importing suites
        from agentprobe.safety.suites.prompt_injection import PromptInjectionSuite  # noqa: F401

        scanner = SafetyScanner.from_config(["prompt-injection"])
        # Scanner should have exactly one suite loaded
        assert len(scanner._suites) == 1
        assert scanner._suites[0].name == "prompt-injection"

    @pytest.mark.asyncio
    async def test_from_config_with_unknown_suite_skips_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        scanner = SafetyScanner.from_config(["nonexistent-suite"])
        assert len(scanner._suites) == 0
        assert "Unknown safety suite" in caplog.text
        assert "nonexistent-suite" in caplog.text

    @pytest.mark.asyncio
    async def test_from_config_mixed_known_and_unknown(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        from agentprobe.safety.suites.prompt_injection import PromptInjectionSuite  # noqa: F401

        scanner = SafetyScanner.from_config(["prompt-injection", "does-not-exist"])
        assert len(scanner._suites) == 1
        assert scanner._suites[0].name == "prompt-injection"
        assert "does-not-exist" in caplog.text

    @pytest.mark.asyncio
    async def test_from_config_empty_list_creates_empty_scanner(self) -> None:
        scanner = SafetyScanner.from_config([])
        assert len(scanner._suites) == 0
        adapter = MockAdapter()
        result = await scanner.scan(adapter)
        assert result.total_suites == 0


class TestSuiteRegistry:
    """Tests for suite registration."""

    def test_prompt_injection_registered(self) -> None:
        # Import triggers registration

        suites = get_registered_suites()
        assert "prompt-injection" in suites
