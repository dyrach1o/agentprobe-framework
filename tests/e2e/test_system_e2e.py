"""End-to-end system integration tests.

Validates the complete AgentProbe pipeline: adapter -> runner ->
evaluator -> storage -> reporter, using the MCP mock server (no API key
needed) and optionally LangChain with a real Anthropic model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentprobe.adapters.mcp import MCPAdapter
from agentprobe.core.models import TestCase
from agentprobe.core.runner import TestRunner
from agentprobe.cost.calculator import CostCalculator
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec
from agentprobe.metrics.collector import MetricCollector
from agentprobe.reporting.json_reporter import JSONReporter
from agentprobe.storage.sqlite import SQLiteStorage
from tests.e2e.conftest import requires_api_key, requires_langchain

pytestmark = [pytest.mark.e2e]


class _MockMCPServer:
    """Minimal mock MCP server for system tests."""

    async def call_tool(self, name: str, args: dict[str, object]) -> dict[str, object]:
        return {"content": f"Mock result for {name}: {args}"}

    async def list_tools(self) -> list[dict[str, object]]:
        return [{"name": "mock_tool", "description": "A mock tool", "inputSchema": {}}]


class TestSystemE2E:
    """Full system pipeline tests using the MCP mock adapter."""

    async def test_full_pipeline_mcp(self, tmp_path: Path) -> None:
        """MCP adapter -> TestRunner -> evaluator -> SQLite storage."""
        server = _MockMCPServer()
        adapter = MCPAdapter(server, model_name="mock-model")

        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 5000}),
            ]
        )
        runner = TestRunner(evaluators=[evaluator])
        test_cases = [
            TestCase(name="system-test-1", input_text="query data"),
            TestCase(name="system-test-2", input_text="another query"),
        ]

        run = await runner.run(test_cases, adapter)

        assert run.total_tests == 2
        assert run.passed == 2

        # Store results
        storage = SQLiteStorage(db_path=tmp_path / "system.db")
        await storage.setup()
        try:
            for result in run.test_results:
                if result.trace is not None:
                    await storage.save_trace(result.trace)
                await storage.save_result(result)

            # Verify retrieval
            traces = await storage.list_traces()
            assert len(traces) == 2

            results = await storage.load_results()
            assert len(results) == 2
        finally:
            await storage.close()

    async def test_full_pipeline_with_cost(self) -> None:
        """Invoke mock adapter and verify CostCalculator runs without error."""
        server = _MockMCPServer()
        adapter = MCPAdapter(server, model_name="mock-model")
        trace = await adapter.invoke("test input", tool_name="mock_tool")

        calculator = CostCalculator()
        summary = calculator.calculate_trace_cost(trace)
        # Mock adapter produces no LLM calls, so cost should be zero
        assert summary.total_cost_usd == 0.0
        assert summary.total_llm_cost_usd == 0.0

    async def test_full_pipeline_with_metrics(self) -> None:
        """Invoke mock adapter and collect metrics from the trace."""
        server = _MockMCPServer()
        adapter = MCPAdapter(server, model_name="mock-model")
        trace = await adapter.invoke("metric test", tool_name="mock_tool")

        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)
        assert len(metrics) > 0

        # Should have at least latency and tool_call_count
        metric_names = {m.metric_name for m in metrics}
        assert "latency_ms" in metric_names
        assert "tool_call_count" in metric_names

    async def test_full_pipeline_store_and_report(self, tmp_path: Path) -> None:
        """Run suite -> store all results -> generate JSON report -> verify."""
        server = _MockMCPServer()
        adapter = MCPAdapter(server, model_name="mock-model")

        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 5000}),
            ]
        )
        runner = TestRunner(evaluators=[evaluator])
        test_cases = [
            TestCase(name="report-test-1", input_text="data query"),
            TestCase(name="report-test-2", input_text="another query"),
            TestCase(name="report-test-3", input_text="third query"),
        ]

        run = await runner.run(test_cases, adapter)
        assert run.total_tests == 3
        assert run.passed == 3

        # Store
        storage = SQLiteStorage(db_path=tmp_path / "report.db")
        await storage.setup()
        try:
            for result in run.test_results:
                await storage.save_result(result)
        finally:
            await storage.close()

        # Report
        report_dir = tmp_path / "reports"
        reporter = JSONReporter(output_dir=report_dir)
        await reporter.report(run)

        # Verify report file
        report_files = list(report_dir.glob("report-*.json"))
        assert len(report_files) == 1

        report_data = json.loads(report_files[0].read_text(encoding="utf-8"))
        assert report_data["total_tests"] == 3
        assert report_data["passed"] == 3
        assert len(report_data["test_results"]) == 3


@pytest.mark.api
@requires_langchain
@requires_api_key
class TestSystemE2EWithLangChain:
    """Full system pipeline tests using a real LangChain adapter."""

    async def test_full_pipeline_langchain(
        self, api_key: str, model_name: str, tmp_path: Path
    ) -> None:
        """LangChain -> TestRunner -> evaluator -> SQLite -> JSON report."""
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

        evaluator = RuleBasedEvaluator(
            rules=[
                RuleSpec(rule_type="max_length", params={"max": 5000}),
            ]
        )
        runner = TestRunner(evaluators=[evaluator])
        test_case = TestCase(name="system-langchain", input_text="Say hello briefly.")

        run = await runner.run([test_case], adapter)
        assert run.total_tests == 1
        assert run.passed == 1

        # Store
        storage = SQLiteStorage(db_path=tmp_path / "langchain_system.db")
        await storage.setup()
        try:
            result = run.test_results[0]
            if result.trace is not None:
                await storage.save_trace(result.trace)
            await storage.save_result(result)

            loaded = await storage.load_trace(result.trace.trace_id)
            assert loaded is not None
        finally:
            await storage.close()

        # Report
        report_dir = tmp_path / "lc_reports"
        reporter = JSONReporter(output_dir=report_dir)
        await reporter.report(run)

        report_files = list(report_dir.glob("report-*.json"))
        assert len(report_files) == 1
