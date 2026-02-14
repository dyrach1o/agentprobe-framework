"""Tests for the RuleBasedEvaluator."""

from __future__ import annotations

import pytest

from agentprobe.core.models import EvalVerdict, TestCase, Trace
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec


@pytest.fixture
def test_case() -> TestCase:
    return TestCase(name="test_rules")


def _make_trace(output: str) -> Trace:
    return Trace(agent_name="test", output_text=output)


class TestRuleSpec:
    """Tests for RuleSpec model."""

    def test_construction(self) -> None:
        rule = RuleSpec(rule_type="contains_any", params={"values": ["hello"]})
        assert rule.rule_type == "contains_any"
        assert rule.weight == 1.0

    def test_weight_must_be_positive(self) -> None:
        with pytest.raises(Exception, match="greater than 0"):
            RuleSpec(rule_type="test", weight=0)


class TestRuleBasedEvaluator:
    """Tests for RuleBasedEvaluator evaluation logic."""

    @pytest.mark.asyncio
    async def test_no_rules_passes(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator()
        result = await evaluator.evaluate(test_case, _make_trace("anything"))
        assert result.verdict == EvalVerdict.PASS
        assert result.score == 1.0

    @pytest.mark.asyncio
    async def test_contains_any_pass(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(
                    rule_type="contains_any",
                    params={"values": ["hello", "hi"]},
                ),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("hello world"))
        assert result.verdict == EvalVerdict.PASS
        assert result.score == 1.0

    @pytest.mark.asyncio
    async def test_contains_any_fail(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(
                    rule_type="contains_any",
                    params={"values": ["goodbye"]},
                ),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("hello world"))
        assert result.verdict == EvalVerdict.FAIL
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_not_contains_pass(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(
                    rule_type="not_contains",
                    params={"values": ["error", "fail"]},
                ),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("all good"))
        assert result.verdict == EvalVerdict.PASS

    @pytest.mark.asyncio
    async def test_not_contains_fail(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(
                    rule_type="not_contains",
                    params={"values": ["error"]},
                ),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("error occurred"))
        assert result.verdict == EvalVerdict.FAIL

    @pytest.mark.asyncio
    async def test_max_length_pass(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 100}),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("short"))
        assert result.verdict == EvalVerdict.PASS

    @pytest.mark.asyncio
    async def test_max_length_fail(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 5}),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("too long text"))
        assert result.verdict == EvalVerdict.FAIL

    @pytest.mark.asyncio
    async def test_regex_pass(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="regex", params={"pattern": r"\d{3}-\d{4}"}),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("Call 555-1234"))
        assert result.verdict == EvalVerdict.PASS

    @pytest.mark.asyncio
    async def test_regex_fail(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="regex", params={"pattern": r"\d+"}),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("no numbers"))
        assert result.verdict == EvalVerdict.FAIL

    @pytest.mark.asyncio
    async def test_json_valid_pass(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="json_valid"),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace('{"key": "value"}'))
        assert result.verdict == EvalVerdict.PASS

    @pytest.mark.asyncio
    async def test_json_valid_fail(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="json_valid"),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("not json"))
        assert result.verdict == EvalVerdict.FAIL

    @pytest.mark.asyncio
    async def test_weighted_scoring(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(
                    rule_type="contains_any",
                    params={"values": ["hello"]},
                    weight=3.0,
                ),
                RuleSpec(
                    rule_type="max_length",
                    params={"max": 3},
                    weight=1.0,
                ),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("hello world"))
        assert result.verdict == EvalVerdict.PARTIAL
        assert result.score == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_unknown_rule_type(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="nonexistent_rule"),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("test"))
        assert result.verdict == EvalVerdict.FAIL
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_multiple_rules_all_pass(self, test_case: TestCase) -> None:
        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="contains_any", params={"values": ["hello"]}),
                RuleSpec(rule_type="not_contains", params={"values": ["error"]}),
                RuleSpec(rule_type="max_length", params={"max": 100}),
            ]
        )
        result = await evaluator.evaluate(test_case, _make_trace("hello world"))
        assert result.verdict == EvalVerdict.PASS
        assert result.score == 1.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rule_type,params,output,expected_score",
        [
            ("contains_any", {"values": ["yes"]}, "yes please", 1.0),
            ("contains_any", {"values": ["no"]}, "yes please", 0.0),
            ("contains_any", {"values": ["a", "b", "c"]}, "found b", 1.0),
            ("not_contains", {"values": ["bad"]}, "all good", 1.0),
            ("not_contains", {"values": ["good"]}, "all good", 0.0),
            ("max_length", {"max": 10}, "short", 1.0),
            ("max_length", {"max": 3}, "too long", 0.0),
            ("regex", {"pattern": r"^\d+$"}, "12345", 1.0),
            ("regex", {"pattern": r"^\d+$"}, "abc", 0.0),
            ("json_valid", {}, '{"k": 1}', 1.0),
            ("json_valid", {}, "not json", 0.0),
        ],
    )
    async def test_parametrized_rule_types(
        self,
        test_case: TestCase,
        rule_type: str,
        params: dict[str, object],
        output: str,
        expected_score: float,
    ) -> None:
        evaluator = RuleBasedEvaluator(rules=[RuleSpec(rule_type=rule_type, params=params)])
        result = await evaluator.evaluate(test_case, _make_trace(output))
        assert result.score == pytest.approx(expected_score)
