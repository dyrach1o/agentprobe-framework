"""Tests for the AutoGenAdapter."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.adapters.autogen import AutoGenAdapter
from agentprobe.core.exceptions import AdapterError


class _FakeAgent:
    """Simulates an AutoGen AssistantAgent with chat history."""

    def __init__(self, messages: list[dict[str, Any]] | None = None) -> None:
        self.chat_messages: dict[str, list[dict[str, Any]]] = {
            "user_proxy": messages or [],
        }


class _FakeUserProxy:
    """Simulates an AutoGen UserProxyAgent."""

    def __init__(self, agent: _FakeAgent | None = None) -> None:
        self._agent = agent

    async def a_initiate_chat(self, agent: Any, message: str = "", **kwargs: Any) -> None:
        pass


class _SyncUserProxy:
    """UserProxy with only synchronous initiate_chat."""

    def initiate_chat(self, agent: Any, message: str = "", **kwargs: Any) -> None:
        pass


class _BrokenUserProxy:
    """UserProxy that raises exceptions."""

    async def a_initiate_chat(self, agent: Any, **kwargs: Any) -> None:
        msg = "connection failed"
        raise RuntimeError(msg)


class _NoInitiateProxy:
    """UserProxy without initiate methods."""


class TestAutoGenAdapter:
    """Tests for AutoGenAdapter."""

    async def test_basic_invocation(self) -> None:
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        agent = _FakeAgent(messages)
        proxy = _FakeUserProxy()
        adapter = AutoGenAdapter(agent, proxy, model_name="test-model")

        trace = await adapter.invoke("hello")
        assert trace.output_text == "Hi there!"
        assert trace.agent_name == "autogen"

    async def test_function_call_extracted(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": "Let me search.",
                "function_call": {"name": "search", "arguments": {"q": "test"}},
            },
            {"role": "function", "name": "search", "content": "results found"},
            {"role": "assistant", "content": "Found it."},
        ]
        agent = _FakeAgent(messages)
        proxy = _FakeUserProxy()
        adapter = AutoGenAdapter(agent, proxy)

        trace = await adapter.invoke("search for test")

        assert len(trace.tool_calls) == 2
        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[0].tool_input == {"q": "test"}
        assert trace.tool_calls[1].tool_name == "search"
        assert trace.tool_calls[1].tool_output == "results found"

    async def test_tool_calls_extracted(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "calc", "arguments": {"expr": "1+1"}}},
                ],
            },
            {"role": "tool", "name": "calc", "content": "2"},
            {"role": "assistant", "content": "The answer is 2."},
        ]
        agent = _FakeAgent(messages)
        proxy = _FakeUserProxy()
        adapter = AutoGenAdapter(agent, proxy)

        trace = await adapter.invoke("calculate 1+1")

        assert trace.output_text == "The answer is 2."
        tool_names = [tc.tool_name for tc in trace.tool_calls]
        assert "calc" in tool_names

    async def test_sync_fallback(self) -> None:
        agent = _FakeAgent([{"role": "assistant", "content": "sync result"}])
        proxy = _SyncUserProxy()
        adapter = AutoGenAdapter(agent, proxy)

        trace = await adapter.invoke("test")
        assert trace.output_text == "sync result"

    async def test_broken_proxy_raises_adapter_error(self) -> None:
        agent = _FakeAgent()
        proxy = _BrokenUserProxy()
        adapter = AutoGenAdapter(agent, proxy)

        with pytest.raises(AdapterError, match="connection failed"):
            await adapter.invoke("test")

    async def test_no_initiate_raises_adapter_error(self) -> None:
        agent = _FakeAgent()
        proxy = _NoInitiateProxy()
        adapter = AutoGenAdapter(agent, proxy)

        with pytest.raises(AdapterError, match="neither initiate_chat"):
            await adapter.invoke("test")

    async def test_custom_name(self) -> None:
        agent = _FakeAgent([{"role": "assistant", "content": "hi"}])
        proxy = _FakeUserProxy()
        adapter = AutoGenAdapter(agent, proxy, name="my-autogen")

        trace = await adapter.invoke("test")
        assert trace.agent_name == "my-autogen"

    async def test_empty_messages(self) -> None:
        agent = _FakeAgent([])
        proxy = _FakeUserProxy()
        adapter = AutoGenAdapter(agent, proxy)

        trace = await adapter.invoke("test")
        assert trace.output_text == ""
        assert len(trace.tool_calls) == 0

    async def test_non_dict_function_args(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": "calling",
                "function_call": {"name": "run", "arguments": "raw args"},
            },
            {"role": "assistant", "content": "done"},
        ]
        agent = _FakeAgent(messages)
        proxy = _FakeUserProxy()
        adapter = AutoGenAdapter(agent, proxy)

        trace = await adapter.invoke("test")
        assert trace.tool_calls[0].tool_input == {"input": "raw args"}
