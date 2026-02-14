"""Integration test: CostCalculator + BudgetEnforcer on real traces."""

from __future__ import annotations

import pytest

from agentprobe.core.exceptions import BudgetExceededError
from agentprobe.cost.budget import BudgetEnforcer
from agentprobe.cost.calculator import CostCalculator, PricingConfig, PricingEntry
from agentprobe.trace.recorder import TraceRecorder


def _make_pricing() -> PricingConfig:
    """Create a minimal pricing config for testing."""
    return PricingConfig(
        entries={
            "test-model": PricingEntry(
                model="test-model",
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
            ),
            "cheap-model": PricingEntry(
                model="cheap-model",
                input_cost_per_1k=0.0001,
                output_cost_per_1k=0.0002,
            ),
        }
    )


@pytest.mark.integration
class TestCostBudgetFlow:
    """End-to-end cost calculation and budget enforcement."""

    @pytest.mark.asyncio
    async def test_calculate_cost_from_recorded_trace(self) -> None:
        """Record a trace, then calculate its cost."""
        recorder = TraceRecorder(agent_name="cost-test", model="test-model")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(
                model="test-model",
                input_tokens=1000,
                output_tokens=500,
                latency_ms=200,
            )
        trace = recorder.finalize(input_text="test", output="response")

        calculator = CostCalculator(pricing=_make_pricing())
        summary = calculator.calculate_trace_cost(trace)

        # 1000/1000 * 0.003 + 500/1000 * 0.015 = 0.003 + 0.0075 = 0.0105
        assert summary.total_cost_usd == pytest.approx(0.0105, abs=1e-6)
        assert "test-model" in summary.breakdown_by_model
        assert summary.total_input_tokens == 1000
        assert summary.total_output_tokens == 500

    @pytest.mark.asyncio
    async def test_multi_model_cost_breakdown(self) -> None:
        """Trace with multiple models gets per-model breakdown."""
        recorder = TraceRecorder(agent_name="multi-model")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="test-model", input_tokens=500, output_tokens=200)
            ctx.record_llm_call(model="cheap-model", input_tokens=2000, output_tokens=1000)
        trace = recorder.finalize(input_text="multi", output="result")

        calculator = CostCalculator(pricing=_make_pricing())
        summary = calculator.calculate_trace_cost(trace)

        assert len(summary.breakdown_by_model) == 2
        assert "test-model" in summary.breakdown_by_model
        assert "cheap-model" in summary.breakdown_by_model
        assert summary.total_cost_usd > 0

    @pytest.mark.asyncio
    async def test_budget_enforcer_within_budget(self) -> None:
        """Budget check passes when cost is within limit."""
        recorder = TraceRecorder(agent_name="budget-ok")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="test-model", input_tokens=100, output_tokens=50)
        trace = recorder.finalize(input_text="x", output="y")

        calculator = CostCalculator(pricing=_make_pricing())
        summary = calculator.calculate_trace_cost(trace)

        enforcer = BudgetEnforcer(test_budget_usd=1.0)
        result = enforcer.check_test(summary)

        assert result is not None
        assert result.within_budget is True
        assert result.remaining_usd > 0

    @pytest.mark.asyncio
    async def test_budget_enforcer_exceeds_budget(self) -> None:
        """Budget check fails when cost exceeds limit."""
        recorder = TraceRecorder(agent_name="budget-exceed")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="test-model", input_tokens=10000, output_tokens=5000)
        trace = recorder.finalize(input_text="expensive", output="costly response")

        calculator = CostCalculator(pricing=_make_pricing())
        summary = calculator.calculate_trace_cost(trace)

        enforcer = BudgetEnforcer(test_budget_usd=0.001)
        result = enforcer.check_test(summary)

        assert result is not None
        assert result.within_budget is False
        assert result.remaining_usd < 0

    @pytest.mark.asyncio
    async def test_suite_budget_enforcement(self) -> None:
        """Suite-level budget check across multiple traces."""
        pricing = _make_pricing()
        calculator = CostCalculator(pricing=pricing)
        summaries = []

        for _ in range(5):
            recorder = TraceRecorder(agent_name="suite-test")
            async with recorder.recording() as ctx:
                ctx.record_llm_call(model="test-model", input_tokens=1000, output_tokens=500)
            trace = recorder.finalize(input_text="x", output="y")
            summaries.append(calculator.calculate_trace_cost(trace))

        enforcer = BudgetEnforcer(suite_budget_usd=1.0)
        result = enforcer.check_suite(summaries)

        assert result is not None
        assert result.within_budget is True

        # Tight budget
        tight_enforcer = BudgetEnforcer(suite_budget_usd=0.01)
        tight_result = tight_enforcer.check_suite(summaries)
        assert tight_result is not None
        assert tight_result.within_budget is False

    @pytest.mark.asyncio
    async def test_calculator_budget_limit_raises(self) -> None:
        """CostCalculator with budget_limit_usd raises on exceed."""
        recorder = TraceRecorder(agent_name="budget-raise")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="test-model", input_tokens=10000, output_tokens=5000)
        trace = recorder.finalize(input_text="x", output="y")

        calculator = CostCalculator(pricing=_make_pricing(), budget_limit_usd=0.001)
        with pytest.raises(BudgetExceededError):
            calculator.calculate_trace_cost(trace)

    @pytest.mark.asyncio
    async def test_unknown_model_zero_cost(self) -> None:
        """Unknown model returns zero cost without raising."""
        recorder = TraceRecorder(agent_name="unknown-model")
        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="unknown-xyz", input_tokens=1000, output_tokens=500)
        trace = recorder.finalize(input_text="x", output="y")

        calculator = CostCalculator(pricing=_make_pricing())
        summary = calculator.calculate_trace_cost(trace)

        assert summary.total_cost_usd == 0.0
