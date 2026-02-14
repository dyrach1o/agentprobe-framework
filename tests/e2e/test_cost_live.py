"""Live cost test — verifies real token usage is captured and costed."""

from __future__ import annotations

import pytest

from tests.e2e.conftest import requires_api_key, requires_langchain

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.api,
    requires_langchain,
    requires_api_key,
]


class TestLiveCost:
    """Tests that real API calls produce non-zero cost data."""

    async def test_token_usage_captured(self, api_key: str, model_name: str) -> None:
        """Verify the callback handler captures real token counts."""
        from langchain_anthropic import ChatAnthropic
        from langchain_core.runnables import RunnableLambda

        from agentprobe.adapters.langchain import LangChainAdapter

        llm = ChatAnthropic(model=model_name, api_key=api_key, max_tokens=128)
        chain = (
            RunnableLambda(lambda x: x["input"])
            | llm
            | RunnableLambda(lambda msg: str(msg.content))
        )
        adapter = LangChainAdapter(chain, model_name=model_name)
        trace = await adapter.invoke("What is 2+2? Reply in one word.")

        assert trace.output_text != ""
        assert len(trace.llm_calls) == 1, f"Expected 1 LLM call, got {len(trace.llm_calls)}"

        call = trace.llm_calls[0]
        assert call.input_tokens > 0, f"Expected input_tokens > 0, got {call.input_tokens}"
        assert call.output_tokens > 0, f"Expected output_tokens > 0, got {call.output_tokens}"
        assert call.model == model_name or "claude" in call.model

    async def test_cost_is_nonzero(self, api_key: str, model_name: str) -> None:
        """Verify CostCalculator produces a real dollar amount."""
        from langchain_anthropic import ChatAnthropic
        from langchain_core.runnables import RunnableLambda

        from agentprobe.adapters.langchain import LangChainAdapter
        from agentprobe.cost.calculator import CostCalculator

        llm = ChatAnthropic(model=model_name, api_key=api_key, max_tokens=128)
        chain = (
            RunnableLambda(lambda x: x["input"])
            | llm
            | RunnableLambda(lambda msg: str(msg.content))
        )
        adapter = LangChainAdapter(chain, model_name=model_name)
        trace = await adapter.invoke("Say hello.")

        calculator = CostCalculator()
        summary = calculator.calculate_trace_cost(trace)

        assert summary.total_cost_usd > 0, f"Expected cost > 0, got {summary.total_cost_usd}"
        assert summary.total_input_tokens > 0
        assert summary.total_output_tokens > 0
        assert model_name in summary.breakdown_by_model

    async def test_full_pipeline_with_real_cost(self, api_key: str, model_name: str) -> None:
        """Full pipeline: invoke -> evaluate -> calculate cost -> verify."""
        from langchain_anthropic import ChatAnthropic
        from langchain_core.runnables import RunnableLambda

        from agentprobe.adapters.langchain import LangChainAdapter
        from agentprobe.core.models import TestCase
        from agentprobe.core.runner import TestRunner
        from agentprobe.cost.calculator import CostCalculator
        from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

        llm = ChatAnthropic(model=model_name, api_key=api_key, max_tokens=256)
        chain = (
            RunnableLambda(lambda x: x["input"])
            | llm
            | RunnableLambda(lambda msg: str(msg.content))
        )
        adapter = LangChainAdapter(chain, model_name=model_name)

        evaluator = RuleBasedEvaluator(rules=[
            RuleSpec(rule_type="max_length", params={"max": 3000}),
        ])
        runner = TestRunner(evaluators=[evaluator])
        test_cases = [
            TestCase(name="cost-test-1", input_text="What is the capital of France?"),
            TestCase(name="cost-test-2", input_text="Name three primary colors."),
        ]

        run = await runner.run(test_cases, adapter)

        assert run.passed == 2

        calculator = CostCalculator()
        total_cost = 0.0
        for result in run.test_results:
            assert result.trace is not None
            assert len(result.trace.llm_calls) == 1
            summary = calculator.calculate_trace_cost(result.trace)
            total_cost += summary.total_cost_usd

        assert total_cost > 0, f"Expected total cost > 0, got {total_cost}"
