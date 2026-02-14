"""Tests for the BaseAdapter abstract base class and _TraceBuilder."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.adapters.base import BaseAdapter, _TraceBuilder
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import LLMCall, ToolCall, Trace, TurnType


class _EchoAdapter(BaseAdapter):
    """Concrete adapter that echoes input back as output."""

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        builder = self._create_builder()
        builder.input_text = input_text
        builder.add_llm_call(
            LLMCall(
                model="echo-model",
                input_tokens=len(input_text),
                output_tokens=len(input_text),
                input_text=input_text,
                output_text=input_text,
            )
        )
        builder.output_text = input_text
        return builder.build()


class _BrokenAdapter(BaseAdapter):
    """Concrete adapter that always fails."""

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        msg = "connection refused"
        raise ConnectionError(msg)


class _DirectAdapterError(BaseAdapter):
    """Concrete adapter that raises AdapterError directly."""

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        raise AdapterError(self.name, "explicit adapter error")


class TestTraceBuilder:
    """Tests for the _TraceBuilder helper."""

    def test_build_empty_trace(self) -> None:
        builder = _TraceBuilder("agent1")
        trace = builder.build()
        assert trace.agent_name == "agent1"
        assert trace.llm_calls == ()
        assert trace.tool_calls == ()
        assert trace.model is None

    def test_add_llm_call(self) -> None:
        builder = _TraceBuilder("agent1")
        call = LLMCall(model="test-model", input_tokens=10, output_tokens=5)
        builder.add_llm_call(call)
        trace = builder.build()
        assert len(trace.llm_calls) == 1
        assert len(trace.turns) == 1
        assert trace.turns[0].turn_type == TurnType.LLM_CALL
        assert trace.model == "test-model"
        assert trace.total_input_tokens == 10

    def test_add_tool_call(self) -> None:
        builder = _TraceBuilder("agent1")
        call = ToolCall(tool_name="search", tool_output="found it")
        builder.add_tool_call(call)
        trace = builder.build()
        assert len(trace.tool_calls) == 1
        assert len(trace.turns) == 1
        assert trace.turns[0].turn_type == TurnType.TOOL_CALL

    def test_model_inferred_from_first_call(self) -> None:
        builder = _TraceBuilder("agent1")
        builder.add_llm_call(LLMCall(model="model-a"))
        builder.add_llm_call(LLMCall(model="model-b"))
        trace = builder.build()
        assert trace.model == "model-a"

    def test_explicit_model_not_overridden(self) -> None:
        builder = _TraceBuilder("agent1", model="explicit-model")
        builder.add_llm_call(LLMCall(model="other"))
        trace = builder.build()
        assert trace.model == "explicit-model"


class TestBaseAdapter:
    """Tests for BaseAdapter template method."""

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            BaseAdapter("test")  # type: ignore[abstract]

    def test_name_property(self) -> None:
        adapter = _EchoAdapter("echo")
        assert adapter.name == "echo"

    @pytest.mark.asyncio
    async def test_successful_invocation(self) -> None:
        adapter = _EchoAdapter("echo")
        trace = await adapter.invoke("hello")
        assert trace.agent_name == "echo"
        assert trace.output_text == "hello"
        assert len(trace.llm_calls) == 1
        assert trace.total_input_tokens == 5

    @pytest.mark.asyncio
    async def test_generic_exception_wrapped_as_adapter_error(self) -> None:
        adapter = _BrokenAdapter("broken")
        with pytest.raises(AdapterError, match="connection refused"):
            await adapter.invoke("test")

    @pytest.mark.asyncio
    async def test_adapter_error_propagates_directly(self) -> None:
        adapter = _DirectAdapterError("direct")
        with pytest.raises(AdapterError, match="explicit adapter error"):
            await adapter.invoke("test")
