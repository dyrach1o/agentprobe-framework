"""Tests for the GeminiAdapter."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.adapters.gemini import GeminiAdapter
from agentprobe.core.exceptions import AdapterError


class _FakeUsageMetadata:
    """Simulates Gemini usage_metadata from a response."""

    def __init__(self, prompt_token_count: int = 0, candidates_token_count: int = 0) -> None:
        self.prompt_token_count = prompt_token_count
        self.candidates_token_count = candidates_token_count


class _FakeFunctionCall:
    """Simulates a Gemini function call in a response part."""

    def __init__(self, name: str, args: dict[str, Any] | None = None) -> None:
        self.name = name
        self.args = args


class _FakePart:
    """Simulates a response part (text or function call)."""

    def __init__(
        self,
        text: str | None = None,
        function_call: _FakeFunctionCall | None = None,
    ) -> None:
        self.text = text
        self.function_call = function_call


class _FakeContent:
    """Simulates candidate content with parts."""

    def __init__(self, parts: list[_FakePart] | None = None) -> None:
        self.parts = parts or []


class _FakeCandidate:
    """Simulates a response candidate."""

    def __init__(self, content: _FakeContent | None = None) -> None:
        self.content = content


class _FakeResponse:
    """Simulates a Gemini GenerateContentResponse."""

    def __init__(
        self,
        text: str | None = "model output",
        candidates: list[_FakeCandidate] | None = None,
        usage_metadata: _FakeUsageMetadata | None = None,
    ) -> None:
        self.text = text
        self.candidates = candidates or []
        self.usage_metadata = usage_metadata


class _FakeModel:
    """Simulates a Gemini GenerativeModel with async support."""

    def __init__(
        self,
        response: _FakeResponse | None = None,
        model_name: str | None = "gemini-1.5-pro",
    ) -> None:
        self._response = response or _FakeResponse()
        self.model_name = model_name

    async def generate_content_async(self, prompt: str, **kwargs: Any) -> _FakeResponse:
        return self._response


class _SyncModel:
    """Model with only synchronous generate_content."""

    def __init__(self, response: _FakeResponse | None = None) -> None:
        self._response = response or _FakeResponse()
        self.model_name = "gemini-1.5-flash"

    def generate_content(self, prompt: str, **kwargs: Any) -> _FakeResponse:
        return self._response


class _BrokenModel:
    """Model that raises exceptions."""

    model_name = "gemini-broken"

    async def generate_content_async(self, prompt: str, **kwargs: Any) -> Any:
        msg = "model overloaded"
        raise RuntimeError(msg)


class _NoMethodModel:
    """Model without generation methods."""

    model_name = "gemini-none"


class TestGeminiAdapter:
    """Tests for GeminiAdapter."""

    async def test_basic_invocation(self) -> None:
        model = _FakeModel(response=_FakeResponse(text="Hello from Gemini!"))
        adapter = GeminiAdapter(model, model_name="gemini-1.5-pro")
        trace = await adapter.invoke("test input")
        assert trace.output_text == "Hello from Gemini!"
        assert trace.agent_name == "gemini"

    async def test_token_usage_extracted(self) -> None:
        usage = _FakeUsageMetadata(prompt_token_count=200, candidates_token_count=100)
        response = _FakeResponse(text="result", usage_metadata=usage)
        model = _FakeModel(response=response)
        adapter = GeminiAdapter(model, model_name="gemini-1.5-pro")

        trace = await adapter.invoke("test")

        assert len(trace.llm_calls) == 1
        assert trace.llm_calls[0].input_tokens == 200
        assert trace.llm_calls[0].output_tokens == 100
        assert trace.total_input_tokens == 200
        assert trace.total_output_tokens == 100

    async def test_function_calls_extracted(self) -> None:
        fc1 = _FakeFunctionCall(name="search", args={"query": "test"})
        fc2 = _FakeFunctionCall(name="calculate", args={"expr": "1+1"})
        parts = [_FakePart(function_call=fc1), _FakePart(function_call=fc2)]
        candidate = _FakeCandidate(content=_FakeContent(parts=parts))
        response = _FakeResponse(text="done", candidates=[candidate])
        model = _FakeModel(response=response)
        adapter = GeminiAdapter(model)

        trace = await adapter.invoke("test")

        assert len(trace.tool_calls) == 2
        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[0].tool_input == {"query": "test"}
        assert trace.tool_calls[1].tool_name == "calculate"

    async def test_sync_fallback(self) -> None:
        model = _SyncModel(response=_FakeResponse(text="sync result"))
        adapter = GeminiAdapter(model)

        trace = await adapter.invoke("test")
        assert trace.output_text == "sync result"

    async def test_broken_model_raises_adapter_error(self) -> None:
        adapter = GeminiAdapter(_BrokenModel())
        with pytest.raises(AdapterError, match="model overloaded"):
            await adapter.invoke("test")

    async def test_no_method_raises_adapter_error(self) -> None:
        adapter = GeminiAdapter(_NoMethodModel())
        with pytest.raises(AdapterError, match="neither generate_content"):
            await adapter.invoke("test")

    async def test_custom_name(self) -> None:
        model = _FakeModel()
        adapter = GeminiAdapter(model, name="my-gemini")
        trace = await adapter.invoke("test")
        assert trace.agent_name == "my-gemini"

    async def test_model_name_from_model_object(self) -> None:
        model = _FakeModel(model_name="gemini-2.0-flash")
        usage = _FakeUsageMetadata(prompt_token_count=10, candidates_token_count=5)
        model._response = _FakeResponse(text="hi", usage_metadata=usage)
        adapter = GeminiAdapter(model)

        trace = await adapter.invoke("test")

        assert trace.model == "gemini-2.0-flash"
        assert trace.llm_calls[0].model == "gemini-2.0-flash"

    async def test_text_from_candidates_fallback(self) -> None:
        """When response.text is None, extract from candidates."""
        part = _FakePart(text="candidate text")
        candidate = _FakeCandidate(content=_FakeContent(parts=[part]))
        response = _FakeResponse(text=None, candidates=[candidate])
        model = _FakeModel(response=response)
        adapter = GeminiAdapter(model)

        trace = await adapter.invoke("test")
        assert trace.output_text == "candidate text"

    async def test_no_usage_metadata(self) -> None:
        """Responses without usage_metadata produce no LLM calls."""
        response = _FakeResponse(text="result", usage_metadata=None)
        model = _FakeModel(response=response)
        adapter = GeminiAdapter(model, model_name="gemini-1.5-pro")

        trace = await adapter.invoke("test")
        assert len(trace.llm_calls) == 0

    async def test_mixed_parts_text_and_function_call(self) -> None:
        """Parts can contain both text and function calls."""
        parts = [
            _FakePart(text="thinking..."),
            _FakePart(function_call=_FakeFunctionCall(name="lookup", args={"id": 42})),
        ]
        candidate = _FakeCandidate(content=_FakeContent(parts=parts))
        response = _FakeResponse(text="thinking...", candidates=[candidate])
        model = _FakeModel(response=response)
        adapter = GeminiAdapter(model)

        trace = await adapter.invoke("test")

        assert trace.output_text == "thinking..."
        assert len(trace.tool_calls) == 1
        assert trace.tool_calls[0].tool_name == "lookup"

    async def test_function_call_without_args(self) -> None:
        """Function calls with no args produce empty tool_input."""
        fc = _FakeFunctionCall(name="get_time", args=None)
        part = _FakePart(function_call=fc)
        candidate = _FakeCandidate(content=_FakeContent(parts=[part]))
        response = _FakeResponse(text="done", candidates=[candidate])
        model = _FakeModel(response=response)
        adapter = GeminiAdapter(model)

        trace = await adapter.invoke("test")

        assert trace.tool_calls[0].tool_input == {}
