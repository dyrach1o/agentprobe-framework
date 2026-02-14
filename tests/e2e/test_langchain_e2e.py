"""End-to-end tests for the LangChain adapter with a real Anthropic model.

Uses ChatAnthropic wrapped in a RunnableLambda to match the adapter's
``{"input": input_text}`` invocation format.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.conftest import requires_api_key, requires_langchain

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.api,
    requires_langchain,
    requires_api_key,
]


def _build_chain(api_key: str, model_name: str) -> object:
    """Build a LangChain runnable that accepts ``{"input": text}``."""
    from langchain_anthropic import ChatAnthropic
    from langchain_core.runnables import RunnableLambda

    llm = ChatAnthropic(model=model_name, api_key=api_key, max_tokens=256)
    chain = RunnableLambda(lambda x: x["input"]) | llm | RunnableLambda(lambda msg: str(msg.content))
    return chain


class TestLangChainE2E:
    """End-to-end tests for LangChainAdapter with a real model."""

    async def test_langchain_simple_invoke(self, api_key: str, model_name: str) -> None:
        """Adapter produces a Trace with non-empty output."""
        from agentprobe.adapters.langchain import LangChainAdapter

        chain = _build_chain(api_key, model_name)
        adapter = LangChainAdapter(chain, model_name=model_name)
        trace = await adapter.invoke("Say hello in exactly two words.")

        assert trace.agent_name == "langchain"
        assert trace.output_text != ""
        assert trace.input_text == "Say hello in exactly two words."

    async def test_langchain_trace_has_metadata(self, api_key: str, model_name: str) -> None:
        """Trace contains expected structural fields."""
        from agentprobe.adapters.langchain import LangChainAdapter

        chain = _build_chain(api_key, model_name)
        adapter = LangChainAdapter(chain, model_name=model_name)
        trace = await adapter.invoke("What is 2 + 2?")

        assert trace.agent_name == "langchain"
        assert trace.created_at is not None
        assert trace.total_latency_ms > 0

    async def test_langchain_with_evaluator(self, api_key: str, model_name: str) -> None:
        """Full pipeline: adapter -> TestRunner -> RuleBasedEvaluator."""
        from agentprobe.adapters.langchain import LangChainAdapter
        from agentprobe.core.models import TestCase
        from agentprobe.core.runner import TestRunner
        from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

        chain = _build_chain(api_key, model_name)
        adapter = LangChainAdapter(chain, model_name=model_name)

        evaluator = RuleBasedEvaluator(rules=[
            RuleSpec(rule_type="max_length", params={"max": 5000}),
        ])
        runner = TestRunner(evaluators=[evaluator])
        test_case = TestCase(name="langchain-e2e-eval", input_text="Say hello.")

        run = await runner.run([test_case], adapter)

        assert run.total_tests == 1
        assert run.passed == 1
        result = run.test_results[0]
        assert result.trace is not None
        assert len(result.eval_results) == 1

    async def test_langchain_store_and_retrieve(
        self, api_key: str, model_name: str, tmp_path: Path
    ) -> None:
        """Invoke -> store in SQLite -> load back and verify."""
        from agentprobe.adapters.langchain import LangChainAdapter
        from agentprobe.storage.sqlite import SQLiteStorage

        chain = _build_chain(api_key, model_name)
        adapter = LangChainAdapter(chain, model_name=model_name)
        trace = await adapter.invoke("What color is the sky?")

        storage = SQLiteStorage(db_path=tmp_path / "test.db")
        await storage.setup()
        try:
            await storage.save_trace(trace)
            loaded = await storage.load_trace(trace.trace_id)
            assert loaded is not None
            assert loaded.trace_id == trace.trace_id
            assert loaded.output_text == trace.output_text
        finally:
            await storage.close()

    async def test_langchain_cost_calculation(self, api_key: str, model_name: str) -> None:
        """Invoke and run through CostCalculator."""
        from agentprobe.adapters.langchain import LangChainAdapter
        from agentprobe.cost.calculator import CostCalculator

        chain = _build_chain(api_key, model_name)
        adapter = LangChainAdapter(chain, model_name=model_name)
        trace = await adapter.invoke("Respond with just the word 'test'.")

        calculator = CostCalculator()
        summary = calculator.calculate_trace_cost(trace)

        # The adapter may not extract token counts from a plain string result,
        # so cost could be zero. Verify the calculation completes without error.
        assert summary.total_cost_usd >= 0.0
