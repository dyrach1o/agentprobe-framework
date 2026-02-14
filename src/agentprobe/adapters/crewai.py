"""CrewAI framework adapter.

Wraps a CrewAI Crew object and translates its execution into AgentProbe's
Trace format by extracting task results and tool usage from the crew output.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.exceptions import AdapterError
from agentprobe.core.models import ToolCall, Trace

logger = logging.getLogger(__name__)


class CrewAIAdapter(BaseAdapter):
    """Adapter for CrewAI Crew objects.

    Captures task results and tool usage from CrewAI's kickoff output
    to build a complete execution trace.

    Attributes:
        _crew: The CrewAI Crew object to invoke.
        _model_name: Optional model name for trace records.
    """

    def __init__(
        self,
        crew: Any,
        *,
        name: str = "crewai",
        model_name: str | None = None,
    ) -> None:
        """Initialize the CrewAI adapter.

        Args:
            crew: A CrewAI Crew object.
            name: Adapter name for identification.
            model_name: Model name to record in traces.
        """
        super().__init__(name)
        self._crew = crew
        self._model_name = model_name

    async def _invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the CrewAI crew and build a trace.

        Args:
            input_text: The input prompt.
            **kwargs: Passed through to the crew.

        Returns:
            A complete execution trace.

        Raises:
            AdapterError: If the crew invocation fails.
        """
        builder = self._create_builder(model=self._model_name)
        builder.input_text = input_text

        try:
            if hasattr(self._crew, "kickoff_async"):
                result = await self._crew.kickoff_async(inputs={"input": input_text}, **kwargs)
            elif hasattr(self._crew, "kickoff"):
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._crew.kickoff(inputs={"input": input_text}),
                )
            else:
                raise AdapterError(
                    self.name,
                    "Crew has neither kickoff() nor kickoff_async() method",
                )
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(self.name, f"Crew invocation failed: {exc}") from exc

        self._extract_result(result, builder)
        return builder.build()

    def _extract_result(self, result: Any, builder: Any) -> None:
        """Extract output and task data from the crew result.

        Args:
            result: The raw CrewOutput or similar result.
            builder: The trace builder to populate.
        """
        if hasattr(result, "raw"):
            builder.output_text = str(result.raw)
        elif isinstance(result, str):
            builder.output_text = result
        else:
            builder.output_text = str(result)

        # Extract tasks_output if available
        tasks_output = getattr(result, "tasks_output", []) or []
        for task_output in tasks_output:
            self._extract_task_tools(task_output, builder)

    def _extract_task_tools(self, task_output: Any, builder: Any) -> None:
        """Extract tool calls from a single task output.

        Args:
            task_output: A CrewAI TaskOutput object.
            builder: The trace builder to populate.
        """
        tools_used = getattr(task_output, "tools_used", []) or []
        for tool_info in tools_used:
            if isinstance(tool_info, dict):
                tool_name = str(tool_info.get("tool", "unknown"))
                tool_input = tool_info.get("input", {})
                tool_output = tool_info.get("output", "")
            else:
                tool_name = str(getattr(tool_info, "tool", "unknown"))
                tool_input = getattr(tool_info, "input", {})
                tool_output = getattr(tool_info, "output", "")

            if not isinstance(tool_input, dict):
                tool_input = {"input": str(tool_input)}

            builder.add_tool_call(
                ToolCall(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=tool_output,
                    success=True,
                )
            )
