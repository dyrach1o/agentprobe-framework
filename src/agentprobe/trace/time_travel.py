"""Time-travel debugger for step-by-step trace inspection.

Provides indexed access to individual turns in a trace with
cumulative metrics at each step, enabling debugging and analysis
of agent execution flow.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from agentprobe.core.models import Trace, TraceStep, TurnType

logger = logging.getLogger(__name__)


class TimeTravel:
    """Step-by-step trace inspector with cumulative metrics.

    Pre-computes a list of TraceStep objects on construction,
    providing indexed access and iteration over the trace timeline
    with cumulative token, cost, and latency metrics at each step.

    Attributes:
        trace: The trace being inspected.
    """

    def __init__(
        self, trace: Trace, *, cost_per_1k_input: float = 0.0, cost_per_1k_output: float = 0.0
    ) -> None:
        """Initialize the time-travel debugger.

        Args:
            trace: The trace to inspect.
            cost_per_1k_input: Cost per 1K input tokens for cumulative cost.
            cost_per_1k_output: Cost per 1K output tokens for cumulative cost.
        """
        self._trace = trace
        self._steps = self._build_steps(trace, cost_per_1k_input, cost_per_1k_output)

    @property
    def trace(self) -> Trace:
        """Return the underlying trace."""
        return self._trace

    @property
    def total_steps(self) -> int:
        """Return the total number of steps."""
        return len(self._steps)

    @staticmethod
    def _build_steps(
        trace: Trace,
        cost_per_1k_input: float,
        cost_per_1k_output: float,
    ) -> list[TraceStep]:
        """Build the list of trace steps with cumulative metrics."""
        steps: list[TraceStep] = []
        cum_input = 0
        cum_output = 0
        cum_cost = 0.0
        cum_latency = 0

        for i, turn in enumerate(trace.turns):
            if turn.turn_type == TurnType.LLM_CALL and turn.llm_call is not None:
                cum_input += turn.llm_call.input_tokens
                cum_output += turn.llm_call.output_tokens
                cum_cost += (
                    turn.llm_call.input_tokens / 1000.0 * cost_per_1k_input
                    + turn.llm_call.output_tokens / 1000.0 * cost_per_1k_output
                )
                cum_latency += turn.llm_call.latency_ms
            elif turn.turn_type == TurnType.TOOL_CALL and turn.tool_call is not None:
                cum_latency += turn.tool_call.latency_ms

            steps.append(
                TraceStep(
                    step_index=i,
                    turn=turn,
                    cumulative_input_tokens=cum_input,
                    cumulative_output_tokens=cum_output,
                    cumulative_cost_usd=round(cum_cost, 6),
                    cumulative_latency_ms=cum_latency,
                )
            )

        return steps

    def __len__(self) -> int:
        return len(self._steps)

    def __getitem__(self, index: int) -> TraceStep:
        """Get a step by index.

        Args:
            index: Zero-based step index. Supports negative indexing.

        Returns:
            The TraceStep at the given index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self._steps[index]

    def __iter__(self) -> Iterator[TraceStep]:
        return iter(self._steps)

    def steps(self) -> list[TraceStep]:
        """Return all steps as a list."""
        return list(self._steps)

    def rerun_from(self, step_index: int) -> list[TraceStep]:
        """Return all steps from a given index onward.

        Args:
            step_index: Zero-based starting index.

        Returns:
            Steps from the given index to the end.

        Raises:
            IndexError: If step_index is out of range.
        """
        if step_index < 0 or step_index >= len(self._steps):
            raise IndexError(f"Step index {step_index} out of range [0, {len(self._steps)})")
        return list(self._steps[step_index:])
