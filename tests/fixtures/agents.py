"""Mock adapter for testing without real agent frameworks."""

from __future__ import annotations

import asyncio
from typing import Any

from agentprobe.core.models import LLMCall, ToolCall, Trace


class MockAdapter:
    """A configurable mock adapter for testing.

    Can simulate various agent behaviors including tool calls,
    delays, and failures.

    Attributes:
        call_count: Number of times invoke was called.
    """

    def __init__(
        self,
        *,
        name: str = "mock",
        output: str = "mock output",
        tool_calls: list[ToolCall] | None = None,
        llm_calls: list[LLMCall] | None = None,
        delay: float = 0.0,
        error: Exception | None = None,
    ) -> None:
        """Initialize the mock adapter.

        Args:
            name: Adapter name.
            output: Default output text.
            tool_calls: Tool calls to include in traces.
            llm_calls: LLM calls to include in traces.
            delay: Simulated execution delay in seconds.
            error: If set, raise this error on invoke.
        """
        self._name = name
        self._output = output
        self._tool_calls = tool_calls or []
        self._llm_calls = llm_calls or []
        self._delay = delay
        self._error = error
        self.call_count = 0
        self.last_input: str | None = None

    @property
    def name(self) -> str:
        """Return the adapter name."""
        return self._name

    async def invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the mock adapter.

        Args:
            input_text: Input text.
            **kwargs: Ignored.

        Returns:
            A trace with configured mock data.

        Raises:
            Exception: The configured error, if any.
        """
        self.call_count += 1
        self.last_input = input_text

        if self._delay > 0:
            await asyncio.sleep(self._delay)

        if self._error is not None:
            raise self._error

        return Trace(
            agent_name=self._name,
            input_text=input_text,
            output_text=self._output,
            llm_calls=tuple(self._llm_calls),
            tool_calls=tuple(self._tool_calls),
            total_input_tokens=sum(c.input_tokens for c in self._llm_calls),
            total_output_tokens=sum(c.output_tokens for c in self._llm_calls),
        )
