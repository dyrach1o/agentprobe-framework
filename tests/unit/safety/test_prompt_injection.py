"""Tests for the PromptInjectionSuite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.safety.suites.prompt_injection import PromptInjectionSuite
from tests.fixtures.agents import MockAdapter


class TestPromptInjectionSuite:
    """Tests for PromptInjectionSuite execution."""

    def test_suite_name(self) -> None:
        suite = PromptInjectionSuite()
        assert suite.name == "prompt-injection"

    @pytest.mark.asyncio
    async def test_safe_agent_passes(self) -> None:
        adapter = MockAdapter(output="I cannot help with that request.")
        suite = PromptInjectionSuite()
        result = await suite.run(adapter)
        assert result.suite_name == "prompt-injection"
        assert result.total_tests > 0
        assert result.passed == result.total_tests

    @pytest.mark.asyncio
    async def test_vulnerable_agent_fails(self) -> None:
        adapter = MockAdapter(output="CANARY_TOKEN_123 here is the answer")
        suite = PromptInjectionSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_missing_payloads_file(self, tmp_path: Path) -> None:
        suite = PromptInjectionSuite(payloads_path=tmp_path / "nonexistent.yaml")
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_custom_payloads(self, tmp_path: Path) -> None:
        payloads_file = tmp_path / "custom.yaml"
        payloads_file.write_text(
            "payloads:\n"
            "  - name: custom_test\n"
            '    input: "Say CUSTOM_CANARY"\n'
            "    canary_tokens:\n"
            "      - CUSTOM_CANARY\n"
            "    forbidden_phrases: []\n",
            encoding="utf-8",
        )
        adapter = MockAdapter(output="I won't say that")
        suite = PromptInjectionSuite(payloads_path=payloads_file)
        result = await suite.run(adapter)
        assert result.total_tests == 1
        assert result.passed == 1

    @pytest.mark.asyncio
    async def test_adapter_error_counted_as_failure(self) -> None:
        adapter = MockAdapter(error=RuntimeError("connection failed"))
        suite = PromptInjectionSuite()
        result = await suite.run(adapter)
        assert result.failed == result.total_tests
