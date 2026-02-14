"""Tests for the LLMJudge evaluator."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agentprobe.core.exceptions import JudgeAPIError
from agentprobe.core.models import EvalVerdict, TestCase, Trace
from agentprobe.eval.llm_judge import LLMJudge


@pytest.fixture
def test_case() -> TestCase:
    return TestCase(name="test_judge", input_text="What is 2+2?", expected_output="4")


@pytest.fixture
def trace() -> Trace:
    return Trace(agent_name="test", output_text="The answer is 4.")


class TestLLMJudge:
    """Tests for LLMJudge evaluation logic."""

    def test_build_prompt_basic(self, test_case: TestCase, trace: Trace) -> None:
        judge = LLMJudge(api_key="test-key")
        prompt = judge._build_prompt(test_case, trace)
        assert "What is 2+2?" in prompt
        assert "The answer is 4." in prompt
        assert "Expected Output" in prompt

    def test_build_prompt_without_expected(self) -> None:
        tc = TestCase(name="test", input_text="Hello")
        trace = Trace(agent_name="test", output_text="Hi")
        judge = LLMJudge(api_key="test-key")
        prompt = judge._build_prompt(tc, trace)
        assert "Expected Output" not in prompt

    def test_build_prompt_with_rubric(self, test_case: TestCase, trace: Trace) -> None:
        judge = LLMJudge(api_key="test-key", rubric="Must be concise")
        prompt = judge._build_prompt(test_case, trace)
        assert "Must be concise" in prompt

    def test_parse_valid_response(self) -> None:
        judge = LLMJudge(api_key="test-key")
        result = judge._parse_response('{"verdict": "pass", "score": 0.95, "reason": "Correct"}')
        assert result.verdict == EvalVerdict.PASS
        assert result.score == 0.95
        assert result.reason == "Correct"

    def test_parse_fail_response(self) -> None:
        judge = LLMJudge(api_key="test-key")
        result = judge._parse_response('{"verdict": "fail", "score": 0.1, "reason": "Wrong"}')
        assert result.verdict == EvalVerdict.FAIL
        assert result.score == 0.1

    def test_parse_partial_response(self) -> None:
        judge = LLMJudge(api_key="test-key")
        result = judge._parse_response(
            '{"verdict": "partial", "score": 0.5, "reason": "Half right"}'
        )
        assert result.verdict == EvalVerdict.PARTIAL

    def test_parse_invalid_json(self) -> None:
        judge = LLMJudge(api_key="test-key")
        result = judge._parse_response("not json at all")
        assert result.verdict == EvalVerdict.ERROR

    def test_parse_json_with_surrounding_text(self) -> None:
        judge = LLMJudge(api_key="test-key")
        response = 'Here is the result: {"verdict": "pass", "score": 1.0, "reason": "Great"}'
        result = judge._parse_response(response)
        assert result.verdict == EvalVerdict.PASS

    def test_score_clamped(self) -> None:
        judge = LLMJudge(api_key="test-key")
        result = judge._parse_response('{"verdict": "pass", "score": 5.0, "reason": ""}')
        assert result.score == 1.0

        result = judge._parse_response('{"verdict": "fail", "score": -1.0, "reason": ""}')
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_missing_api_key_raises(self, test_case: TestCase, trace: Trace) -> None:
        judge = LLMJudge(provider="anthropic")
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(JudgeAPIError, match="ANTHROPIC_API_KEY"),
        ):
            await judge._call_api("test prompt")

    @pytest.mark.asyncio
    async def test_unknown_provider_raises(self, test_case: TestCase, trace: Trace) -> None:
        judge = LLMJudge(provider="unknown", api_key="key")
        with pytest.raises(JudgeAPIError, match="Unknown provider"):
            await judge._call_api("test prompt")
