"""End-to-end tests for the AutoGen adapter with a real Anthropic model.

Creates an AssistantAgent + UserProxyAgent pair, invokes through the
adapter, and validates trace structure and pipeline integration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.conftest import requires_api_key, requires_autogen

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.api,
    requires_autogen,
    requires_api_key,
]


def _build_agents(api_key: str, model_name: str) -> tuple[object, object]:
    """Build AutoGen AssistantAgent and UserProxyAgent pair."""
    from autogen import AssistantAgent, UserProxyAgent

    config_list = [
        {
            "model": model_name,
            "api_key": api_key,
            "api_type": "anthropic",
        }
    ]
    assistant = AssistantAgent(
        "assistant",
        llm_config={"config_list": config_list},
        system_message="You are a helpful assistant. Reply concisely.",
    )
    user_proxy = UserProxyAgent(
        "user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config=False,
    )
    return assistant, user_proxy


class TestAutoGenE2E:
    """End-to-end tests for AutoGenAdapter with a real model."""

    async def test_autogen_simple_invoke(self, api_key: str, model_name: str) -> None:
        """Adapter produces a Trace with non-empty output."""
        from agentprobe.adapters.autogen import AutoGenAdapter

        assistant, user_proxy = _build_agents(api_key, model_name)
        adapter = AutoGenAdapter(assistant, user_proxy, model_name=model_name)
        trace = await adapter.invoke("What is the capital of Japan?")

        assert trace.agent_name == "autogen"
        assert trace.output_text != ""

    async def test_autogen_trace_has_messages(self, api_key: str, model_name: str) -> None:
        """Trace output_text is non-empty after conversation."""
        from agentprobe.adapters.autogen import AutoGenAdapter

        assistant, user_proxy = _build_agents(api_key, model_name)
        adapter = AutoGenAdapter(assistant, user_proxy, model_name=model_name)
        trace = await adapter.invoke("Say the word 'hello'.")

        assert trace.output_text != ""
        assert trace.total_latency_ms > 0

    async def test_autogen_with_runner(self, api_key: str, model_name: str) -> None:
        """Full TestRunner pipeline with RuleBasedEvaluator."""
        from agentprobe.adapters.autogen import AutoGenAdapter
        from agentprobe.core.models import TestCase
        from agentprobe.core.runner import TestRunner
        from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

        assistant, user_proxy = _build_agents(api_key, model_name)
        adapter = AutoGenAdapter(assistant, user_proxy, model_name=model_name)

        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 5000}),
            ]
        )
        runner = TestRunner(evaluators=[evaluator])
        test_case = TestCase(name="autogen-e2e-eval", input_text="Say hi.")

        run = await runner.run([test_case], adapter)

        assert run.total_tests == 1
        assert run.passed == 1

    async def test_autogen_store_results(
        self, api_key: str, model_name: str, tmp_path: Path
    ) -> None:
        """Persist trace to SQLite and verify retrieval."""
        from agentprobe.adapters.autogen import AutoGenAdapter
        from agentprobe.storage.sqlite import SQLiteStorage

        assistant, user_proxy = _build_agents(api_key, model_name)
        adapter = AutoGenAdapter(assistant, user_proxy, model_name=model_name)
        trace = await adapter.invoke("What is 3 + 3?")

        storage = SQLiteStorage(db_path=tmp_path / "autogen.db")
        await storage.setup()
        try:
            await storage.save_trace(trace)
            loaded = await storage.load_trace(trace.trace_id)
            assert loaded is not None
            assert loaded.trace_id == trace.trace_id
        finally:
            await storage.close()
