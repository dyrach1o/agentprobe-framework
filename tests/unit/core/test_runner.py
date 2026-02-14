"""Tests for the TestRunner."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from agentprobe.core.config import AgentProbeConfig
from agentprobe.core.models import (
    EvalResult,
    EvalVerdict,
    RunStatus,
    TestCase,
    TestStatus,
    Trace,
)
from agentprobe.core.runner import TestRunner


class _MockAdapter:
    """Mock adapter for testing the runner."""

    def __init__(
        self,
        output: str = "mock output",
        delay: float = 0.0,
        fail: bool = False,
    ) -> None:
        self._output = output
        self._delay = delay
        self._fail = fail
        self.call_count = 0

    @property
    def name(self) -> str:
        return "mock-adapter"

    async def invoke(self, input_text: str, **kwargs: Any) -> Trace:
        self.call_count += 1
        if self._delay > 0:
            await asyncio.sleep(self._delay)
        if self._fail:
            msg = "mock failure"
            raise RuntimeError(msg)
        return Trace(
            agent_name="mock",
            input_text=input_text,
            output_text=self._output,
        )


class _MockEvaluator:
    """Mock evaluator for testing."""

    def __init__(self, verdict: EvalVerdict = EvalVerdict.PASS, score: float = 1.0) -> None:
        self._verdict = verdict
        self._score = score

    @property
    def name(self) -> str:
        return "mock-eval"

    async def evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name=self.name,
            verdict=self._verdict,
            score=self._score,
        )


class TestTestRunner:
    """Tests for the TestRunner."""

    @pytest.fixture
    def test_cases(self) -> list[TestCase]:
        return [
            TestCase(name="test_one", input_text="Hello"),
            TestCase(name="test_two", input_text="World"),
        ]

    @pytest.mark.asyncio
    async def test_sequential_execution(self, test_cases: list[TestCase]) -> None:
        adapter = _MockAdapter()
        runner = TestRunner()
        run = await runner.run(test_cases, adapter)
        assert run.status == RunStatus.COMPLETED
        assert run.total_tests == 2
        assert run.passed == 2
        assert adapter.call_count == 2

    @pytest.mark.asyncio
    async def test_parallel_execution(self, test_cases: list[TestCase]) -> None:
        config = AgentProbeConfig()
        config.runner.parallel = True
        config.runner.max_workers = 2
        adapter = _MockAdapter()
        runner = TestRunner(config=config)
        run = await runner.run(test_cases, adapter)
        assert run.total_tests == 2
        assert run.passed == 2

    @pytest.mark.asyncio
    async def test_adapter_failure_produces_error_result(self) -> None:
        adapter = _MockAdapter(fail=True)
        runner = TestRunner()
        run = await runner.run([TestCase(name="test_fail", input_text="x")], adapter)
        assert run.errors == 1
        assert run.test_results[0].status == TestStatus.ERROR
        assert run.test_results[0].error_message is not None

    @pytest.mark.asyncio
    async def test_timeout_produces_timeout_result(self) -> None:
        adapter = _MockAdapter(delay=5.0)
        tc = TestCase(name="test_timeout", input_text="x", timeout_seconds=0.1)
        runner = TestRunner()
        run = await runner.run([tc], adapter)
        assert run.test_results[0].status == TestStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_evaluator_results_included(self, test_cases: list[TestCase]) -> None:
        adapter = _MockAdapter()
        evaluator = _MockEvaluator(verdict=EvalVerdict.PASS, score=0.9)
        runner = TestRunner(evaluators=[evaluator])
        run = await runner.run(test_cases[:1], adapter)
        result = run.test_results[0]
        assert len(result.eval_results) == 1
        assert result.eval_results[0].score == 0.9
        assert result.status == TestStatus.PASSED

    @pytest.mark.asyncio
    async def test_failing_evaluator_marks_test_failed(self) -> None:
        adapter = _MockAdapter()
        evaluator = _MockEvaluator(verdict=EvalVerdict.FAIL, score=0.1)
        runner = TestRunner(evaluators=[evaluator])
        run = await runner.run([TestCase(name="test_eval_fail", input_text="x")], adapter)
        assert run.test_results[0].status == TestStatus.FAILED
        assert run.failed == 1

    @pytest.mark.asyncio
    async def test_empty_test_cases(self) -> None:
        adapter = _MockAdapter()
        runner = TestRunner()
        run = await runner.run([], adapter)
        assert run.total_tests == 0
        assert run.status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_status_failed_on_errors(self) -> None:
        adapter = _MockAdapter(fail=True)
        runner = TestRunner()
        run = await runner.run([TestCase(name="test_err", input_text="x")], adapter)
        assert run.status == RunStatus.FAILED
