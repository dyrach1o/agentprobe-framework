"""MCP (Model Context Protocol) server adapter.

Wraps an MCP server via stdio or HTTP transport and translates tool
call results into AgentProbe's Trace format.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import ToolCall, Trace

logger = logging.getLogger(__name__)


class MCPAdapter(BaseAdapter):
    """Adapter for MCP (Model Context Protocol) servers.

    Communicates with an MCP server to execute tool calls and captures
    the results as a structured trace.

    Attributes:
        _server: The MCP server client or connection.
        _transport: Transport type ('stdio' or 'http').
        _model_name: Optional model name for trace records.
    """

    def __init__(
        self,
        server: Any,
        *,
        name: str = "mcp",
        transport: str = "stdio",
        model_name: str | None = None,
    ) -> None:
        """Initialize the MCP adapter.

        Args:
            server: An MCP server client or connection object.
            name: Adapter name for identification.
            transport: Transport protocol ('stdio' or 'http').
            model_name: Model name to record in traces.
        """
        super().__init__(name)
        self._server = server
        self._transport = transport
        self._model_name = model_name

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the MCP server and build a trace.

        Sends the input as a tool call request and captures the response.

        Args:
            input_text: The input prompt or tool call specification.
            **kwargs: Additional arguments (e.g., tool_name, tool_args).

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the server invocation fails.
        """
        builder = self._create_builder(model=self._model_name)
        builder.input_text = input_text

        tool_name = kwargs.get("tool_name", "default")
        tool_args = kwargs.get("tool_args", {"input": input_text})
        if not isinstance(tool_args, dict):
            tool_args = {"input": str(tool_args)}

        try:
            result = await self._call_tool(str(tool_name), tool_args)
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self.name, f"MCP server call failed: {exc}") from exc

        self._process_result(result, str(tool_name), tool_args, builder)
        return builder.build()

    async def _call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call.
            tool_args: Arguments to pass to the tool.

        Returns:
            The raw tool result.

        Raises:
            AdapterError: If the server does not support tool calls.
        """
        if hasattr(self._server, "call_tool"):
            if asyncio.iscoroutinefunction(self._server.call_tool):
                return await self._server.call_tool(tool_name, tool_args)
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._server.call_tool(tool_name, tool_args),
            )

        raise AdapterError(self.name, "Server has no call_tool() method")

    def _process_result(
        self,
        result: Any,
        tool_name: str,
        tool_args: dict[str, Any],
        builder: Any,
    ) -> None:
        """Process the tool call result into the trace builder.

        Args:
            result: The raw result from the MCP server.
            tool_name: Name of the tool that was called.
            tool_args: Arguments that were passed to the tool.
            builder: The trace builder to populate.
        """
        if isinstance(result, dict):
            output_text = result.get("content", result.get("text", ""))
            is_error = result.get("isError", False)
        elif hasattr(result, "content"):
            content_parts = result.content if isinstance(result.content, list) else [result.content]
            output_text = " ".join(getattr(part, "text", str(part)) for part in content_parts)
            is_error = getattr(result, "isError", False)
        else:
            output_text = str(result)
            is_error = False

        builder.add_tool_call(
            ToolCall(
                tool_name=tool_name,
                tool_input=tool_args,
                tool_output=output_text,
                success=not is_error,
                error=str(output_text) if is_error else None,
            )
        )
        builder.output_text = str(output_text)

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools on the MCP server.

        Returns:
            A list of tool descriptions.

        Raises:
            AdapterError: If the server does not support listing tools.
        """
        if hasattr(self._server, "list_tools"):
            if asyncio.iscoroutinefunction(self._server.list_tools):
                result = await self._server.list_tools()
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, self._server.list_tools)
            if isinstance(result, list):
                return [self._normalize_tool_desc(t) for t in result]
            tools = getattr(result, "tools", [])
            return [self._normalize_tool_desc(t) for t in tools]

        raise AdapterError(self.name, "Server has no list_tools() method")

    @staticmethod
    def _normalize_tool_desc(tool: Any) -> dict[str, Any]:
        """Normalize a tool description to a standard dict format.

        Args:
            tool: A tool description object or dict.

        Returns:
            A normalized dict with name, description, and input_schema.
        """
        if isinstance(tool, dict):
            return {
                "name": tool.get("name", "unknown"),
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", tool.get("input_schema", {})),
            }
        return {
            "name": getattr(tool, "name", "unknown"),
            "description": getattr(tool, "description", ""),
            "input_schema": getattr(tool, "inputSchema", getattr(tool, "input_schema", {})),
        }
