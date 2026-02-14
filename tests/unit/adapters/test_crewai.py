"""Tests for the CrewAIAdapter."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.adapters.crewai import CrewAIAdapter
from agentprobe.core.exceptions import AdapterError


class _FakeTaskOutput:
    """Simulates a CrewAI TaskOutput with tool usage."""

    def __init__(self, tools_used: list[dict[str, Any]] | None = None) -> None:
        self.tools_used = tools_used or []


class _FakeCrewOutput:
    """Simulates a CrewAI CrewOutput."""

    def __init__(
        self,
        raw: str = "crew result",
        tasks_output: list[Any] | None = None,
    ) -> None:
        self.raw = raw
        self.tasks_output = tasks_output or []


class _FakeCrew:
    """Simulates a CrewAI Crew with async support."""

    def __init__(self, output: _FakeCrewOutput | None = None) -> None:
        self._output = output or _FakeCrewOutput()

    async def kickoff_async(self, inputs: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._output


class _SyncCrew:
    """Crew with only synchronous kickoff."""

    def __init__(self, output: _FakeCrewOutput | None = None) -> None:
        self._output = output or _FakeCrewOutput()

    def kickoff(self, inputs: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._output


class _BrokenCrew:
    """Crew that raises exceptions."""

    async def kickoff_async(self, **kwargs: Any) -> Any:
        msg = "crew failed"
        raise RuntimeError(msg)


class _NoKickoffCrew:
    """Crew without kickoff methods."""


class TestCrewAIAdapter:
    """Tests for CrewAIAdapter."""

    async def test_basic_invocation(self) -> None:
        crew = _FakeCrew()
        adapter = CrewAIAdapter(crew, model_name="test-model")
        trace = await adapter.invoke("test input")
        assert trace.output_text == "crew result"
        assert trace.agent_name == "crewai"

    async def test_tool_calls_extracted(self) -> None:
        tools = [
            {"tool": "search", "input": {"q": "test"}, "output": "found"},
            {"tool": "write", "input": {"text": "hello"}, "output": "ok"},
        ]
        task_output = _FakeTaskOutput(tools_used=tools)
        crew_output = _FakeCrewOutput(raw="done", tasks_output=[task_output])
        crew = _FakeCrew(output=crew_output)
        adapter = CrewAIAdapter(crew)

        trace = await adapter.invoke("test")

        assert len(trace.tool_calls) == 2
        assert trace.tool_calls[0].tool_name == "search"
        assert trace.tool_calls[1].tool_name == "write"
        assert trace.tool_calls[0].tool_output == "found"

    async def test_string_result(self) -> None:
        """Test handling when crew returns a plain string."""

        class _StringCrew:
            async def kickoff_async(self, **kwargs: Any) -> str:
                return "plain string"

        adapter = CrewAIAdapter(_StringCrew())
        trace = await adapter.invoke("test")
        assert trace.output_text == "plain string"

    async def test_broken_crew_raises_adapter_error(self) -> None:
        adapter = CrewAIAdapter(_BrokenCrew())
        with pytest.raises(AdapterError, match="crew failed"):
            await adapter.invoke("test")

    async def test_no_kickoff_raises_adapter_error(self) -> None:
        adapter = CrewAIAdapter(_NoKickoffCrew())
        with pytest.raises(AdapterError, match="neither kickoff"):
            await adapter.invoke("test")

    async def test_custom_name(self) -> None:
        crew = _FakeCrew()
        adapter = CrewAIAdapter(crew, name="my-crew")
        trace = await adapter.invoke("test")
        assert trace.agent_name == "my-crew"

    async def test_multiple_tasks(self) -> None:
        t1 = _FakeTaskOutput(tools_used=[{"tool": "a", "input": {}, "output": "1"}])
        t2 = _FakeTaskOutput(tools_used=[{"tool": "b", "input": {}, "output": "2"}])
        crew_output = _FakeCrewOutput(raw="done", tasks_output=[t1, t2])
        crew = _FakeCrew(output=crew_output)
        adapter = CrewAIAdapter(crew)

        trace = await adapter.invoke("test")
        assert len(trace.tool_calls) == 2

    async def test_non_dict_tool_input(self) -> None:
        tools = [{"tool": "search", "input": "raw query", "output": "found"}]
        task_output = _FakeTaskOutput(tools_used=tools)
        crew_output = _FakeCrewOutput(tasks_output=[task_output])
        crew = _FakeCrew(output=crew_output)
        adapter = CrewAIAdapter(crew)

        trace = await adapter.invoke("test")
        assert trace.tool_calls[0].tool_input == {"input": "raw query"}
