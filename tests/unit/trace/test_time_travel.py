"""Tests for the time-travel debugger."""

from __future__ import annotations

import pytest

from agentprobe.core.models import TurnType
from agentprobe.trace.time_travel import TimeTravel
from tests.fixtures.traces import make_llm_call, make_tool_call, make_trace, make_turn


class TestTimeTravel:
    """Test TimeTravel step-by-step inspection."""

    @pytest.fixture
    def trace_with_turns(self) -> object:
        llm = make_llm_call(input_tokens=100, output_tokens=50, latency_ms=200)
        tool = make_tool_call(tool_name="search", latency_ms=50)
        turns = [
            make_turn(turn_type=TurnType.LLM_CALL, llm_call=llm),
            make_turn(turn_type=TurnType.TOOL_CALL, tool_call=tool),
            make_turn(
                turn_type=TurnType.LLM_CALL,
                llm_call=make_llm_call(
                    input_tokens=80,
                    output_tokens=30,
                    latency_ms=150,
                ),
            ),
        ]
        return make_trace(turns=turns, llm_calls=[llm], tool_calls=[tool])

    def test_total_steps(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        assert tt.total_steps == 3
        assert len(tt) == 3

    def test_index_access(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)

        step0 = tt[0]
        assert step0.step_index == 0
        assert step0.turn.turn_type == TurnType.LLM_CALL

        step1 = tt[1]
        assert step1.step_index == 1
        assert step1.turn.turn_type == TurnType.TOOL_CALL

    def test_negative_index(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        last = tt[-1]
        assert last.step_index == 2

    def test_index_out_of_range(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        with pytest.raises(IndexError):
            _ = tt[10]

    def test_cumulative_tokens(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)

        # After first LLM call
        assert tt[0].cumulative_input_tokens == 100
        assert tt[0].cumulative_output_tokens == 50

        # After tool call (no token change)
        assert tt[1].cumulative_input_tokens == 100
        assert tt[1].cumulative_output_tokens == 50

        # After second LLM call
        assert tt[2].cumulative_input_tokens == 180
        assert tt[2].cumulative_output_tokens == 80

    def test_cumulative_latency(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)

        assert tt[0].cumulative_latency_ms == 200
        assert tt[1].cumulative_latency_ms == 250  # +50 from tool
        assert tt[2].cumulative_latency_ms == 400  # +150 from second LLM

    def test_cumulative_cost(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns, cost_per_1k_input=3.0, cost_per_1k_output=15.0)

        # First step: 100/1000 * 3.0 + 50/1000 * 15.0 = 0.3 + 0.75 = 1.05
        assert abs(tt[0].cumulative_cost_usd - 1.05) < 0.001

    def test_iteration(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        indices = [step.step_index for step in tt]
        assert indices == [0, 1, 2]

    def test_steps_method(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        all_steps = tt.steps()
        assert len(all_steps) == 3
        assert all_steps[0].step_index == 0

    def test_rerun_from(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        remaining = tt.rerun_from(1)
        assert len(remaining) == 2
        assert remaining[0].step_index == 1
        assert remaining[1].step_index == 2

    def test_rerun_from_start(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        all_from_start = tt.rerun_from(0)
        assert len(all_from_start) == 3

    def test_rerun_from_invalid_index(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        with pytest.raises(IndexError, match="out of range"):
            tt.rerun_from(10)

        with pytest.raises(IndexError, match="out of range"):
            tt.rerun_from(-1)

    def test_empty_trace(self) -> None:
        trace = make_trace(turns=[])
        tt = TimeTravel(trace)
        assert tt.total_steps == 0
        assert list(tt) == []

    def test_trace_property(self, trace_with_turns: object) -> None:
        from agentprobe.core.models import Trace

        assert isinstance(trace_with_turns, Trace)
        tt = TimeTravel(trace_with_turns)
        assert tt.trace is trace_with_turns
