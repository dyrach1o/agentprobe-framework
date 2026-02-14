"""Tests for protocol structural subtyping verification."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agentprobe.core.models import (
    AgentRun,
    EvalResult,
    EvalVerdict,
    RunStatus,
    TestCase,
    TestResult,
    Trace,
)
from agentprobe.core.protocols import (
    AdapterProtocol,
    EvaluatorProtocol,
    ReporterProtocol,
    RunnerProtocol,
    StorageProtocol,
)


class _FakeAdapter:
    """Concrete adapter implementation for protocol testing."""

    @property
    def name(self) -> str:
        return "fake"

    async def invoke(self, input_text: str, **kwargs: Any) -> Trace:
        return Trace(agent_name="fake", input_text=input_text)


class _FakeEvaluator:
    """Concrete evaluator implementation for protocol testing."""

    @property
    def name(self) -> str:
        return "fake-eval"

    async def evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name="fake-eval",
            verdict=EvalVerdict.PASS,
            score=1.0,
        )


class _FakeStorage:
    """Concrete storage implementation for protocol testing."""

    async def setup(self) -> None:
        pass

    async def save_trace(self, trace: Trace) -> None:
        pass

    async def load_trace(self, trace_id: str) -> Trace | None:
        return None

    async def list_traces(self, agent_name: str | None = None, limit: int = 100) -> Sequence[Trace]:
        return []

    async def save_result(self, result: TestResult) -> None:
        pass

    async def load_results(
        self, test_name: str | None = None, limit: int = 100
    ) -> Sequence[TestResult]:
        return []


class _FakeRunner:
    """Concrete runner implementation for protocol testing."""

    async def run(self, test_cases: Sequence[TestCase], adapter: AdapterProtocol) -> AgentRun:
        return AgentRun(agent_name="fake", status=RunStatus.COMPLETED)


class _FakeReporter:
    """Concrete reporter implementation for protocol testing."""

    async def report(self, run: AgentRun) -> None:
        pass


class _NotAnAdapter:
    """Intentionally missing required methods."""

    pass


class TestAdapterProtocol:
    """Verify AdapterProtocol structural subtyping."""

    def test_conforming_class_is_instance(self) -> None:
        adapter = _FakeAdapter()
        assert isinstance(adapter, AdapterProtocol)

    def test_non_conforming_class_is_not_instance(self) -> None:
        obj = _NotAnAdapter()
        assert not isinstance(obj, AdapterProtocol)


class TestEvaluatorProtocol:
    """Verify EvaluatorProtocol structural subtyping."""

    def test_conforming_class_is_instance(self) -> None:
        evaluator = _FakeEvaluator()
        assert isinstance(evaluator, EvaluatorProtocol)


class TestStorageProtocol:
    """Verify StorageProtocol structural subtyping."""

    def test_conforming_class_is_instance(self) -> None:
        storage = _FakeStorage()
        assert isinstance(storage, StorageProtocol)


class TestRunnerProtocol:
    """Verify RunnerProtocol structural subtyping."""

    def test_conforming_class_is_instance(self) -> None:
        runner = _FakeRunner()
        assert isinstance(runner, RunnerProtocol)


class TestReporterProtocol:
    """Verify ReporterProtocol structural subtyping."""

    def test_conforming_class_is_instance(self) -> None:
        reporter = _FakeReporter()
        assert isinstance(reporter, ReporterProtocol)
