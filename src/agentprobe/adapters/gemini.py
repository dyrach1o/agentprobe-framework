"""Google Vertex AI / Gemini adapter.

Wraps a Google Generative AI model and translates its execution into
AgentProbe's Trace format by extracting token usage from response metadata
and function calls from response parts.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import LLMCall, ToolCall, Trace

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Generative AI / Vertex AI Gemini models.

    Supports both the ``google-genai`` and ``google-generativeai`` SDKs.
    Captures token usage from response metadata and function calls from
    response parts.

    Attributes:
        _model: The Gemini GenerativeModel or genai client model object.
        _model_name: Model name for trace records.
    """

    def __init__(
        self,
        model: Any,
        *,
        name: str = "gemini",
        model_name: str | None = None,
    ) -> None:
        """Initialize the Gemini adapter.

        Args:
            model: A Google GenerativeModel or genai model object.
            name: Adapter name for identification.
            model_name: Model name to record in traces. If not provided,
                attempts to read from the model object.
        """
        super().__init__(name)
        self._model = model
        self._model_name = model_name

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the Gemini model and build a trace.

        Attempts ``generate_content_async()`` first, then falls back to
        ``generate_content()`` in an executor.

        Args:
            input_text: The input prompt.
            **kwargs: Passed through to the generation method.

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the model invocation fails.
        """
        resolved_model = self._model_name or getattr(self._model, "model_name", None)
        builder = self._create_builder(model=resolved_model)
        builder.input_text = input_text

        try:
            if hasattr(self._model, "generate_content_async"):
                response = await self._model.generate_content_async(input_text, **kwargs)
            elif hasattr(self._model, "generate_content"):
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self._model.generate_content(input_text),
                )
            else:
                raise AdapterError(
                    self.name,
                    "Model has neither generate_content() nor generate_content_async()",
                )
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self.name, f"Generation failed: {exc}") from exc

        self._extract_result(response, builder)
        return builder.build()

    def _extract_result(self, response: Any, builder: Any) -> None:
        """Extract output text, token usage, and function calls from the response.

        Args:
            response: The raw GenerateContentResponse.
            builder: The trace builder to populate.
        """
        # Extract output text
        text = getattr(response, "text", None)
        if text is not None:
            builder.output_text = str(text)
        else:
            # Try candidates[0].content.parts[0].text
            candidates = getattr(response, "candidates", []) or []
            if candidates:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", []) or [] if content else []
                for part in parts:
                    part_text = getattr(part, "text", None)
                    if part_text is not None:
                        builder.output_text = str(part_text)
                        break

        self._extract_usage(response, builder)
        self._extract_function_calls(response, builder)

    def _extract_usage(self, response: Any, builder: Any) -> None:
        """Extract token usage from response metadata.

        Checks ``usage_metadata`` (google-genai SDK) for token counts.

        Args:
            response: The raw model response.
            builder: The trace builder to populate.
        """
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return

        input_tokens = int(getattr(usage, "prompt_token_count", 0))
        output_tokens = int(getattr(usage, "candidates_token_count", 0))

        if input_tokens > 0 or output_tokens > 0:
            model = self._model_name or getattr(self._model, "model_name", None) or "unknown"
            builder.add_llm_call(
                LLMCall(
                    model=str(model),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )

    def _extract_function_calls(self, response: Any, builder: Any) -> None:
        """Extract function calls from response parts.

        Gemini returns function calls as parts within candidates.

        Args:
            response: The raw model response.
            builder: The trace builder to populate.
        """
        candidates = getattr(response, "candidates", []) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content is None:
                continue
            parts = getattr(content, "parts", []) or []
            for part in parts:
                function_call = getattr(part, "function_call", None)
                if function_call is None:
                    continue

                fn_name = getattr(function_call, "name", "unknown")
                fn_args = getattr(function_call, "args", None)
                if isinstance(fn_args, dict):
                    tool_input = fn_args
                elif fn_args is not None:
                    tool_input = {"input": str(fn_args)}
                else:
                    tool_input = {}

                builder.add_tool_call(
                    ToolCall(
                        tool_name=str(fn_name),
                        tool_input=tool_input,
                        tool_output=None,
                        success=True,
                    )
                )
