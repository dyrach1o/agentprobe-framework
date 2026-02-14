"""End-to-end tests for the CrewAI adapter with a real Anthropic model.

Creates a minimal Crew with one Agent and one Task, invokes it through
the adapter, and validates trace structure and pipeline integration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.conftest import requires_api_key, requires_crewai

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.api,
    requires_crewai,
    requires_api_key,
]


def _build_crew(model_name: str) -> object:
    """Build a minimal CrewAI Crew with one agent and one task."""
    from crewai import Agent, Crew, Task

    agent = Agent(
        role="assistant",
        goal="Answer questions accurately and concisely",
        backstory="A helpful assistant that provides brief answers.",
        llm=f"anthropic/{model_name}",
        verbose=False,
    )
    task = Task(
        description="{input}",
        agent=agent,
        expected_output="A concise answer",
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    return crew


class TestCrewAIE2E:
    """End-to-end tests for CrewAIAdapter with a real model."""

    async def test_crewai_simple_invoke(self, api_key: str, model_name: str) -> None:
        """Adapter produces a Trace with non-empty output."""
        from agentprobe.adapters.crewai import CrewAIAdapter

        crew = _build_crew(model_name)
        adapter = CrewAIAdapter(crew, model_name=model_name)
        trace = await adapter.invoke("What is the capital of France?")

        assert trace.agent_name == "crewai"
        assert trace.output_text != ""

    async def test_crewai_trace_structure(self, api_key: str, model_name: str) -> None:
        """Trace has expected structural fields."""
        from agentprobe.adapters.crewai import CrewAIAdapter

        crew = _build_crew(model_name)
        adapter = CrewAIAdapter(crew, model_name=model_name)
        trace = await adapter.invoke("Name a primary color.")

        assert trace.agent_name == "crewai"
        assert trace.total_latency_ms > 0
        assert trace.created_at is not None

    async def test_crewai_with_runner(self, api_key: str, model_name: str) -> None:
        """Full TestRunner pipeline with RuleBasedEvaluator."""
        from agentprobe.adapters.crewai import CrewAIAdapter
        from agentprobe.core.models import TestCase
        from agentprobe.core.runner import TestRunner
        from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

        crew = _build_crew(model_name)
        adapter = CrewAIAdapter(crew, model_name=model_name)

        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 5000}),
            ]
        )
        runner = TestRunner(evaluators=[evaluator])
        test_case = TestCase(name="crewai-e2e-eval", input_text="Say hello.")

        run = await runner.run([test_case], adapter)

        assert run.total_tests == 1
        assert run.passed == 1

    async def test_crewai_store_results(
        self, api_key: str, model_name: str, tmp_path: Path
    ) -> None:
        """Persist trace to SQLite and verify retrieval."""
        from agentprobe.adapters.crewai import CrewAIAdapter
        from agentprobe.storage.sqlite import SQLiteStorage

        crew = _build_crew(model_name)
        adapter = CrewAIAdapter(crew, model_name=model_name)
        trace = await adapter.invoke("What is 1 + 1?")

        storage = SQLiteStorage(db_path=tmp_path / "crewai.db")
        await storage.setup()
        try:
            await storage.save_trace(trace)
            loaded = await storage.load_trace(trace.trace_id)
            assert loaded is not None
            assert loaded.trace_id == trace.trace_id
        finally:
            await storage.close()
