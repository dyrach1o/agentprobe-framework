"""Tests for the CostCalculator."""

from __future__ import annotations

import pytest

from agentprobe.core.exceptions import BudgetExceededError
from agentprobe.cost.calculator import CostCalculator, PricingConfig, PricingEntry
from tests.fixtures.traces import make_llm_call, make_trace


def _test_pricing() -> PricingConfig:
    """Create a simple pricing config for testing."""
    return PricingConfig(
        entries={
            "claude-sonnet-4-5-20250929": PricingEntry(
                model="claude-sonnet-4-5-20250929",
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
            ),
            "gpt-4o": PricingEntry(
                model="gpt-4o",
                input_cost_per_1k=0.0025,
                output_cost_per_1k=0.01,
            ),
        }
    )


class TestPricingConfig:
    """Tests for PricingConfig loading."""

    def test_load_from_default_dir(self) -> None:
        config = PricingConfig.load_from_dir()
        assert len(config.entries) > 0
        assert "claude-sonnet-4-5-20250929" in config.entries

    def test_load_from_nonexistent_dir(self, tmp_path: object) -> None:
        config = PricingConfig.load_from_dir("/nonexistent/path")
        assert len(config.entries) == 0


class TestCostCalculator:
    """Tests for CostCalculator cost computation."""

    @pytest.fixture
    def calculator(self) -> CostCalculator:
        return CostCalculator(pricing=_test_pricing())

    def test_calculate_llm_cost_known_model(self, calculator: CostCalculator) -> None:
        call = make_llm_call(
            model="claude-sonnet-4-5-20250929", input_tokens=1000, output_tokens=500
        )
        cost = calculator.calculate_llm_cost(call)
        expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
        assert cost == pytest.approx(expected, abs=1e-6)

    def test_calculate_llm_cost_unknown_model(self, calculator: CostCalculator) -> None:
        call = make_llm_call(model="unknown-model", input_tokens=100)
        cost = calculator.calculate_llm_cost(call)
        assert cost == 0.0

    def test_calculate_llm_cost_zero_tokens(self, calculator: CostCalculator) -> None:
        call = make_llm_call(model="claude-sonnet-4-5-20250929", input_tokens=0, output_tokens=0)
        cost = calculator.calculate_llm_cost(call)
        assert cost == 0.0

    def test_calculate_trace_cost_single_model(self, calculator: CostCalculator) -> None:
        trace = make_trace(
            llm_calls=[
                make_llm_call(
                    model="claude-sonnet-4-5-20250929", input_tokens=1000, output_tokens=500
                ),
            ]
        )
        summary = calculator.calculate_trace_cost(trace)
        assert summary.total_llm_cost_usd > 0
        assert summary.total_cost_usd == summary.total_llm_cost_usd
        assert "claude-sonnet-4-5-20250929" in summary.breakdown_by_model

    def test_calculate_trace_cost_multiple_models(self, calculator: CostCalculator) -> None:
        trace = make_trace(
            llm_calls=[
                make_llm_call(
                    model="claude-sonnet-4-5-20250929", input_tokens=100, output_tokens=50
                ),
                make_llm_call(model="gpt-4o", input_tokens=200, output_tokens=100),
            ]
        )
        summary = calculator.calculate_trace_cost(trace)
        assert len(summary.breakdown_by_model) == 2
        assert summary.total_input_tokens == 300
        assert summary.total_output_tokens == 150

    def test_calculate_trace_cost_empty(self, calculator: CostCalculator) -> None:
        trace = make_trace(llm_calls=[])
        summary = calculator.calculate_trace_cost(trace)
        assert summary.total_cost_usd == 0.0

    def test_budget_not_exceeded(self) -> None:
        calculator = CostCalculator(pricing=_test_pricing(), budget_limit_usd=10.0)
        trace = make_trace(
            llm_calls=[make_llm_call(model="claude-sonnet-4-5-20250929", input_tokens=100)]
        )
        summary = calculator.calculate_trace_cost(trace)
        assert summary.total_cost_usd < 10.0

    def test_budget_exceeded_raises(self) -> None:
        calculator = CostCalculator(pricing=_test_pricing(), budget_limit_usd=0.0001)
        trace = make_trace(
            llm_calls=[
                make_llm_call(
                    model="claude-sonnet-4-5-20250929", input_tokens=10000, output_tokens=5000
                ),
            ]
        )
        with pytest.raises(BudgetExceededError):
            calculator.calculate_trace_cost(trace)

    @pytest.mark.parametrize(
        "input_tokens,output_tokens,expected_cost",
        [
            (1000, 500, 0.0105),
            (0, 0, 0.0),
            (1, 1, 0.000018),
        ],
    )
    def test_cost_accuracy(
        self,
        calculator: CostCalculator,
        input_tokens: int,
        output_tokens: int,
        expected_cost: float,
    ) -> None:
        call = make_llm_call(
            model="claude-sonnet-4-5-20250929",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        cost = calculator.calculate_llm_cost(call)
        assert cost == pytest.approx(expected_cost, abs=1e-6)

    def test_breakdown_call_count(self, calculator: CostCalculator) -> None:
        trace = make_trace(
            llm_calls=[
                make_llm_call(model="gpt-4o", input_tokens=10),
                make_llm_call(model="gpt-4o", input_tokens=20),
                make_llm_call(model="gpt-4o", input_tokens=30),
            ]
        )
        summary = calculator.calculate_trace_cost(trace)
        assert summary.breakdown_by_model["gpt-4o"].call_count == 3
        assert summary.breakdown_by_model["gpt-4o"].input_tokens == 60


class TestCostCalculatorNewProviders:
    """Parametrized tests for cost calculation across multiple providers."""

    @pytest.mark.parametrize(
        "model,input_tokens,output_tokens,expected_cost",
        [
            # Google models
            ("gemini-1.5-pro", 1000, 500, (1000 / 1000) * 0.00125 + (500 / 1000) * 0.005),
            ("gemini-1.5-flash", 1000, 500, (1000 / 1000) * 0.000075 + (500 / 1000) * 0.0003),
            ("gemini-2.0-flash", 2000, 1000, (2000 / 1000) * 0.0001 + (1000 / 1000) * 0.0004),
            # Mistral models
            ("mistral-large-latest", 1000, 500, (1000 / 1000) * 0.002 + (500 / 1000) * 0.006),
            ("mistral-small-latest", 1000, 500, (1000 / 1000) * 0.0002 + (500 / 1000) * 0.0006),
            ("codestral-latest", 1000, 500, (1000 / 1000) * 0.0003 + (500 / 1000) * 0.0009),
            # Cohere models
            ("command-r-plus", 1000, 500, (1000 / 1000) * 0.0025 + (500 / 1000) * 0.01),
            ("command-r", 1000, 500, (1000 / 1000) * 0.00015 + (500 / 1000) * 0.0006),
            ("embed-english-v3.0", 1000, 0, (1000 / 1000) * 0.0001),
        ],
    )
    def test_new_provider_cost_accuracy(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        expected_cost: float,
    ) -> None:
        config = PricingConfig.load_from_dir()
        calculator = CostCalculator(pricing=config)
        call = make_llm_call(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        cost = calculator.calculate_llm_cost(call)
        assert cost == pytest.approx(expected_cost, abs=1e-8)
