"""Integration test: TraceRecorder → SQLiteStorage → load → ReplayEngine → TimeTravel."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.storage.sqlite import SQLiteStorage
from agentprobe.trace.recorder import TraceRecorder
from agentprobe.trace.replay import ReplayEngine
from agentprobe.trace.time_travel import TimeTravel


@pytest.mark.integration
class TestTracePipeline:
    """End-to-end: record, store, load, replay, time-travel."""

    @pytest.mark.asyncio
    async def test_record_store_load_roundtrip(self, tmp_path: Path) -> None:
        """Record a trace, persist it, and load it back losslessly."""
        recorder = TraceRecorder(agent_name="trace-test", model="test-model", tags=["integration"])
        async with recorder.recording() as ctx:
            ctx.record_llm_call(
                model="test-model",
                input_tokens=100,
                output_tokens=50,
                input_text="Hello",
                output_text="Hi there!",
                latency_ms=150,
            )
            ctx.record_tool_call(
                tool_name="search",
                tool_input={"query": "news"},
                tool_output="Breaking: ...",
                latency_ms=80,
            )
        trace = recorder.finalize(input_text="Hello", output="Hi there!")

        # Persist
        storage = SQLiteStorage(db_path=tmp_path / "traces.db")
        await storage.setup()
        await storage.save_trace(trace)

        # Load back
        loaded = await storage.load_trace(trace.trace_id)
        assert loaded is not None
        assert loaded.trace_id == trace.trace_id
        assert loaded.agent_name == "trace-test"
        assert loaded.total_input_tokens == 100
        assert loaded.total_output_tokens == 50
        assert len(loaded.llm_calls) == 1
        assert len(loaded.tool_calls) == 1
        assert "integration" in loaded.tags

        await storage.close()

    @pytest.mark.asyncio
    async def test_record_and_replay_with_mock(self, tmp_path: Path) -> None:
        """Record a trace, store it, reload, then replay with mock tools."""
        recorder = TraceRecorder(agent_name="replay-test")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="test-model", input_tokens=50, output_tokens=25)
            ctx.record_tool_call(
                tool_name="calculator",
                tool_input={"expr": "2+2"},
                tool_output="4",
            )
        trace = recorder.finalize(input_text="Calculate", output="4")

        storage = SQLiteStorage(db_path=tmp_path / "replay.db")
        await storage.setup()
        await storage.save_trace(trace)
        loaded = await storage.load_trace(trace.trace_id)
        assert loaded is not None

        # Replay with a mock tool override
        engine = ReplayEngine(
            mock_tools={"calculator": lambda inp: "overridden_result"},
            mock_output="overridden output",
        )
        replayed = engine.replay(loaded)

        assert replayed.output_text == "overridden output"
        assert replayed.tool_calls[0].tool_output == "overridden_result"

        # Diff
        diff = engine.diff(loaded, replayed)
        assert not diff.output_matches
        assert diff.original_output == "4"
        assert diff.replay_output == "overridden output"

        await storage.close()

    @pytest.mark.asyncio
    async def test_record_and_time_travel(self) -> None:
        """Record a multi-step trace and navigate with TimeTravel."""
        recorder = TraceRecorder(agent_name="tt-test", model="test-model")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(
                model="test-model",
                input_tokens=100,
                output_tokens=50,
                latency_ms=100,
            )
            ctx.record_tool_call(
                tool_name="search",
                tool_input={"q": "test"},
                tool_output="found",
                latency_ms=50,
            )
            ctx.record_llm_call(
                model="test-model",
                input_tokens=80,
                output_tokens=40,
                latency_ms=90,
            )
        trace = recorder.finalize(input_text="multi-step", output="done")

        tt = TimeTravel(trace, cost_per_1k_input=0.003, cost_per_1k_output=0.015)

        assert tt.total_steps == 3
        assert len(tt) == 3

        # Step 0: first LLM call
        step0 = tt[0]
        assert step0.step_index == 0
        assert step0.cumulative_input_tokens == 100
        assert step0.cumulative_latency_ms == 100

        # Step 2: cumulative includes all steps
        step2 = tt[2]
        assert step2.cumulative_input_tokens == 180
        assert step2.cumulative_latency_ms == 240

        # rerun_from
        remaining = tt.rerun_from(1)
        assert len(remaining) == 2

    @pytest.mark.asyncio
    async def test_list_traces_by_agent(self, tmp_path: Path) -> None:
        """Store multiple traces, list and filter by agent name."""
        storage = SQLiteStorage(db_path=tmp_path / "list.db")
        await storage.setup()

        for agent in ["agent-a", "agent-a", "agent-b"]:
            recorder = TraceRecorder(agent_name=agent)
            async with recorder.recording() as ctx:
                ctx.record_llm_call(model="m", input_tokens=10, output_tokens=5)
            trace = recorder.finalize(input_text="x", output="y")
            await storage.save_trace(trace)

        all_traces = await storage.list_traces()
        assert len(all_traces) == 3

        agent_a_traces = await storage.list_traces(agent_name="agent-a")
        assert len(agent_a_traces) == 2

        agent_b_traces = await storage.list_traces(agent_name="agent-b")
        assert len(agent_b_traces) == 1

        await storage.close()
