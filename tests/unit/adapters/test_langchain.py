"""Tests for the LangChainAdapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from agentprobe.adapters.langchain import LangChainAdapter
from agentprobe.core.exceptions import AdapterError


@dataclass
class _FakeAction:
    """Simulates a LangChain AgentAction."""

    tool: str
    tool_input: dict[str, Any]
    log: str = ""


class _FakeAgent:
    """Simulates a LangChain AgentExecutor with async support."""

    def __init__(
        self,
        output: str = "test output",
        steps: list[Any] | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
        self._output = output
        self._steps = steps or []
        self._token_usage = token_usage

    async def ainvoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        result: dict[str, Any] = {
            "input": inputs.get("input", ""),
            "output": self._output,
            "intermediate_steps": self._steps,
        }
        if self._token_usage:
            result["token_usage"] = self._token_usage
        return result


class _SyncOnlyAgent:
    """Agent with only synchronous invoke."""

    def invoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return {"output": "sync result"}


class _BrokenAgent:
    """Agent that raises exceptions."""

    async def ainvoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        msg = "model overloaded"
        raise RuntimeError(msg)


class _NoInvokeAgent:
    """Agent without invoke methods."""

    pass


class TestLangChainAdapter:
    """Tests for LangChainAdapter invocation and trace building."""

    @pytest.mark.asyncio
    async def test_basic_invocation(self) -> None:
        agent = _FakeAgent(output="Hello there!")
        adapter = LangChainAdapter(agent, model_name="test-model")
        trace = await adapter.invoke("Hi")
        assert trace.output_text == "Hello there!"
        assert trace.agent_name == "langchain"

    @pytest.mark.asyncio
    async def test_intermediate_steps_extracted(self) -> None:
        steps = [
            (_FakeAction(tool="search", tool_input={"q": "test"}), "found it"),
            (_FakeAction(tool="calculate", tool_input={"expr": "1+1"}), "2"),
        ]
        agent = _FakeAgent(output="done", steps=steps)
        adapter = LangChainAdapter(agent)
        trace = await adapter.invoke("test")
        assert len(trace.tool_calls) == 2
        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[1].tool_name == "calculate"
        assert trace.tool_calls[1].tool_output == "2"

    @pytest.mark.asyncio
    async def test_token_usage_extracted(self) -> None:
        agent = _FakeAgent(
            output="result",
            token_usage={"prompt_tokens": 100, "completion_tokens": 50},
        )
        adapter = LangChainAdapter(agent, model_name="gpt-4o")
        trace = await adapter.invoke("test")
        assert len(trace.llm_calls) == 1
        assert trace.llm_calls[0].input_tokens == 100
        assert trace.llm_calls[0].output_tokens == 50

    @pytest.mark.asyncio
    async def test_sync_fallback(self) -> None:
        agent = _SyncOnlyAgent()
        adapter = LangChainAdapter(agent)
        trace = await adapter.invoke("test")
        assert trace.output_text == "sync result"

    @pytest.mark.asyncio
    async def test_broken_agent_raises_adapter_error(self) -> None:
        agent = _BrokenAgent()
        adapter = LangChainAdapter(agent)
        with pytest.raises(AdapterError, match="model overloaded"):
            await adapter.invoke("test")

    @pytest.mark.asyncio
    async def test_no_invoke_raises_adapter_error(self) -> None:
        agent = _NoInvokeAgent()
        adapter = LangChainAdapter(agent)
        with pytest.raises(AdapterError, match="neither invoke"):
            await adapter.invoke("test")

    @pytest.mark.asyncio
    async def test_custom_name(self) -> None:
        agent = _FakeAgent()
        adapter = LangChainAdapter(agent, name="my-agent")
        trace = await adapter.invoke("test")
        assert trace.agent_name == "my-agent"

    @pytest.mark.asyncio
    async def test_string_result(self) -> None:
        """Test handling when agent returns a plain string."""

        class _StringAgent:
            async def ainvoke(self, inputs: dict[str, Any], **kwargs: Any) -> str:
                return "plain string"

        adapter = LangChainAdapter(_StringAgent())
        trace = await adapter.invoke("test")
        assert trace.output_text == "plain string"
