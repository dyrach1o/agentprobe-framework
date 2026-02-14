"""Test runner: orchestrates test execution with optional parallelism.

Discovers tests, invokes them against an adapter, runs evaluators,
and assembles results into an AgentRun.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence

from agentprobe.core.config import AgentProbeConfig
from agentprobe.core.models import (
    AgentRun,
    EvalResult,
    RunStatus,
    TestCase,
    TestResult,
    TestStatus,
    Trace,
)
from agentprobe.core.protocols import AdapterProtocol, EvaluatorProtocol

logger = logging.getLogger(__name__)


class TestRunner:
    """Orchestrates test case execution against an agent adapter.

    Supports sequential and parallel execution modes, per-test timeouts,
    and evaluator orchestration.

    Attributes:
        config: The runner configuration.
        evaluators: Evaluators to run on each test result.
    """

    def __init__(
        self,
        config: AgentProbeConfig | None = None,
        evaluators: list[EvaluatorProtocol] | None = None,
    ) -> None:
        """Initialize the test runner.

        Args:
            config: AgentProbe configuration. Uses defaults if None.
            evaluators: Evaluators to apply to test results.
        """
        self._config = config or AgentProbeConfig()
        self._evaluators = evaluators or []

    async def run(
        self,
        test_cases: Sequence[TestCase],
        adapter: AdapterProtocol,
    ) -> AgentRun:
        """Execute test cases against an adapter and collect results.

        Args:
            test_cases: The test cases to execute.
            adapter: The agent adapter to test.

        Returns:
            An AgentRun with all results.
        """
        start = time.monotonic()
        results: list[TestResult] = []

        if self._config.runner.parallel:
            results = await self._run_parallel(list(test_cases), adapter)
        else:
            results = await self._run_sequential(list(test_cases), adapter)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)

        status = RunStatus.COMPLETED if errors == 0 else RunStatus.FAILED

        return AgentRun(
            agent_name=adapter.name,
            status=status,
            test_results=tuple(results),
            total_tests=len(results),
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_ms=elapsed_ms,
        )

    async def _run_sequential(
        self,
        test_cases: list[TestCase],
        adapter: AdapterProtocol,
    ) -> list[TestResult]:
        """Execute tests one at a time."""
        results: list[TestResult] = []
        for tc in test_cases:
            result = await self._execute_single(tc, adapter)
            results.append(result)
        return results

    async def _run_parallel(
        self,
        test_cases: list[TestCase],
        adapter: AdapterProtocol,
    ) -> list[TestResult]:
        """Execute tests concurrently with a semaphore limit."""
        semaphore = asyncio.Semaphore(self._config.runner.max_workers)
        results: list[TestResult] = [None] * len(test_cases)  # type: ignore[list-item]

        async def _run_with_semaphore(idx: int, tc: TestCase) -> None:
            async with semaphore:
                results[idx] = await self._execute_single(tc, adapter)

        async with asyncio.TaskGroup() as tg:
            for i, tc in enumerate(test_cases):
                tg.create_task(_run_with_semaphore(i, tc))

        return results

    async def _execute_single(
        self,
        test_case: TestCase,
        adapter: AdapterProtocol,
    ) -> TestResult:
        """Execute a single test case with timeout and error handling.

        Args:
            test_case: The test to execute.
            adapter: The agent adapter.

        Returns:
            A TestResult reflecting the outcome.
        """
        start = time.monotonic()
        timeout = test_case.timeout_seconds or self._config.runner.default_timeout

        try:
            trace = await asyncio.wait_for(
                adapter.invoke(test_case.input_text),
                timeout=timeout,
            )
        except TimeoutError:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning("Test '%s' timed out after %.1fs", test_case.name, timeout)
            return TestResult(
                test_name=test_case.name,
                status=TestStatus.TIMEOUT,
                duration_ms=elapsed_ms,
                error_message=f"Timed out after {timeout}s",
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error("Test '%s' errored: %s", test_case.name, exc)
            return TestResult(
                test_name=test_case.name,
                status=TestStatus.ERROR,
                duration_ms=elapsed_ms,
                error_message=str(exc),
            )

        eval_results = await self._run_evaluators(test_case, trace)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if eval_results:
            avg_score = sum(r.score for r in eval_results) / len(eval_results)
            all_passed = all(r.verdict.value in ("pass", "partial") for r in eval_results)
        else:
            avg_score = 1.0
            all_passed = True

        status = TestStatus.PASSED if all_passed else TestStatus.FAILED

        return TestResult(
            test_name=test_case.name,
            status=status,
            score=avg_score,
            duration_ms=elapsed_ms,
            trace=trace,
            eval_results=tuple(eval_results),
        )

    async def _run_evaluators(
        self,
        test_case: TestCase,
        trace: Trace,
    ) -> list[EvalResult]:
        """Run all evaluators against a test result.

        Args:
            test_case: The test case.
            trace: The execution trace.

        Returns:
            List of evaluation results.
        """
        results: list[EvalResult] = []
        for evaluator in self._evaluators:
            try:
                result = await evaluator.evaluate(test_case, trace)
                results.append(result)
            except Exception:
                logger.exception(
                    "Evaluator '%s' failed for test '%s'",
                    evaluator.name,
                    test_case.name,
                )
        return results
