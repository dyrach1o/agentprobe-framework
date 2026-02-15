"""Tests for the pytest plugin module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.config import AgentProbeConfig
from agentprobe.core.models import (
    CostSummary,
    EvalResult,
    EvalVerdict,
    LLMCall,
    Trace,
)
from agentprobe.eval.base import BaseEvaluator
from agentprobe.pytest_plugin import AgentProbeContext, pytest_addoption, pytest_configure
from agentprobe.storage.sqlite import SQLiteStorage


def _make_trace(output_text: str = "test output") -> Trace:
    """Create a minimal trace for testing."""
    return Trace(agent_name="test-agent", output_text=output_text)


class TestPytestAddoption:
    """Tests for pytest_addoption hook."""

    def test_registers_options(self) -> None:
        parser = MagicMock(spec=pytest.Parser)
        group = MagicMock()
        parser.getgroup.return_value = group

        pytest_addoption(parser)

        parser.getgroup.assert_called_once_with("agentprobe", "AgentProbe agent testing")
        assert group.addoption.call_count == 4

        option_names = [call.args[0] for call in group.addoption.call_args_list]
        assert "--agentprobe-config" in option_names
        assert "--agentprobe-trace-dir" in option_names
        assert "--agentprobe-store-traces" in option_names
        assert "--agentprobe-parallel" in option_names


class TestPytestConfigure:
    """Tests for pytest_configure hook."""

    def test_registers_marker(self) -> None:
        config = MagicMock(spec=pytest.Config)
        pytest_configure(config)
        config.addinivalue_line.assert_called_once_with(
            "markers",
            "agentprobe: marks tests using the AgentProbe framework",
        )


class TestAgentProbeContext:
    """Tests for the AgentProbeContext class."""

    def _make_context(
        self,
        storage: SQLiteStorage | None = None,
        store_traces: bool = False,
    ) -> AgentProbeContext:
        config = AgentProbeConfig()
        return AgentProbeContext(
            config=config,
            storage=storage,
            store_traces=store_traces,
        )

    def test_config_property(self) -> None:
        ctx = self._make_context()
        assert isinstance(ctx.config, AgentProbeConfig)

    def test_traces_starts_empty(self) -> None:
        ctx = self._make_context()
        assert ctx.traces == []

    def test_last_trace_raises_when_empty(self) -> None:
        ctx = self._make_context()
        with pytest.raises(ValueError, match="No traces collected"):
            _ = ctx.last_trace

    async def test_invoke_collects_trace(self) -> None:
        ctx = self._make_context()
        trace = _make_trace()

        adapter = AsyncMock(spec=BaseAdapter)
        adapter.invoke = AsyncMock(return_value=trace)

        result = await ctx.invoke("hello", adapter=adapter)

        assert result is trace
        assert len(ctx.traces) == 1
        assert ctx.last_trace is trace
        adapter.invoke.assert_awaited_once_with("hello")

    async def test_invoke_stores_trace_when_enabled(self, tmp_path: Any) -> None:
        storage = SQLiteStorage(db_path=tmp_path / "test.db")
        await storage.setup()

        ctx = self._make_context(storage=storage, store_traces=True)
        trace = _make_trace()

        adapter = AsyncMock(spec=BaseAdapter)
        adapter.invoke = AsyncMock(return_value=trace)

        await ctx.invoke("hello", adapter=adapter)

        loaded = await storage.load_trace(trace.trace_id)
        assert loaded is not None
        assert loaded.trace_id == trace.trace_id

        await storage.close()

    async def test_invoke_does_not_store_when_disabled(self) -> None:
        storage = AsyncMock(spec=SQLiteStorage)
        ctx = self._make_context(storage=storage, store_traces=False)
        trace = _make_trace()

        adapter = AsyncMock(spec=BaseAdapter)
        adapter.invoke = AsyncMock(return_value=trace)

        await ctx.invoke("hello", adapter=adapter)

        storage.save_trace.assert_not_awaited()

    async def test_evaluate_runs_evaluator(self) -> None:
        ctx = self._make_context()
        trace = _make_trace()

        evaluator = AsyncMock(spec=BaseEvaluator)
        evaluator.name = "mock-eval"
        evaluator.evaluate = AsyncMock(
            return_value=EvalResult(
                evaluator_name="mock-eval",
                verdict=EvalVerdict.PASS,
                score=0.95,
            )
        )

        result = await ctx.evaluate(trace, evaluator, input_text="test input")

        assert isinstance(result, EvalResult)
        assert result.score == 0.95
        evaluator.evaluate.assert_awaited_once()

    def test_calculate_cost_returns_summary(self) -> None:
        ctx = self._make_context()
        call = LLMCall(model="unknown-model", input_tokens=100, output_tokens=50)
        trace = Trace(agent_name="test", llm_calls=(call,))

        result = ctx.calculate_cost(trace)
        assert isinstance(result, CostSummary)

    def test_calculate_cost_reuses_calculator(self) -> None:
        ctx = self._make_context()
        trace = _make_trace()

        ctx.calculate_cost(trace)
        first_calc = ctx._calculator

        ctx.calculate_cost(trace)
        assert ctx._calculator is first_calc

    async def test_multiple_invocations_accumulate_traces(self) -> None:
        ctx = self._make_context()

        adapter = AsyncMock(spec=BaseAdapter)
        trace1 = _make_trace(output_text="first")
        trace2 = _make_trace(output_text="second")
        adapter.invoke = AsyncMock(side_effect=[trace1, trace2])

        await ctx.invoke("one", adapter=adapter)
        await ctx.invoke("two", adapter=adapter)

        assert len(ctx.traces) == 2
        assert ctx.last_trace.output_text == "second"

    def test_traces_returns_copy(self) -> None:
        ctx = self._make_context()
        traces_ref = ctx.traces
        traces_ref.append(_make_trace())
        assert len(ctx.traces) == 0
