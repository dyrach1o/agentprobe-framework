"""Trace replay engine for re-executing recorded traces.

Supports pure replay from recorded data, with optional mock overrides
for tool calls and outputs. Computes a ReplayDiff showing differences
between original and replayed results.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from agentprobe.core.models import DiffItem, ReplayDiff, ToolCall, Trace

logger = logging.getLogger(__name__)


def _tool_call_similarity(a: ToolCall, b: ToolCall) -> float:
    """Compute similarity between two tool calls."""
    score = 0.0
    total = 3.0

    if a.tool_name == b.tool_name:
        score += 1.0
    if a.tool_input == b.tool_input:
        score += 1.0
    if str(a.tool_output) == str(b.tool_output):
        score += 1.0

    return score / total


class ReplayEngine:
    """Replays recorded traces for comparison and testing.

    In pure replay mode, tool calls return their recorded outputs.
    Optional mock functions can override specific tools.

    Attributes:
        mock_tools: Mapping of tool names to mock functions.
        mock_output: If set, override the replay output text.
    """

    def __init__(
        self,
        *,
        mock_tools: dict[str, Callable[..., Any]] | None = None,
        mock_output: str | None = None,
    ) -> None:
        """Initialize the replay engine.

        Args:
            mock_tools: Optional tool name to mock function mapping.
            mock_output: If set, override the output text.
        """
        self._mock_tools = mock_tools or {}
        self._mock_output = mock_output

    def replay(self, trace: Trace) -> Trace:
        """Replay a trace, applying any mock overrides.

        Args:
            trace: The original trace to replay.

        Returns:
            A new trace with mock overrides applied.
        """
        if not self._mock_tools and self._mock_output is None:
            return trace

        modified_calls: list[ToolCall] = []
        for tc in trace.tool_calls:
            mock_fn = self._mock_tools.get(tc.tool_name)
            if mock_fn is not None:
                try:
                    mock_result = mock_fn(tc.tool_input)
                    modified_calls.append(tc.model_copy(update={"tool_output": mock_result}))
                except Exception as exc:
                    modified_calls.append(
                        tc.model_copy(
                            update={
                                "success": False,
                                "error": f"Mock error: {exc}",
                                "tool_output": None,
                            }
                        )
                    )
            else:
                modified_calls.append(tc)

        output = self._mock_output if self._mock_output is not None else trace.output_text

        return trace.model_copy(
            update={
                "tool_calls": tuple(modified_calls),
                "output_text": output,
            },
        )

    def diff(self, original: Trace, replay: Trace) -> ReplayDiff:
        """Compute the diff between an original trace and a replay.

        Args:
            original: The original trace.
            replay: The replayed trace.

        Returns:
            A ReplayDiff showing the differences.
        """
        tool_diffs: list[DiffItem] = []

        max_len = max(len(original.tool_calls), len(replay.tool_calls))
        for i in range(max_len):
            if i < len(original.tool_calls) and i < len(replay.tool_calls):
                orig_tc = original.tool_calls[i]
                replay_tc = replay.tool_calls[i]
                sim = _tool_call_similarity(orig_tc, replay_tc)
                tool_diffs.append(
                    DiffItem(
                        dimension=f"tool_call_{i}",
                        expected=orig_tc.tool_name,
                        actual=replay_tc.tool_name,
                        similarity=round(sim, 4),
                    )
                )
            elif i < len(original.tool_calls):
                tool_diffs.append(
                    DiffItem(
                        dimension=f"tool_call_{i}",
                        expected=original.tool_calls[i].tool_name,
                        actual=None,
                        similarity=0.0,
                    )
                )
            else:
                tool_diffs.append(
                    DiffItem(
                        dimension=f"tool_call_{i}",
                        expected=None,
                        actual=replay.tool_calls[i].tool_name,
                        similarity=0.0,
                    )
                )

        output_matches = original.output_text == replay.output_text

        return ReplayDiff(
            original_trace_id=original.trace_id,
            replay_trace_id=replay.trace_id,
            tool_call_diffs=tuple(tool_diffs),
            output_matches=output_matches,
            original_output=original.output_text,
            replay_output=replay.output_text,
        )
