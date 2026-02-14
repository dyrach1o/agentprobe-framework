"""Tests for the chaos fault injection proxy."""

from __future__ import annotations

import pytest

from agentprobe.core.chaos import ChaosProxy
from agentprobe.core.models import ChaosOverride, ChaosType
from tests.fixtures.agents import MockAdapter
from tests.fixtures.traces import make_tool_call


class TestChaosProxy:
    """Test ChaosProxy fault injection."""

    @pytest.fixture
    def adapter(self) -> MockAdapter:
        return MockAdapter(
            output="result",
            tool_calls=[
                make_tool_call(tool_name="search", tool_output="found it"),
                make_tool_call(tool_name="calc", tool_output="42"),
            ],
        )

    async def test_passthrough_no_overrides(self, adapter: MockAdapter) -> None:
        proxy = ChaosProxy(adapter, overrides=[])
        trace = await proxy.invoke("test")
        assert trace.output_text == "result"
        assert all(tc.success for tc in trace.tool_calls)

    async def test_name(self, adapter: MockAdapter) -> None:
        proxy = ChaosProxy(adapter, overrides=[])
        assert proxy.name == "chaos-mock"

    async def test_timeout_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.TIMEOUT, probability=1.0)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is False
            assert "timed out" in (tc.error or "")

    async def test_error_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(
            chaos_type=ChaosType.ERROR,
            probability=1.0,
            error_message="service unavailable",
        )
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is False
            assert "service unavailable" in (tc.error or "")

    async def test_malformed_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.MALFORMED, probability=1.0)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is True
            assert "malformed" in str(tc.tool_output).lower()

    async def test_rate_limit_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.RATE_LIMIT, probability=1.0)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is False
            assert "429" in (tc.error or "")

    async def test_slow_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.SLOW, probability=1.0, delay_ms=3000)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is True
            assert tc.latency_ms >= 3000

    async def test_empty_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.EMPTY, probability=1.0)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is True
            assert tc.tool_output == ""

    async def test_probability_zero_no_fault(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.ERROR, probability=0.0)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        for tc in trace.tool_calls:
            assert tc.success is True

    async def test_targeted_tool(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(
            chaos_type=ChaosType.ERROR,
            probability=1.0,
            target_tool="search",
        )
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        # search should be faulted, calc should not
        search_calls = [tc for tc in trace.tool_calls if tc.tool_name == "search"]
        calc_calls = [tc for tc in trace.tool_calls if tc.tool_name == "calc"]
        assert all(not tc.success for tc in search_calls)
        assert all(tc.success for tc in calc_calls)

    async def test_deterministic_with_seed(self, adapter: MockAdapter) -> None:
        override = ChaosOverride(chaos_type=ChaosType.ERROR, probability=0.5)
        proxy1 = ChaosProxy(adapter, overrides=[override], seed=123)
        trace1 = await proxy1.invoke("test")

        proxy2 = ChaosProxy(adapter, overrides=[override], seed=123)
        trace2 = await proxy2.invoke("test")

        # Same seed should produce same fault pattern
        for tc1, tc2 in zip(trace1.tool_calls, trace2.tool_calls, strict=True):
            assert tc1.success == tc2.success

    async def test_no_tool_calls_passthrough(self) -> None:
        adapter = MockAdapter(output="no tools", tool_calls=[])
        override = ChaosOverride(chaos_type=ChaosType.ERROR, probability=1.0)
        proxy = ChaosProxy(adapter, overrides=[override], seed=42)
        trace = await proxy.invoke("test")

        assert trace.output_text == "no tools"
        assert len(trace.tool_calls) == 0
