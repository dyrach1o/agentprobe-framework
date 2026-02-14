"""Abstract base adapter with trace-building helper.

Subclasses implement ``_invoke()`` while the base class provides
a ``_TraceBuilder`` for accumulating mutable state before producing
a frozen ``Trace``.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import LLMCall, ToolCall, Trace, Turn, TurnType

logger = logging.getLogger(__name__)


class _TraceBuilder:
    """Mutable helper for assembling a frozen Trace.

    Accumulates LLM calls, tool calls, and turns during agent execution,
    then produces an immutable Trace via ``build()``.
    """

    def __init__(self, agent_name: str, model: str | None = None) -> None:
        self.agent_name = agent_name
        self.model = model
        self.llm_calls: list[LLMCall] = []
        self.tool_calls: list[ToolCall] = []
        self.turns: list[Turn] = []
        self.input_text: str = ""
        self.output_text: str = ""
        self.tags: list[str] = []
        self.metadata: dict[str, Any] = {}
        self._start_time: float = time.monotonic()

    def add_llm_call(self, call: LLMCall) -> None:
        """Record an LLM call and create a corresponding turn."""
        self.llm_calls.append(call)
        self.turns.append(
            Turn(
                turn_type=TurnType.LLM_CALL,
                content=call.output_text,
                llm_call=call,
            )
        )
        if self.model is None:
            self.model = call.model

    def add_tool_call(self, call: ToolCall) -> None:
        """Record a tool call and create a corresponding turn."""
        self.tool_calls.append(call)
        self.turns.append(
            Turn(
                turn_type=TurnType.TOOL_CALL,
                content=str(call.tool_output) if call.tool_output is not None else "",
                tool_call=call,
            )
        )

    def build(self) -> Trace:
        """Produce an immutable Trace from accumulated state."""
        total_input = sum(c.input_tokens for c in self.llm_calls)
        total_output = sum(c.output_tokens for c in self.llm_calls)
        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)

        return Trace(
            agent_name=self.agent_name,
            model=self.model,
            input_text=self.input_text,
            output_text=self.output_text,
            turns=tuple(self.turns),
            llm_calls=tuple(self.llm_calls),
            tool_calls=tuple(self.tool_calls),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_latency_ms=elapsed_ms,
            tags=tuple(self.tags),
            metadata=self.metadata,
            created_at=datetime.now(UTC),
        )


class BaseAdapter(ABC):
    """Abstract base class for agent framework adapters.

    Provides a public ``invoke()`` method that wraps ``_invoke()``
    with error handling and logging.

    Attributes:
        _name: The adapter's name.
    """

    def __init__(self, name: str) -> None:
        """Initialize the adapter.

        Args:
            name: A unique name identifying this adapter instance.
        """
        self._name = name

    @property
    def name(self) -> str:
        """Return the adapter name."""
        return self._name

    def _create_builder(self, model: str | None = None) -> _TraceBuilder:
        """Create a new trace builder for this adapter.

        Args:
            model: Optional primary model name.

        Returns:
            A mutable trace builder instance.
        """
        return _TraceBuilder(agent_name=self._name, model=model)

    async def invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the agent and return a trace.

        Wraps ``_invoke()`` with error handling and logging.

        Args:
            input_text: The input prompt to send to the agent.
            **kwargs: Additional adapter-specific arguments.

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the agent invocation fails.
        """
        logger.info("Invoking adapter '%s' with input length %d", self._name, len(input_text))
        try:
            trace = await self._invoke(input_text, **kwargs)
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self._name, str(exc)) from exc
        else:
            logger.info(
                "Adapter '%s' completed: %d LLM calls, %d tool calls",
                self._name,
                len(trace.llm_calls),
                len(trace.tool_calls),
            )
            return trace

    @abstractmethod
    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Perform the actual agent invocation.

        Subclasses must implement this method.

        Args:
            input_text: The input prompt to send to the agent.
            **kwargs: Additional adapter-specific arguments.

        Returns:
            A complete execution trace.
        """
        ...
