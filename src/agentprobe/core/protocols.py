"""Protocol definitions for AgentProbe's pluggable architecture.

All protocols are runtime-checkable, allowing isinstance() verification
of structural subtyping. Implementors do not need to inherit from these
protocols — they only need to provide the required methods.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from agentprobe.core.models import (
    AgentRun,
    EvalResult,
    MetricValue,
    TestCase,
    TestResult,
    Trace,
)


@runtime_checkable
class AdapterProtocol(Protocol):
    """Interface for agent framework adapters.

    Adapters wrap specific agent frameworks (LangChain, CrewAI, etc.)
    and translate their execution into AgentProbe's Trace format.
    """

    @property
    def name(self) -> str:
        """Return the adapter name."""
        ...

    async def invoke(
        self,
        input_text: str,
        **kwargs: Any,
    ) -> Trace:
        """Invoke the agent with the given input and return a trace.

        Args:
            input_text: The input prompt to send to the agent.
            **kwargs: Additional adapter-specific arguments.

        Returns:
            A complete execution trace.
        """
        ...


@runtime_checkable
class EvaluatorProtocol(Protocol):
    """Interface for test result evaluators.

    Evaluators assess agent outputs against expectations, producing
    scored results with pass/fail verdicts.
    """

    @property
    def name(self) -> str:
        """Return the evaluator name."""
        ...

    async def evaluate(
        self,
        test_case: TestCase,
        trace: Trace,
    ) -> EvalResult:
        """Evaluate an agent's output for a given test case.

        Args:
            test_case: The test case that was executed.
            trace: The execution trace to evaluate.

        Returns:
            An evaluation result with score and verdict.
        """
        ...


@runtime_checkable
class StorageProtocol(Protocol):
    """Interface for persistence backends.

    Storage implementations handle saving and loading traces,
    test results, and agent runs.
    """

    async def setup(self) -> None:
        """Initialize the storage backend (create tables, etc.)."""
        ...

    async def save_trace(self, trace: Trace) -> None:
        """Persist a trace.

        Args:
            trace: The trace to save.
        """
        ...

    async def load_trace(self, trace_id: str) -> Trace | None:
        """Load a trace by ID.

        Args:
            trace_id: The unique identifier of the trace.

        Returns:
            The trace if found, otherwise None.
        """
        ...

    async def list_traces(
        self,
        agent_name: str | None = None,
        limit: int = 100,
    ) -> Sequence[Trace]:
        """List traces with optional filtering.

        Args:
            agent_name: Filter by agent name if provided.
            limit: Maximum number of traces to return.

        Returns:
            A sequence of matching traces.
        """
        ...

    async def save_result(self, result: TestResult) -> None:
        """Persist a test result.

        Args:
            result: The test result to save.
        """
        ...

    async def load_results(
        self,
        test_name: str | None = None,
        limit: int = 100,
    ) -> Sequence[TestResult]:
        """Load test results with optional filtering.

        Args:
            test_name: Filter by test name if provided.
            limit: Maximum number of results to return.

        Returns:
            A sequence of matching test results.
        """
        ...


@runtime_checkable
class MetricStoreProtocol(Protocol):
    """Interface for metric persistence backends.

    Metric storage is optional and separate from the main StorageProtocol,
    allowing implementations to opt in to metric tracking independently.
    """

    async def save_metrics(self, metrics: Sequence[MetricValue]) -> None:
        """Persist a batch of metric values.

        Args:
            metrics: The metric values to save.
        """
        ...

    async def load_metrics(
        self,
        metric_name: str | None = None,
        limit: int = 1000,
    ) -> Sequence[MetricValue]:
        """Load metric values with optional filtering.

        Args:
            metric_name: Filter by metric name if provided.
            limit: Maximum number of values to return.

        Returns:
            A sequence of matching metric values.
        """
        ...


@runtime_checkable
class RunnerProtocol(Protocol):
    """Interface for test execution engines."""

    async def run(
        self,
        test_cases: Sequence[TestCase],
        adapter: AdapterProtocol,
    ) -> AgentRun:
        """Execute a batch of test cases against an agent adapter.

        Args:
            test_cases: The test cases to execute.
            adapter: The agent adapter to test against.

        Returns:
            An AgentRun containing all results.
        """
        ...


@runtime_checkable
class ReporterProtocol(Protocol):
    """Interface for test result reporters."""

    async def report(self, run: AgentRun) -> None:
        """Generate and output a report for an agent run.

        Args:
            run: The completed agent run to report on.
        """
        ...
