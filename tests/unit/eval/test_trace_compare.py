"""Tests for trace comparison evaluator."""

from __future__ import annotations

import pytest

from agentprobe.core.models import EvalVerdict, TestCase, Trace
from agentprobe.eval.trace_compare import (
    TraceComparisonEvaluator,
    _collect_param_keys,
    _jaccard_similarity,
    _keyword_overlap,
    _levenshtein_distance,
    _levenshtein_similarity,
)
from tests.fixtures.traces import make_llm_call, make_tool_call, make_trace

# ── Helper factories ──


def _trace_with_tools(
    tool_names: list[str],
    output: str = "output",
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> Trace:
    """Build a trace with the given tool names and token counts."""
    calls = [make_tool_call(tool_name=name, tool_input={"arg": "val"}) for name in tool_names]
    llm_calls = [make_llm_call(input_tokens=input_tokens, output_tokens=output_tokens)]
    return make_trace(
        tool_calls=calls,
        llm_calls=llm_calls,
        output_text=output,
    )


def _trace_with_params(
    tools_and_params: list[tuple[str, dict[str, str]]],
    output: str = "output",
) -> Trace:
    """Build a trace with specific tool names and parameter keys."""
    calls = [make_tool_call(tool_name=name, tool_input=params) for name, params in tools_and_params]
    return make_trace(tool_calls=calls, llm_calls=[make_llm_call()], output_text=output)


def _test_case() -> TestCase:
    return TestCase(name="test-compare", input_text="compare these")


# ── Levenshtein distance tests ──


class TestLevenshteinDistance:
    """Tests for _levenshtein_distance."""

    def test_identical_sequences(self) -> None:
        assert _levenshtein_distance(["a", "b", "c"], ["a", "b", "c"]) == 0

    def test_empty_sequences(self) -> None:
        assert _levenshtein_distance([], []) == 0

    def test_one_empty(self) -> None:
        assert _levenshtein_distance(["a", "b"], []) == 2
        assert _levenshtein_distance([], ["x", "y", "z"]) == 3

    def test_single_substitution(self) -> None:
        assert _levenshtein_distance(["a", "b", "c"], ["a", "x", "c"]) == 1

    def test_insertion_and_deletion(self) -> None:
        assert _levenshtein_distance(["a", "b"], ["a", "b", "c"]) == 1
        assert _levenshtein_distance(["a", "b", "c"], ["a", "c"]) == 1

    def test_completely_different(self) -> None:
        assert _levenshtein_distance(["a", "b"], ["x", "y"]) == 2


class TestLevenshteinSimilarity:
    """Tests for _levenshtein_similarity."""

    def test_identical(self) -> None:
        assert _levenshtein_similarity(["a", "b"], ["a", "b"]) == 1.0

    def test_both_empty(self) -> None:
        assert _levenshtein_similarity([], []) == 1.0

    def test_completely_different(self) -> None:
        assert _levenshtein_similarity(["a"], ["b"]) == 0.0

    def test_partial_match(self) -> None:
        sim = _levenshtein_similarity(["a", "b", "c", "d"], ["a", "b", "x", "d"])
        assert sim == pytest.approx(0.75)

    def test_different_lengths(self) -> None:
        sim = _levenshtein_similarity(["a", "b", "c"], ["a", "b"])
        # distance=1, max_len=3 → 1 - 1/3 ≈ 0.6667
        assert sim == pytest.approx(1.0 - 1 / 3, abs=1e-4)


# ── Jaccard similarity tests ──


class TestJaccardSimilarity:
    """Tests for _jaccard_similarity."""

    def test_identical_sets(self) -> None:
        assert _jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0

    def test_both_empty(self) -> None:
        assert _jaccard_similarity(set(), set()) == 1.0

    def test_disjoint_sets(self) -> None:
        assert _jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self) -> None:
        sim = _jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"})
        # intersection=2, union=4 → 0.5
        assert sim == pytest.approx(0.5)

    def test_subset(self) -> None:
        sim = _jaccard_similarity({"a", "b"}, {"a", "b", "c"})
        # intersection=2, union=3 → 0.6667
        assert sim == pytest.approx(2 / 3, abs=1e-4)


# ── Keyword overlap tests ──


class TestKeywordOverlap:
    """Tests for _keyword_overlap."""

    def test_identical_text(self) -> None:
        assert _keyword_overlap("hello world", "hello world") == 1.0

    def test_case_insensitive(self) -> None:
        assert _keyword_overlap("Hello World", "hello world") == 1.0

    def test_partial_overlap(self) -> None:
        sim = _keyword_overlap("the quick brown fox", "the slow brown dog")
        # words_a={the,quick,brown,fox}, words_b={the,slow,brown,dog}
        # intersection={the,brown}=2, union={the,quick,brown,fox,slow,dog}=6
        assert sim == pytest.approx(2 / 6, abs=1e-4)

    def test_no_overlap(self) -> None:
        assert _keyword_overlap("hello world", "foo bar") == 0.0


# ── Collect param keys tests ──


class TestCollectParamKeys:
    """Tests for _collect_param_keys."""

    def test_collects_prefixed_keys(self) -> None:
        trace = _trace_with_params(
            [
                ("search", {"query": "test", "limit": "10"}),
                ("fetch", {"url": "http://example.com"}),
            ]
        )
        keys = _collect_param_keys(trace)
        assert keys == {"search.query", "search.limit", "fetch.url"}

    def test_empty_trace(self) -> None:
        trace = make_trace(tool_calls=[])
        assert _collect_param_keys(trace) == set()

    def test_duplicate_tools_merge_keys(self) -> None:
        trace = _trace_with_params(
            [
                ("search", {"query": "a"}),
                ("search", {"query": "b", "filter": "x"}),
            ]
        )
        keys = _collect_param_keys(trace)
        assert keys == {"search.query", "search.filter"}


# ── TraceComparisonEvaluator tests ──


class TestTraceComparisonEvaluator:
    """Tests for TraceComparisonEvaluator."""

    @pytest.fixture
    def tc(self) -> TestCase:
        return _test_case()

    async def test_identical_traces_score_1(self, tc: TestCase) -> None:
        trace = _trace_with_tools(["search", "fetch"], output="hello world")
        evaluator = TraceComparisonEvaluator(reference_trace=trace)

        result = await evaluator.evaluate(tc, trace)

        assert result.score == pytest.approx(1.0, abs=1e-4)
        assert result.verdict == EvalVerdict.PASS

    async def test_completely_different_traces(self, tc: TestCase) -> None:
        ref = _trace_with_tools(["search", "fetch"], output="hello world", input_tokens=100)
        cur = _trace_with_tools(["write", "delete"], output="foo bar baz", input_tokens=500)
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        assert result.score < 0.5
        assert result.verdict == EvalVerdict.FAIL

    async def test_partial_similarity(self, tc: TestCase) -> None:
        ref = _trace_with_tools(["search", "fetch", "save"], output="the quick brown fox")
        cur = _trace_with_tools(["search", "fetch", "delete"], output="the quick red fox")
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        assert 0.5 < result.score < 1.0
        assert result.verdict in (EvalVerdict.PASS, EvalVerdict.PARTIAL)

    async def test_custom_weights(self, tc: TestCase) -> None:
        ref = _trace_with_tools(["search"], output="hello world")
        cur = _trace_with_tools(["delete"], output="hello world")

        # Weight only output similarity
        weights = {
            "tool_sequence": 0.0,
            "tool_parameters": 0.0,
            "output_similarity": 1.0,
            "cost_deviation": 0.0,
        }
        evaluator = TraceComparisonEvaluator(reference_trace=ref, weights=weights)
        result = await evaluator.evaluate(tc, cur)

        # Output is identical → score should be 1.0
        assert result.score == pytest.approx(1.0, abs=1e-4)

    async def test_custom_pass_threshold(self, tc: TestCase) -> None:
        ref = _trace_with_tools(["search"], output="hello")
        cur = _trace_with_tools(["search"], output="hello")
        evaluator = TraceComparisonEvaluator(reference_trace=ref, pass_threshold=0.99)

        result = await evaluator.evaluate(tc, cur)

        assert result.verdict == EvalVerdict.PASS

    async def test_cost_deviation_zero_ref_zero_cur(self, tc: TestCase) -> None:
        ref = make_trace(
            tool_calls=[make_tool_call(tool_name="search")],
            llm_calls=[make_llm_call(input_tokens=0, output_tokens=0)],
        )
        cur = make_trace(
            tool_calls=[make_tool_call(tool_name="search")],
            llm_calls=[make_llm_call(input_tokens=0, output_tokens=0)],
        )
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        meta = result.metadata
        assert meta is not None
        assert meta["dimension_scores"]["cost_deviation"] == 1.0

    async def test_cost_deviation_zero_ref_nonzero_cur(self, tc: TestCase) -> None:
        ref = make_trace(
            tool_calls=[make_tool_call(tool_name="search")],
            llm_calls=[make_llm_call(input_tokens=0, output_tokens=0)],
        )
        cur = make_trace(
            tool_calls=[make_tool_call(tool_name="search")],
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=50)],
        )
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        meta = result.metadata
        assert meta is not None
        assert meta["dimension_scores"]["cost_deviation"] == 0.0

    async def test_cost_deviation_symmetric(self, tc: TestCase) -> None:
        ref = make_trace(
            tool_calls=[make_tool_call(tool_name="s")],
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=0)],
        )
        cur = make_trace(
            tool_calls=[make_tool_call(tool_name="s")],
            llm_calls=[make_llm_call(input_tokens=200, output_tokens=0)],
        )
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        meta = result.metadata
        assert meta is not None
        # min(100,200)/max(100,200) = 0.5
        assert meta["dimension_scores"]["cost_deviation"] == pytest.approx(0.5)

    async def test_metadata_contains_scores_and_weights(self, tc: TestCase) -> None:
        trace = _trace_with_tools(["search"], output="test")
        evaluator = TraceComparisonEvaluator(reference_trace=trace)

        result = await evaluator.evaluate(tc, trace)

        assert result.metadata is not None
        assert "dimension_scores" in result.metadata
        assert "weights" in result.metadata
        scores = result.metadata["dimension_scores"]
        assert set(scores.keys()) == {
            "tool_sequence",
            "tool_parameters",
            "output_similarity",
            "cost_deviation",
        }

    async def test_reason_contains_formatted_scores(self, tc: TestCase) -> None:
        trace = _trace_with_tools(["search"], output="test")
        evaluator = TraceComparisonEvaluator(reference_trace=trace)

        result = await evaluator.evaluate(tc, trace)

        assert "Trace comparison" in result.reason
        assert "tool_sequence=" in result.reason
        assert "output_similarity=" in result.reason

    async def test_evaluator_name(self) -> None:
        trace = _trace_with_tools(["s"])
        evaluator = TraceComparisonEvaluator(reference_trace=trace, name="custom-compare")
        assert evaluator.name == "custom-compare"

    async def test_default_name(self) -> None:
        trace = _trace_with_tools(["s"])
        evaluator = TraceComparisonEvaluator(reference_trace=trace)
        assert evaluator.name == "trace-compare"

    async def test_empty_tool_calls_both(self, tc: TestCase) -> None:
        ref = make_trace(tool_calls=[], output_text="hello")
        cur = make_trace(tool_calls=[], output_text="hello")
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        meta = result.metadata
        assert meta is not None
        assert meta["dimension_scores"]["tool_sequence"] == 1.0
        assert meta["dimension_scores"]["tool_parameters"] == 1.0

    async def test_partial_verdict_range(self, tc: TestCase) -> None:
        ref = _trace_with_tools(["a", "b", "c"], output="quick brown fox jumps over")
        cur = _trace_with_tools(["a", "x", "y"], output="slow red cat sits under")
        evaluator = TraceComparisonEvaluator(reference_trace=ref, pass_threshold=0.9)

        result = await evaluator.evaluate(tc, cur)

        # Should get partial (between 0.5 and 0.9)
        assert result.verdict in (EvalVerdict.PARTIAL, EvalVerdict.FAIL)

    async def test_score_clamped_between_0_and_1(self, tc: TestCase) -> None:
        ref = _trace_with_tools(["s"], output="test")
        cur = _trace_with_tools(["s"], output="test")
        evaluator = TraceComparisonEvaluator(reference_trace=ref)

        result = await evaluator.evaluate(tc, cur)

        assert 0.0 <= result.score <= 1.0
