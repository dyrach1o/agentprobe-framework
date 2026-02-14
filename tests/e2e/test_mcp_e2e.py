"""End-to-end tests for the MCP adapter with a local mock server.

No API key or external packages required. The mock server simulates
an MCP-compliant tool server with ``call_tool()`` and ``list_tools()``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.adapters.mcp import MCPAdapter
from agentprobe.core.models import TestCase
from agentprobe.core.runner import TestRunner
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

pytestmark = [pytest.mark.e2e]


class MockMCPServer:
    """Local MCP server mock for testing.

    Implements the ``call_tool()`` and ``list_tools()`` interface expected
    by MCPAdapter.
    """

    async def call_tool(self, name: str, args: dict[str, object]) -> dict[str, object]:
        """Simulate a tool call with a deterministic response."""
        if name == "error_tool":
            return {"content": "Something went wrong", "isError": True}
        return {"content": f"Result for {name}: {args}"}

    async def list_tools(self) -> list[dict[str, object]]:
        """Return a list of available tool descriptions."""
        return [
            {
                "name": "search",
                "description": "Search the web for information",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
            },
            {
                "name": "calculate",
                "description": "Perform arithmetic calculations",
                "inputSchema": {"type": "object", "properties": {"expression": {"type": "string"}}},
            },
        ]


@pytest.fixture
def mock_server() -> MockMCPServer:
    """Create a mock MCP server."""
    return MockMCPServer()


@pytest.fixture
def mcp_adapter(mock_server: MockMCPServer) -> MCPAdapter:
    """Create an MCPAdapter with the mock server."""
    return MCPAdapter(mock_server, model_name="mock-model")


class TestMCPE2E:
    """End-to-end tests for MCPAdapter with a local mock server."""

    async def test_mcp_simple_tool_call(self, mcp_adapter: MCPAdapter) -> None:
        """Invoke adapter with a tool call and verify Trace output."""
        trace = await mcp_adapter.invoke(
            "search for python",
            tool_name="search",
            tool_args={"query": "python"},
        )

        assert trace.agent_name == "mcp"
        assert trace.output_text != ""
        assert "search" in trace.output_text.lower() or "python" in trace.output_text.lower()

    async def test_mcp_trace_has_tool_calls(self, mcp_adapter: MCPAdapter) -> None:
        """Verify Trace.tool_calls contains the correct tool invocation."""
        trace = await mcp_adapter.invoke(
            "calculate 2+2",
            tool_name="calculate",
            tool_args={"expression": "2+2"},
        )

        assert len(trace.tool_calls) == 1
        tc = trace.tool_calls[0]
        assert tc.tool_name == "calculate"
        assert tc.tool_input == {"expression": "2+2"}
        assert tc.success is True
        assert tc.tool_output is not None

    async def test_mcp_list_tools(self, mcp_adapter: MCPAdapter) -> None:
        """list_tools() returns normalized tool descriptions."""
        tools = await mcp_adapter.list_tools()

        assert len(tools) == 2
        names = {t["name"] for t in tools}
        assert names == {"search", "calculate"}
        for tool in tools:
            assert "description" in tool
            assert "input_schema" in tool

    async def test_mcp_error_handling(self, mcp_adapter: MCPAdapter) -> None:
        """Server returns an error — verify ToolCall.success is False."""
        trace = await mcp_adapter.invoke(
            "trigger error",
            tool_name="error_tool",
            tool_args={"input": "bad"},
        )

        assert len(trace.tool_calls) == 1
        tc = trace.tool_calls[0]
        assert tc.tool_name == "error_tool"
        assert tc.success is False
        assert tc.error is not None

    async def test_mcp_with_runner(self, mcp_adapter: MCPAdapter) -> None:
        """Full TestRunner pipeline with RuleBasedEvaluator."""
        evaluator = RuleBasedEvaluator(rules=[
            RuleSpec(rule_type="max_length", params={"max": 5000}),
        ])
        runner = TestRunner(evaluators=[evaluator])
        test_case = TestCase(
            name="mcp-e2e-eval",
            input_text="search for testing",
            metadata={"tool_name": "search"},
        )

        # MCP adapter uses kwargs for tool_name/tool_args, but the runner
        # only passes input_text. The adapter defaults to tool_name="default"
        # and tool_args={"input": input_text} when kwargs are absent.
        run = await runner.run([test_case], mcp_adapter)

        assert run.total_tests == 1
        assert run.passed == 1
        result = run.test_results[0]
        assert result.trace is not None
        assert len(result.trace.tool_calls) == 1

    async def test_mcp_store_and_retrieve(
        self, mcp_adapter: MCPAdapter, tmp_path: Path
    ) -> None:
        """Store MCP trace in SQLite and verify retrieval."""
        from agentprobe.storage.sqlite import SQLiteStorage

        trace = await mcp_adapter.invoke(
            "search python",
            tool_name="search",
            tool_args={"query": "python"},
        )
        storage = SQLiteStorage(db_path=tmp_path / "mcp.db")
        await storage.setup()
        try:
            await storage.save_trace(trace)
            loaded = await storage.load_trace(trace.trace_id)
            assert loaded is not None
            assert loaded.trace_id == trace.trace_id
            assert len(loaded.tool_calls) == 1
        finally:
            await storage.close()
