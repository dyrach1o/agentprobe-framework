"""OpenAI Agents SDK adapter.

Wraps an OpenAI Agents SDK Agent and translates its execution into
AgentProbe's Trace format by extracting tool calls from run items
and token usage from raw model responses.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import LLMCall, ToolCall, Trace

logger = logging.getLogger(__name__)


class OpenAIAgentsAdapter(BaseAdapter):
    """Adapter for OpenAI Agents SDK (openai-agents).

    Captures tool calls from run items and token usage from raw model
    responses to build a complete execution trace.

    Attributes:
        _agent: The OpenAI Agents SDK Agent object.
        _model_name: Optional model name for trace records.
    """

    def __init__(
        self,
        agent: Any,
        *,
        name: str = "openai-agents",
        model_name: str | None = None,
    ) -> None:
        """Initialize the OpenAI Agents SDK adapter.

        Args:
            agent: An OpenAI Agents SDK Agent object.
            name: Adapter name for identification.
            model_name: Model name to record in traces.
        """
        super().__init__(name)
        self._agent = agent
        self._model_name = model_name

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the OpenAI Agents SDK agent and build a trace.

        Attempts async ``Runner.run()`` first, then falls back to
        ``Runner.run_sync()`` in an executor if async is not available.

        Args:
            input_text: The input prompt.
            **kwargs: Passed through to the runner.

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the agent invocation fails.
        """
        resolved_model = self._model_name or getattr(self._agent, "model", None)
        builder = self._create_builder(model=resolved_model)
        builder.input_text = input_text

        try:
            from agents import Runner  # noqa: PLC0415
        except ImportError as exc:
            raise AdapterError(
                self.name,
                "openai-agents package is not installed",
            ) from exc

        try:
            if hasattr(Runner, "run"):
                result = await Runner.run(self._agent, input=input_text, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: Runner.run_sync(self._agent, input=input_text),
                )
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self.name, f"Agent run failed: {exc}") from exc

        self._extract_result(result, builder)
        return builder.build()

    def _extract_result(self, result: Any, builder: Any) -> None:
        """Extract output, tool calls, and token usage from the run result.

        Args:
            result: The raw RunResult from the Agents SDK.
            builder: The trace builder to populate.
        """
        # Extract final output
        final_output = getattr(result, "final_output", None)
        if final_output is not None:
            builder.output_text = str(final_output)
        elif isinstance(result, str):
            builder.output_text = result
        else:
            builder.output_text = str(result)

        # Extract tool calls from new_items
        new_items = getattr(result, "new_items", []) or []
        self._extract_tool_calls(new_items, builder)

        # Extract LLM calls from raw_responses
        raw_responses = getattr(result, "raw_responses", []) or []
        self._extract_llm_calls(raw_responses, builder)

    def _extract_tool_calls(self, items: list[Any], builder: Any) -> None:
        """Extract tool calls from run items.

        Items with a ``tool_name`` attribute are treated as tool call items.

        Args:
            items: List of run items from the result.
            builder: The trace builder to populate.
        """
        for item in items:
            tool_name = getattr(item, "tool_name", None)
            if tool_name is None:
                continue

            raw_args = getattr(item, "arguments", None)
            if isinstance(raw_args, dict):
                tool_input = raw_args
            elif raw_args is not None:
                tool_input = {"input": str(raw_args)}
            else:
                tool_input = {}

            tool_output = getattr(item, "output", None)

            builder.add_tool_call(
                ToolCall(
                    tool_name=str(tool_name),
                    tool_input=tool_input,
                    tool_output=tool_output,
                    success=True,
                )
            )

    def _extract_llm_calls(self, raw_responses: list[Any], builder: Any) -> None:
        """Extract LLM call data from raw model responses.

        Each response with a ``usage`` attribute contributes token counts.

        Args:
            raw_responses: List of raw model responses from the result.
            builder: The trace builder to populate.
        """
        for response in raw_responses:
            usage = getattr(response, "usage", None)
            if usage is None:
                continue

            input_tokens = int(getattr(usage, "input_tokens", 0))
            output_tokens = int(getattr(usage, "output_tokens", 0))

            if input_tokens > 0 or output_tokens > 0:
                model = self._model_name or getattr(self._agent, "model", None) or "unknown"
                builder.add_llm_call(
                    LLMCall(
                        model=str(model),
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                )
