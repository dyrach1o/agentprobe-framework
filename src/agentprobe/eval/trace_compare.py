"""Trace comparison evaluator with weighted multi-dimension scoring.

Compares two traces across tool sequences, tool parameters, output
similarity, and cost deviation, producing a weighted composite score.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace
from agentprobe.eval.base import BaseEvaluator

logger = logging.getLogger(__name__)


def _levenshtein_distance(a: list[str], b: list[str]) -> int:
    """Compute Levenshtein edit distance between two string sequences."""
    m, n = len(a), len(b)
    dp = list(range(n + 1))

    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp

    return dp[n]


def _levenshtein_similarity(a: list[str], b: list[str]) -> float:
    """Compute normalized Levenshtein similarity (0.0 to 1.0)."""
    if not a and not b:
        return 1.0
    max_len = max(len(a), len(b))
    dist = _levenshtein_distance(a, b)
    return 1.0 - (dist / max_len)


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union)


def _keyword_overlap(a: str, b: str) -> float:
    """Compute word-level Jaccard similarity."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    return _jaccard_similarity(words_a, words_b)


class TraceComparisonEvaluator(BaseEvaluator):
    """Evaluator that compares a trace against a reference trace.

    Computes similarity across multiple dimensions with configurable
    weights: tool sequence, tool parameters, output text, and cost.

    Attributes:
        reference_trace: The reference trace to compare against.
        weights: Per-dimension weight configuration.
    """

    DEFAULT_WEIGHTS: ClassVar[dict[str, float]] = {
        "tool_sequence": 0.3,
        "tool_parameters": 0.2,
        "output_similarity": 0.35,
        "cost_deviation": 0.15,
    }

    def __init__(
        self,
        reference_trace: Trace,
        *,
        name: str = "trace-compare",
        weights: dict[str, float] | None = None,
        pass_threshold: float = 0.7,
    ) -> None:
        """Initialize the trace comparison evaluator.

        Args:
            reference_trace: The baseline trace to compare against.
            name: Evaluator name.
            weights: Dimension weight overrides.
            pass_threshold: Minimum score for a pass verdict.
        """
        super().__init__(name)
        self._reference = reference_trace
        self._weights = weights or dict(self.DEFAULT_WEIGHTS)
        self._pass_threshold = pass_threshold

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Compare the trace against the reference.

        Args:
            test_case: The test case (used for context).
            trace: The current trace to compare.

        Returns:
            An evaluation result with the composite similarity score.
        """
        scores: dict[str, float] = {}

        # Tool sequence similarity (Levenshtein)
        ref_tools = [tc.tool_name for tc in self._reference.tool_calls]
        cur_tools = [tc.tool_name for tc in trace.tool_calls]
        scores["tool_sequence"] = _levenshtein_similarity(ref_tools, cur_tools)

        # Tool parameter similarity (Jaccard on parameter keys)
        ref_params = _collect_param_keys(self._reference)
        cur_params = _collect_param_keys(trace)
        scores["tool_parameters"] = _jaccard_similarity(ref_params, cur_params)

        # Output text similarity (word-level Jaccard)
        scores["output_similarity"] = _keyword_overlap(
            self._reference.output_text, trace.output_text
        )

        # Cost deviation
        ref_tokens = self._reference.total_input_tokens + self._reference.total_output_tokens
        cur_tokens = trace.total_input_tokens + trace.total_output_tokens
        if ref_tokens > 0:
            cost_ratio = min(cur_tokens, ref_tokens) / max(cur_tokens, ref_tokens)
        elif cur_tokens == 0:
            cost_ratio = 1.0
        else:
            cost_ratio = 0.0
        scores["cost_deviation"] = cost_ratio

        # Weighted composite
        total_weight = sum(self._weights.get(k, 0.0) for k in scores)
        composite = sum(scores[k] * self._weights.get(k, 0.0) for k in scores)
        final_score = composite / total_weight if total_weight > 0 else 0.0
        final_score = round(min(max(final_score, 0.0), 1.0), 4)

        _partial_threshold = 0.5
        if final_score >= self._pass_threshold:
            verdict = EvalVerdict.PASS
        elif final_score >= _partial_threshold:
            verdict = EvalVerdict.PARTIAL
        else:
            verdict = EvalVerdict.FAIL

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=final_score,
            reason=f"Trace comparison: {final_score:.3f} ({_format_scores(scores)})",
            metadata={"dimension_scores": scores, "weights": self._weights},
        )


def _collect_param_keys(trace: Trace) -> set[str]:
    """Collect all tool parameter keys from a trace."""
    keys: set[str] = set()
    for tc in trace.tool_calls:
        keys.update(f"{tc.tool_name}.{k}" for k in tc.tool_input)
    return keys


def _format_scores(scores: dict[str, float]) -> str:
    """Format dimension scores for display."""
    parts = [f"{k}={v:.2f}" for k, v in scores.items()]
    return ", ".join(parts)
