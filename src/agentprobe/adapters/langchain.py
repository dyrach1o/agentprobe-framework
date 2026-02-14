"""LangChain framework adapter.

Wraps a LangChain agent (AgentExecutor or RunnableSequence) and
translates its execution into AgentProbe's Trace format by extracting
intermediate steps and token usage via callback instrumentation.
"""

from __future__ import annotations

import logging
from typing import Any

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import LLMCall, ToolCall, Trace

logger = logging.getLogger(__name__)


def _create_token_handler() -> Any | None:
    """Create a LangChain callback handler that captures token usage.

    Returns the handler instance, or None if langchain is not installed.
    """
    try:
        from langchain_core.callbacks import BaseCallbackHandler  # noqa: PLC0415
    except ImportError:
        return None

    class _TokenHandler(BaseCallbackHandler):  # type: ignore[misc]
        """Callback handler that accumulates token usage across LLM calls."""

        def __init__(self) -> None:
            super().__init__()
            self.total_input_tokens: int = 0
            self.total_output_tokens: int = 0
            self.model_id: str | None = None

        def on_llm_end(self, response: Any, **kwargs: Any) -> None:
            """Extract token usage from the LLM response."""
            input_tokens = 0
            output_tokens = 0

            # Source 1: AIMessage.usage_metadata (Anthropic, modern providers)
            for gen_list in getattr(response, "generations", []):
                for gen in gen_list:
                    msg = getattr(gen, "message", None)
                    if msg is None:
                        continue
                    usage = getattr(msg, "usage_metadata", None)
                    if usage:
                        if isinstance(usage, dict):
                            input_tokens += int(usage.get("input_tokens", 0))
                            output_tokens += int(usage.get("output_tokens", 0))
                        else:
                            input_tokens += int(getattr(usage, "input_tokens", 0))
                            output_tokens += int(getattr(usage, "output_tokens", 0))

                    resp_meta = getattr(msg, "response_metadata", {})
                    if isinstance(resp_meta, dict):
                        model = resp_meta.get("model") or resp_meta.get("model_name")
                        if model:
                            self.model_id = str(model)

            # Source 2: llm_output (fallback for older providers / OpenAI)
            if input_tokens == 0 and output_tokens == 0:
                llm_output = getattr(response, "llm_output", None) or {}
                if isinstance(llm_output, dict):
                    usage = llm_output.get("usage", llm_output.get("token_usage", {}))
                    if isinstance(usage, dict):
                        input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)))  # type: ignore[arg-type]
                        output_tokens = int(
                            usage.get("output_tokens", usage.get("completion_tokens", 0))  # type: ignore[arg-type]
                        )

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

    return _TokenHandler()


class LangChainAdapter(BaseAdapter):
    """Adapter for LangChain agents (AgentExecutor or Runnable).

    Captures intermediate steps (tool calls) and token usage from
    LangChain's callback metadata to build a complete execution trace.

    Attributes:
        agent: The LangChain agent or runnable to invoke.
        model_name: The model name to use in trace records.
    """

    def __init__(
        self,
        agent: Any,
        *,
        name: str = "langchain",
        model_name: str | None = None,
    ) -> None:
        """Initialize the LangChain adapter.

        Args:
            agent: A LangChain AgentExecutor or Runnable.
            name: Adapter name for identification.
            model_name: Model name to record in traces.
        """
        super().__init__(name)
        self._agent = agent
        self._model_name = model_name

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the LangChain agent and build a trace.

        Attempts async invocation first (``ainvoke``), then falls back
        to synchronous ``invoke`` if async is not available. Attaches a
        callback handler to capture token usage from the LLM response.

        Args:
            input_text: The input prompt.
            **kwargs: Passed through to the agent.

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the agent invocation fails.
        """
        builder = self._create_builder(model=self._model_name)
        builder.input_text = input_text

        token_handler = _create_token_handler()
        invoke_config: dict[str, Any] | None = None
        if token_handler is not None:
            invoke_config = {"callbacks": [token_handler]}

        try:
            if hasattr(self._agent, "ainvoke"):
                result = await self._agent.ainvoke(
                    {"input": input_text}, config=invoke_config, **kwargs
                )
            elif hasattr(self._agent, "invoke"):
                result = self._agent.invoke({"input": input_text}, config=invoke_config, **kwargs)
            else:
                raise AdapterError(
                    self.name,
                    "Agent has neither invoke() nor ainvoke() method",
                )
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self.name, f"Agent invocation failed: {exc}") from exc

        self._extract_result(result, builder)

        # If no token usage from the result dict, use the callback handler
        if token_handler is not None and not builder.llm_calls:
            self._apply_callback_tokens(token_handler, builder)

        return builder.build()

    def _apply_callback_tokens(self, token_handler: Any, builder: Any) -> None:
        """Apply token usage captured by the callback handler.

        Args:
            token_handler: The callback handler with accumulated token data.
            builder: The trace builder to populate.
        """
        input_tokens: int = getattr(token_handler, "total_input_tokens", 0)
        output_tokens: int = getattr(token_handler, "total_output_tokens", 0)

        if input_tokens > 0 or output_tokens > 0:
            model_id: str | None = getattr(token_handler, "model_id", None)
            model = model_id or self._model_name or "unknown"
            builder.add_llm_call(
                LLMCall(
                    model=str(model),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )

    def _extract_result(self, result: Any, builder: Any) -> None:
        """Extract output and intermediate steps from the agent result.

        Args:
            result: The raw result from agent invocation.
            builder: The trace builder to populate.
        """
        if isinstance(result, dict):
            builder.output_text = str(result.get("output", ""))
            intermediate_steps = result.get("intermediate_steps", [])
            self._extract_intermediate_steps(intermediate_steps, builder)
            self._extract_token_usage(result, builder)
        elif isinstance(result, str):
            builder.output_text = result
        else:
            builder.output_text = str(result)

    def _extract_intermediate_steps(self, steps: list[Any], builder: Any) -> None:
        """Extract tool calls from LangChain intermediate steps.

        Each step is typically a (AgentAction, observation) tuple.

        Args:
            steps: List of intermediate step tuples.
            builder: The trace builder to populate.
        """
        for step in steps:
            _min_step_length = 2
            if not isinstance(step, (list, tuple)) or len(step) < _min_step_length:
                continue

            action, observation = step[0], step[1]
            tool_name = getattr(action, "tool", "unknown")
            tool_input_raw = getattr(action, "tool_input", {})
            tool_input = (
                tool_input_raw
                if isinstance(tool_input_raw, dict)
                else {"input": str(tool_input_raw)}
            )

            builder.add_tool_call(
                ToolCall(
                    tool_name=str(tool_name),
                    tool_input=tool_input,
                    tool_output=observation,
                    success=True,
                )
            )

    def _extract_token_usage(self, result: dict[str, Any], builder: Any) -> None:
        """Extract token usage from LangChain callback metadata.

        Args:
            result: The raw agent result dict.
            builder: The trace builder to populate.
        """
        token_usage = result.get("token_usage") or result.get("llm_output", {})
        if not isinstance(token_usage, dict):
            return

        input_tokens = int(token_usage.get("prompt_tokens", 0))
        output_tokens = int(token_usage.get("completion_tokens", 0))

        if input_tokens > 0 or output_tokens > 0:
            model = self._model_name or token_usage.get("model_name", "unknown")
            builder.add_llm_call(
                LLMCall(
                    model=str(model),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )
