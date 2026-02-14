"""Tests for the TraceRecorder."""

from __future__ import annotations

import pytest

from agentprobe.core.exceptions import TraceError
from agentprobe.core.models import TurnType
from agentprobe.trace.recorder import TraceRecorder


class TestTraceRecorder:
    """Tests for TraceRecorder functionality."""

    def test_empty_agent_name_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_name"):
            TraceRecorder(agent_name="")

    @pytest.mark.asyncio
    async def test_basic_recording(self) -> None:
        recorder = TraceRecorder(agent_name="test-agent", model="test-model")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(
                model="test-model",
                input_tokens=100,
                output_tokens=50,
                input_text="hello",
                output_text="world",
            )

        trace = recorder.finalize(input_text="hello", output="world")
        assert trace.agent_name == "test-agent"
        assert trace.model == "test-model"
        assert len(trace.llm_calls) == 1
        assert trace.total_input_tokens == 100
        assert trace.total_output_tokens == 50
        assert trace.input_text == "hello"
        assert trace.output_text == "world"

    @pytest.mark.asyncio
    async def test_record_tool_call(self) -> None:
        recorder = TraceRecorder(agent_name="test-agent")
        async with recorder.recording() as ctx:
            ctx.record_tool_call(
                tool_name="search",
                tool_input={"query": "test"},
                tool_output="found it",
            )

        trace = recorder.finalize()
        assert len(trace.tool_calls) == 1
        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[0].tool_output == "found it"

    @pytest.mark.asyncio
    async def test_mixed_events(self) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="m1", input_tokens=10, output_tokens=5)
            ctx.record_tool_call(tool_name="search")
            ctx.record_llm_call(model="m1", input_tokens=20, output_tokens=10)

        trace = recorder.finalize()
        assert len(trace.turns) == 3
        assert trace.turns[0].turn_type == TurnType.LLM_CALL
        assert trace.turns[1].turn_type == TurnType.TOOL_CALL
        assert trace.turns[2].turn_type == TurnType.LLM_CALL
        assert trace.total_input_tokens == 30
        assert trace.total_output_tokens == 15

    @pytest.mark.asyncio
    async def test_model_inferred_from_first_call(self) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="auto-detected")

        trace = recorder.finalize()
        assert trace.model == "auto-detected"

    @pytest.mark.asyncio
    async def test_tags_preserved(self) -> None:
        recorder = TraceRecorder(agent_name="agent", tags=["smoke", "fast"])
        async with recorder.recording():
            pass

        trace = recorder.finalize()
        assert "smoke" in trace.tags
        assert "fast" in trace.tags

    def test_finalize_without_recording_raises(self) -> None:
        recorder = TraceRecorder(agent_name="agent")
        with pytest.raises(TraceError, match="No recording session"):
            recorder.finalize()

    @pytest.mark.asyncio
    async def test_finalize_clears_context(self) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording():
            pass

        recorder.finalize()

        with pytest.raises(TraceError):
            recorder.finalize()

    @pytest.mark.asyncio
    async def test_recording_context_elapsed_ms(self) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording() as ctx:
            assert ctx.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_exception_during_recording_propagates(self) -> None:
        recorder = TraceRecorder(agent_name="agent")
        with pytest.raises(RuntimeError, match="test error"):
            async with recorder.recording():
                msg = "test error"
                raise RuntimeError(msg)


class TestTraceRecorderParametrized:
    """Parametrized tests for recording various event counts."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("num_llm_calls", [1, 3, 5])
    async def test_llm_call_counts(self, num_llm_calls: int) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording() as ctx:
            for i in range(num_llm_calls):
                ctx.record_llm_call(
                    model="test-model",
                    input_tokens=10 * (i + 1),
                    output_tokens=5 * (i + 1),
                )

        trace = recorder.finalize()
        assert len(trace.llm_calls) == num_llm_calls
        expected_input = sum(10 * (i + 1) for i in range(num_llm_calls))
        expected_output = sum(5 * (i + 1) for i in range(num_llm_calls))
        assert trace.total_input_tokens == expected_input
        assert trace.total_output_tokens == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize("num_tool_calls", [0, 1, 4])
    async def test_tool_call_counts(self, num_tool_calls: int) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording() as ctx:
            for i in range(num_tool_calls):
                ctx.record_tool_call(tool_name=f"tool_{i}")

        trace = recorder.finalize()
        assert len(trace.tool_calls) == num_tool_calls

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "num_llm,num_tool,expected_turns",
        [
            (0, 0, 0),
            (1, 0, 1),
            (0, 1, 1),
            (2, 3, 5),
        ],
    )
    async def test_mixed_event_counts(
        self, num_llm: int, num_tool: int, expected_turns: int
    ) -> None:
        recorder = TraceRecorder(agent_name="agent")
        async with recorder.recording() as ctx:
            for _ in range(num_llm):
                ctx.record_llm_call(model="m")
            for _ in range(num_tool):
                ctx.record_tool_call(tool_name="t")

        trace = recorder.finalize()
        assert len(trace.turns) == expected_turns
