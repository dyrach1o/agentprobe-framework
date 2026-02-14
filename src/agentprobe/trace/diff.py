"""Structural diffing between any two traces.

Compares output text, tool call sequences, model usage, token counts,
and latency. Independent from ReplayEngine — works on arbitrary trace pairs.
"""

from __future__ import annotations

import logging

from agentprobe.core.models import DiffItem, ToolCall, Trace, TraceDiffReport

logger = logging.getLogger(__name__)


def _tool_similarity(a: ToolCall, b: ToolCall) -> float:
    """Compute similarity between two tool calls (0.0-1.0)."""
    score = 0.0
    total = 3.0

    if a.tool_name == b.tool_name:
        score += 1.0
    if a.tool_input == b.tool_input:
        score += 1.0
    if str(a.tool_output) == str(b.tool_output):
        score += 1.0

    return score / total


class TraceDiffer:
    """Compares two Trace objects across multiple dimensions.

    Produces a TraceDiffReport with per-tool-call diffs, token/latency
    deltas, output match status, and an overall similarity score.

    Attributes:
        similarity_threshold: Minimum overall similarity for a match.
    """

    def __init__(self, *, similarity_threshold: float = 0.8) -> None:
        """Initialize the trace differ.

        Args:
            similarity_threshold: Threshold for overall_similarity to
                be considered a match.
        """
        self._threshold = similarity_threshold

    def diff(self, trace_a: Trace, trace_b: Trace) -> TraceDiffReport:
        """Compare two traces and produce a diff report.

        Args:
            trace_a: The first (baseline) trace.
            trace_b: The second (comparison) trace.

        Returns:
            A TraceDiffReport summarising the differences.
        """
        tool_diffs = self._diff_tool_calls(trace_a, trace_b)
        output_matches = trace_a.output_text == trace_b.output_text

        total_tokens_a = trace_a.total_input_tokens + trace_a.total_output_tokens
        total_tokens_b = trace_b.total_input_tokens + trace_b.total_output_tokens
        token_delta = total_tokens_b - total_tokens_a
        latency_delta = trace_b.total_latency_ms - trace_a.total_latency_ms

        overall = self._compute_overall_similarity(
            tool_diffs=tool_diffs,
            output_matches=output_matches,
        )

        return TraceDiffReport(
            trace_a_id=trace_a.trace_id,
            trace_b_id=trace_b.trace_id,
            tool_call_diffs=tuple(tool_diffs),
            output_matches=output_matches,
            token_delta=token_delta,
            latency_delta_ms=latency_delta,
            overall_similarity=round(overall, 4),
        )

    def _diff_tool_calls(self, a: Trace, b: Trace) -> list[DiffItem]:
        """Produce per-index tool call diffs."""
        diffs: list[DiffItem] = []
        max_len = max(len(a.tool_calls), len(b.tool_calls))

        for i in range(max_len):
            if i < len(a.tool_calls) and i < len(b.tool_calls):
                sim = _tool_similarity(a.tool_calls[i], b.tool_calls[i])
                diffs.append(
                    DiffItem(
                        dimension=f"tool_call_{i}",
                        expected=a.tool_calls[i].tool_name,
                        actual=b.tool_calls[i].tool_name,
                        similarity=round(sim, 4),
                    )
                )
            elif i < len(a.tool_calls):
                diffs.append(
                    DiffItem(
                        dimension=f"tool_call_{i}",
                        expected=a.tool_calls[i].tool_name,
                        actual=None,
                        similarity=0.0,
                    )
                )
            else:
                diffs.append(
                    DiffItem(
                        dimension=f"tool_call_{i}",
                        expected=None,
                        actual=b.tool_calls[i].tool_name,
                        similarity=0.0,
                    )
                )

        return diffs

    @staticmethod
    def _compute_overall_similarity(
        *,
        tool_diffs: list[DiffItem],
        output_matches: bool,
    ) -> float:
        """Weighted average of output match and tool call similarities."""
        output_score = 1.0 if output_matches else 0.0

        if not tool_diffs:
            return output_score

        tool_score = sum(d.similarity for d in tool_diffs) / len(tool_diffs)

        # Weight: output 40%, tools 60%
        return 0.4 * output_score + 0.6 * tool_score
