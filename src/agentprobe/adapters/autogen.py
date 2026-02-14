"""AutoGen framework adapter.

Wraps an AutoGen agent chat session and translates the message history
into AgentProbe's Trace format by parsing conversation turns.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import LLMCall, ToolCall, Trace

logger = logging.getLogger(__name__)


class AutoGenAdapter(BaseAdapter):
    """Adapter for AutoGen agent conversations.

    Captures message history from AutoGen's chat interface and translates
    function calls and assistant responses into a structured trace.

    Attributes:
        _agent: The primary AutoGen agent (e.g. AssistantAgent).
        _user_proxy: The user proxy agent for initiating chats.
        _model_name: Optional model name for trace records.
    """

    def __init__(
        self,
        agent: Any,
        user_proxy: Any,
        *,
        name: str = "autogen",
        model_name: str | None = None,
    ) -> None:
        """Initialize the AutoGen adapter.

        Args:
            agent: An AutoGen AssistantAgent or similar.
            user_proxy: An AutoGen UserProxyAgent for initiating chats.
            name: Adapter name for identification.
            model_name: Model name to record in traces.
        """
        super().__init__(name)
        self._agent = agent
        self._user_proxy = user_proxy
        self._model_name = model_name

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the AutoGen agent chat and build a trace.

        Args:
            input_text: The input prompt.
            **kwargs: Passed through to the chat initiation.

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the chat invocation fails.
        """
        builder = self._create_builder(model=self._model_name)
        builder.input_text = input_text

        try:
            if hasattr(self._user_proxy, "a_initiate_chat"):
                await self._user_proxy.a_initiate_chat(self._agent, message=input_text, **kwargs)
            elif hasattr(self._user_proxy, "initiate_chat"):
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._user_proxy.initiate_chat(self._agent, message=input_text),
                )
            else:
                raise AdapterError(
                    self.name,
                    "User proxy has neither initiate_chat() nor a_initiate_chat()",
                )
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self.name, f"Chat invocation failed: {exc}") from exc

        self._extract_messages(builder)
        return builder.build()

    def _extract_messages(self, builder: Any) -> None:
        """Extract messages from the agent's chat history.

        Args:
            builder: The trace builder to populate.
        """
        messages: list[dict[str, Any]] = []
        if hasattr(self._agent, "chat_messages"):
            for msg_list in self._agent.chat_messages.values():
                messages.extend(msg_list)
        elif hasattr(self._agent, "messages"):
            messages = list(self._agent.messages)

        last_assistant_msg = ""
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "assistant":
                last_assistant_msg = str(content) if content else ""
                self._extract_function_calls(msg, builder)
            elif role in {"function", "tool"}:
                builder.add_tool_call(
                    ToolCall(
                        tool_name=str(msg.get("name", "unknown")),
                        tool_input={},
                        tool_output=str(content),
                        success=True,
                    )
                )

        builder.output_text = last_assistant_msg

    def _extract_function_calls(self, msg: dict[str, Any], builder: Any) -> None:
        """Extract function/tool calls from an assistant message.

        Args:
            msg: A single message dict from the chat history.
            builder: The trace builder to populate.
        """
        function_call = msg.get("function_call")
        if isinstance(function_call, dict):
            name = str(function_call.get("name", "unknown"))
            arguments = function_call.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {"input": str(arguments)}
            builder.add_tool_call(
                ToolCall(
                    tool_name=name,
                    tool_input=arguments,
                    tool_output=None,
                    success=True,
                )
            )

        tool_calls = msg.get("tool_calls", [])
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                func = tc.get("function", {})
                if isinstance(func, dict):
                    name = str(func.get("name", "unknown"))
                    arguments = func.get("arguments", {})
                    if not isinstance(arguments, dict):
                        arguments = {"input": str(arguments)}
                    builder.add_tool_call(
                        ToolCall(
                            tool_name=name,
                            tool_input=arguments,
                            tool_output=None,
                            success=True,
                        )
                    )

    def _extract_token_usage(self, builder: Any) -> None:
        """Extract token usage from agent cost tracking if available.

        Args:
            builder: The trace builder to populate.
        """
        cost_info = getattr(self._agent, "cost", None)
        if isinstance(cost_info, dict):
            input_tokens = int(cost_info.get("prompt_tokens", 0))
            output_tokens = int(cost_info.get("completion_tokens", 0))
            if input_tokens > 0 or output_tokens > 0:
                model = self._model_name or "unknown"
                builder.add_llm_call(
                    LLMCall(
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                )
