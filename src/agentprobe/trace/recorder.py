"""Trace recorder: captures agent execution events into structured Traces.

Provides an async context manager for recording LLM calls, tool
invocations, and message exchanges during agent execution.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from agentprobe.core.exceptions import TraceError
from agentprobe.core.models import LLMCall, ToolCall, Trace, Turn, TurnType

logger = logging.getLogger(__name__)


class TraceRecordingContext:
    """Mutable context for recording events during an agent run.

    Accumulates LLM calls, tool calls, and turns that will be
    assembled into a frozen Trace by ``TraceRecorder.finalize()``.
    """

    def __init__(self, agent_name: str, model: str | None = None) -> None:
        self.agent_name = agent_name
        self.model = model
        self.llm_calls: list[LLMCall] = []
        self.tool_calls: list[ToolCall] = []
        self.turns: list[Turn] = []
        self.tags: list[str] = []
        self.metadata: dict[str, Any] = {}
        self._start_time = time.monotonic()

    def record_llm_call(
        self,
        *,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        input_text: str = "",
        output_text: str = "",
        latency_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> LLMCall:
        """Record an LLM call event.

        Args:
            model: Model identifier.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            input_text: Prompt text.
            output_text: Response text.
            latency_ms: Call latency in milliseconds.
            metadata: Additional metadata.

        Returns:
            The recorded LLMCall object.
        """
        call = LLMCall(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_text=input_text,
            output_text=output_text,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )
        self.llm_calls.append(call)
        self.turns.append(Turn(turn_type=TurnType.LLM_CALL, content=output_text, llm_call=call))
        if self.model is None:
            self.model = model
        return call

    def record_tool_call(
        self,
        *,
        tool_name: str,
        tool_input: dict[str, Any] | None = None,
        tool_output: Any = None,
        success: bool = True,
        error: str | None = None,
        latency_ms: int = 0,
    ) -> ToolCall:
        """Record a tool call event.

        Args:
            tool_name: Name of the tool.
            tool_input: Arguments passed to the tool.
            tool_output: Output from the tool.
            success: Whether the call succeeded.
            error: Error message if failed.
            latency_ms: Call latency in milliseconds.

        Returns:
            The recorded ToolCall object.
        """
        call = ToolCall(
            tool_name=tool_name,
            tool_input=tool_input or {},
            tool_output=tool_output,
            success=success,
            error=error,
            latency_ms=latency_ms,
        )
        self.tool_calls.append(call)
        self.turns.append(
            Turn(
                turn_type=TurnType.TOOL_CALL,
                content=str(tool_output) if tool_output is not None else "",
                tool_call=call,
            )
        )
        return call

    @property
    def elapsed_ms(self) -> int:
        """Return elapsed time since recording started."""
        return int((time.monotonic() - self._start_time) * 1000)


class TraceRecorder:
    """Records agent execution events into a structured Trace.

    Use as an async context manager via ``recording()`` to capture
    events, then call ``finalize()`` to produce the frozen Trace.

    Attributes:
        agent_name: Name of the agent being recorded.
        model: Primary model being used.
        tags: Optional tags for filtering.

    Example:
        ```python
        recorder = TraceRecorder(agent_name="support")

        async with recorder.recording() as ctx:
            ctx.record_llm_call(model="claude-sonnet-4-5-20250929", ...)
            ctx.record_tool_call(tool_name="search", ...)

        trace = recorder.finalize(output="Done")
        ```
    """

    def __init__(
        self,
        agent_name: str,
        model: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Initialize a new trace recorder.

        Args:
            agent_name: Identifier for the agent being recorded.
            model: Primary model name.
            tags: Optional tags for categorization.

        Raises:
            ValueError: If agent_name is empty.
        """
        if not agent_name:
            msg = "agent_name must not be empty"
            raise ValueError(msg)
        self._agent_name = agent_name
        self._model = model
        self._tags = tags or []
        self._context: TraceRecordingContext | None = None

    @asynccontextmanager
    async def recording(self) -> AsyncGenerator[TraceRecordingContext, None]:
        """Start a recording session.

        Yields a TraceRecordingContext for recording events.

        Yields:
            A mutable recording context.
        """
        self._context = TraceRecordingContext(
            agent_name=self._agent_name,
            model=self._model,
        )
        self._context.tags = list(self._tags)
        logger.debug("Started recording for agent '%s'", self._agent_name)
        try:
            yield self._context
        except Exception:
            logger.exception("Error during recording for agent '%s'", self._agent_name)
            raise
        finally:
            logger.debug(
                "Recording ended for agent '%s': %d LLM calls, %d tool calls",
                self._agent_name,
                len(self._context.llm_calls),
                len(self._context.tool_calls),
            )

    def finalize(
        self,
        *,
        input_text: str = "",
        output: str = "",
    ) -> Trace:
        """Produce a frozen Trace from the recorded events.

        Args:
            input_text: The input given to the agent.
            output: The final output from the agent.

        Returns:
            An immutable Trace object.

        Raises:
            TraceError: If no recording session was started.
        """
        if self._context is None:
            raise TraceError("No recording session — call recording() first")

        ctx = self._context
        total_input = sum(c.input_tokens for c in ctx.llm_calls)
        total_output = sum(c.output_tokens for c in ctx.llm_calls)

        trace = Trace(
            agent_name=ctx.agent_name,
            model=ctx.model,
            input_text=input_text,
            output_text=output,
            turns=tuple(ctx.turns),
            llm_calls=tuple(ctx.llm_calls),
            tool_calls=tuple(ctx.tool_calls),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_latency_ms=ctx.elapsed_ms,
            tags=tuple(ctx.tags),
            metadata=ctx.metadata,
            created_at=datetime.now(UTC),
        )

        self._context = None
        return trace
