"""Tests for the MCPAdapter."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.adapters.mcp import MCPAdapter
from agentprobe.core.exceptions import AdapterError


class _FakeMCPServer:
    """Simulates an MCP server with async tool calling."""

    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self._result = result or {"content": "tool output", "isError": False}
        self.last_tool_name: str = ""
        self.last_tool_args: dict[str, Any] = {}

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
        self.last_tool_name = tool_name
        self.last_tool_args = tool_args
        return self._result


class _SyncMCPServer:
    """MCP server with synchronous call_tool."""

    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self._result = result or {"content": "sync output"}

    def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
        return self._result


class _BrokenMCPServer:
    """MCP server that raises exceptions."""

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        msg = "server unavailable"
        raise ConnectionError(msg)


class _NoCallToolServer:
    """Server without call_tool method."""


class _ObjectResultServer:
    """Server that returns an object with .content attribute."""

    def __init__(self) -> None:
        self._called = False

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        self._called = True
        return _FakeToolResult(
            content=[_FakeTextContent(text="object output")],
            isError=False,
        )


class _FakeTextContent:
    """Simulates MCP TextContent."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeToolResult:
    """Simulates MCP CallToolResult."""

    def __init__(self, content: list[Any], isError: bool = False) -> None:  # noqa: N803
        self.content = content
        self.isError = isError


class _ListToolsServer:
    """Server that supports list_tools."""

    def __init__(self, tools: list[dict[str, Any]] | None = None) -> None:
        self._tools = tools or [
            {"name": "search", "description": "Search things", "inputSchema": {"type": "object"}},
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
        return {"content": "ok"}

    async def list_tools(self) -> list[dict[str, Any]]:
        return self._tools


class TestMCPAdapter:
    """Tests for MCPAdapter."""

    async def test_basic_invocation(self) -> None:
        server = _FakeMCPServer()
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("test input")
        assert trace.output_text == "tool output"
        assert trace.agent_name == "mcp"
        assert len(trace.tool_calls) == 1

    async def test_tool_call_captured(self) -> None:
        server = _FakeMCPServer(result={"content": "search result"})
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("query", tool_name="search", tool_args={"q": "test"})

        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[0].tool_input == {"q": "test"}
        assert trace.tool_calls[0].tool_output == "search result"
        assert trace.tool_calls[0].success is True

    async def test_error_result(self) -> None:
        server = _FakeMCPServer(result={"content": "not found", "isError": True})
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("test")

        assert trace.tool_calls[0].success is False
        assert trace.tool_calls[0].error == "not found"

    async def test_object_result_with_content(self) -> None:
        server = _ObjectResultServer()
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("test")
        assert "object output" in trace.output_text

    async def test_sync_server(self) -> None:
        server = _SyncMCPServer()
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("test")
        assert trace.output_text == "sync output"

    async def test_broken_server_raises_adapter_error(self) -> None:
        server = _BrokenMCPServer()
        adapter = MCPAdapter(server)

        with pytest.raises(AdapterError, match="server unavailable"):
            await adapter.invoke("test")

    async def test_no_call_tool_raises_adapter_error(self) -> None:
        server = _NoCallToolServer()
        adapter = MCPAdapter(server)

        with pytest.raises(AdapterError, match="no call_tool"):
            await adapter.invoke("test")

    async def test_custom_name(self) -> None:
        server = _FakeMCPServer()
        adapter = MCPAdapter(server, name="my-mcp")

        trace = await adapter.invoke("test")
        assert trace.agent_name == "my-mcp"

    async def test_list_tools(self) -> None:
        server = _ListToolsServer()
        adapter = MCPAdapter(server)

        tools = await adapter.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "search"

    async def test_list_tools_not_supported(self) -> None:
        adapter = MCPAdapter(_NoCallToolServer())

        with pytest.raises(AdapterError, match="no list_tools"):
            await adapter.list_tools()

    async def test_string_tool_args(self) -> None:
        server = _FakeMCPServer()
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("test", tool_name="run", tool_args="raw string")
        assert trace.tool_calls[0].tool_input == {"input": "raw string"}

    async def test_default_tool_name(self) -> None:
        server = _FakeMCPServer()
        adapter = MCPAdapter(server)

        trace = await adapter.invoke("test input")
        assert trace.tool_calls[0].tool_name == "default"
