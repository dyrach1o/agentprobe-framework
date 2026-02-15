"""Tests for the OpenAIAgentsAdapter."""

from __future__ import annotations

import sys
import types
from typing import Any
from unittest.mock import patch

import pytest

from agentprobe.adapters.openai_agents import OpenAIAgentsAdapter
from agentprobe.core.exceptions import AdapterError


class _FakeUsage:
    """Simulates token usage from a model response."""

    def __init__(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeResponse:
    """Simulates a raw model response with usage data."""

    def __init__(self, usage: _FakeUsage | None = None) -> None:
        self.usage = usage


class _FakeToolCallItem:
    """Simulates a ToolCallItem from the Agents SDK run items."""

    def __init__(
        self,
        tool_name: str,
        arguments: dict[str, Any] | str | None = None,
        output: Any = None,
    ) -> None:
        self.tool_name = tool_name
        self.arguments = arguments
        self.output = output


class _FakeRunResult:
    """Simulates a RunResult from the Agents SDK."""

    def __init__(
        self,
        final_output: str = "agent result",
        new_items: list[Any] | None = None,
        raw_responses: list[Any] | None = None,
    ) -> None:
        self.final_output = final_output
        self.new_items = new_items or []
        self.raw_responses = raw_responses or []


class _FakeAgent:
    """Simulates an OpenAI Agents SDK Agent."""

    def __init__(self, model: str | None = "gpt-4o") -> None:
        self.model = model


class _FakeRunner:
    """Simulates the Agents SDK Runner with async run()."""

    _result: _FakeRunResult = _FakeRunResult()

    @classmethod
    async def run(cls, agent: Any, input: str = "", **kwargs: Any) -> _FakeRunResult:
        return cls._result


class _BrokenRunner:
    """Runner that raises exceptions on run()."""

    @classmethod
    async def run(cls, agent: Any, input: str = "", **kwargs: Any) -> Any:
        msg = "agent execution failed"
        raise RuntimeError(msg)


def _make_agents_module(runner_cls: type) -> types.ModuleType:
    """Create a fake 'agents' module with the given Runner class."""
    mod = types.ModuleType("agents")
    mod.Runner = runner_cls  # type: ignore[attr-defined]
    return mod


class TestOpenAIAgentsAdapter:
    """Tests for OpenAIAgentsAdapter."""

    async def test_basic_invocation(self) -> None:
        agent = _FakeAgent()
        result = _FakeRunResult(final_output="Hello from agent!")
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent, model_name="gpt-4o")

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test input")

        assert trace.output_text == "Hello from agent!"
        assert trace.agent_name == "openai-agents"

    async def test_tool_calls_extracted(self) -> None:
        agent = _FakeAgent()
        items = [
            _FakeToolCallItem(tool_name="search", arguments={"q": "test"}, output="found it"),
            _FakeToolCallItem(tool_name="write", arguments={"text": "hello"}, output="ok"),
        ]
        result = _FakeRunResult(final_output="done", new_items=items)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent)

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert len(trace.tool_calls) == 2
        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[0].tool_input == {"q": "test"}
        assert trace.tool_calls[0].tool_output == "found it"
        assert trace.tool_calls[1].tool_name == "write"

    async def test_token_usage_extracted(self) -> None:
        agent = _FakeAgent(model="gpt-4o")
        responses = [
            _FakeResponse(usage=_FakeUsage(input_tokens=150, output_tokens=75)),
        ]
        result = _FakeRunResult(final_output="result", raw_responses=responses)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent, model_name="gpt-4o")

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert len(trace.llm_calls) == 1
        assert trace.llm_calls[0].input_tokens == 150
        assert trace.llm_calls[0].output_tokens == 75
        assert trace.total_input_tokens == 150
        assert trace.total_output_tokens == 75

    async def test_multiple_responses_aggregated(self) -> None:
        agent = _FakeAgent()
        responses = [
            _FakeResponse(usage=_FakeUsage(input_tokens=100, output_tokens=50)),
            _FakeResponse(usage=_FakeUsage(input_tokens=200, output_tokens=100)),
        ]
        result = _FakeRunResult(final_output="result", raw_responses=responses)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent, model_name="gpt-4o")

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert len(trace.llm_calls) == 2
        assert trace.total_input_tokens == 300
        assert trace.total_output_tokens == 150

    async def test_broken_runner_raises_adapter_error(self) -> None:
        agent = _FakeAgent()
        fake_module = _make_agents_module(_BrokenRunner)

        adapter = OpenAIAgentsAdapter(agent)

        with (
            patch.dict(sys.modules, {"agents": fake_module}),
            pytest.raises(AdapterError, match="agent execution failed"),
        ):
            await adapter.invoke("test")

    async def test_custom_name(self) -> None:
        agent = _FakeAgent()
        result = _FakeRunResult(final_output="hi")
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent, name="my-agent")

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert trace.agent_name == "my-agent"

    async def test_string_result_fallback(self) -> None:
        """Test handling when result has no final_output attribute."""
        agent = _FakeAgent()

        class _StringResult:
            pass

        string_result = _StringResult()

        class _StringRunner:
            @classmethod
            async def run(cls, agent: Any, input: str = "", **kwargs: Any) -> Any:
                return string_result

        fake_module = _make_agents_module(_StringRunner)

        adapter = OpenAIAgentsAdapter(agent)

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert trace.output_text == str(string_result)

    async def test_model_from_agent(self) -> None:
        """Test that model name is resolved from agent when not provided."""
        agent = _FakeAgent(model="gpt-4o-mini")
        responses = [
            _FakeResponse(usage=_FakeUsage(input_tokens=10, output_tokens=5)),
        ]
        result = _FakeRunResult(final_output="result", raw_responses=responses)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent)

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert trace.model == "gpt-4o-mini"
        assert trace.llm_calls[0].model == "gpt-4o-mini"

    async def test_non_dict_tool_arguments(self) -> None:
        """Test handling of non-dict tool arguments."""
        agent = _FakeAgent()
        items = [
            _FakeToolCallItem(tool_name="run", arguments="raw args string", output="ok"),
        ]
        result = _FakeRunResult(final_output="done", new_items=items)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent)

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert trace.tool_calls[0].tool_input == {"input": "raw args string"}

    async def test_items_without_tool_name_skipped(self) -> None:
        """Test that run items without tool_name are not treated as tool calls."""
        agent = _FakeAgent()

        class _MessageItem:
            """A non-tool run item."""

            def __init__(self) -> None:
                self.content = "some message"

        items = [
            _MessageItem(),
            _FakeToolCallItem(tool_name="search", arguments={}, output="found"),
        ]
        result = _FakeRunResult(final_output="done", new_items=items)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent)

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert len(trace.tool_calls) == 1
        assert trace.tool_calls[0].tool_name == "search"

    async def test_response_without_usage_skipped(self) -> None:
        """Test that responses without usage data do not create LLM calls."""
        agent = _FakeAgent()
        responses = [
            _FakeResponse(usage=None),
            _FakeResponse(usage=_FakeUsage(input_tokens=50, output_tokens=25)),
        ]
        result = _FakeRunResult(final_output="done", raw_responses=responses)
        _FakeRunner._result = result
        fake_module = _make_agents_module(_FakeRunner)

        adapter = OpenAIAgentsAdapter(agent, model_name="gpt-4o")

        with patch.dict(sys.modules, {"agents": fake_module}):
            trace = await adapter.invoke("test")

        assert len(trace.llm_calls) == 1
        assert trace.llm_calls[0].input_tokens == 50
