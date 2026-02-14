"""Abstract base evaluator with template-method pattern.

Subclasses implement ``_evaluate()`` while the base class handles
timing, error wrapping, and consistent result construction.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from agentprobe.core.exceptions import EvaluatorError
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace

logger = logging.getLogger(__name__)


class BaseEvaluator(ABC):
    """Abstract base class for all evaluators.

    Provides a public ``evaluate()`` template method that delegates to
    the subclass-defined ``_evaluate()``, adding timing and error handling.

    Attributes:
        _name: The evaluator's name, used in results and logging.
    """

    def __init__(self, name: str) -> None:
        """Initialize the evaluator.

        Args:
            name: A unique name identifying this evaluator instance.
        """
        self._name = name

    @property
    def name(self) -> str:
        """Return the evaluator name."""
        return self._name

    async def evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Evaluate an agent trace for a given test case.

        This template method times the evaluation, catches errors, and
        ensures a consistent EvalResult is always returned.

        Args:
            test_case: The test case that was executed.
            trace: The execution trace to evaluate.

        Returns:
            An evaluation result with score and verdict.
        """
        start = time.monotonic()
        try:
            result = await self._evaluate(test_case, trace)
        except EvaluatorError:
            raise
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "Evaluator '%s' failed for test '%s': %s",
                self._name,
                test_case.name,
                exc,
            )
            return EvalResult(
                evaluator_name=self._name,
                verdict=EvalVerdict.ERROR,
                score=0.0,
                reason=f"Evaluation error: {exc}",
                metadata={"duration_ms": elapsed_ms},
            )
        else:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.debug(
                "Evaluator '%s' completed for test '%s' in %dms: %s (%.2f)",
                self._name,
                test_case.name,
                elapsed_ms,
                result.verdict.value,
                result.score,
            )
            return result

    @abstractmethod
    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Perform the actual evaluation logic.

        Subclasses must implement this method.

        Args:
            test_case: The test case that was executed.
            trace: The execution trace to evaluate.

        Returns:
            An evaluation result with score and verdict.
        """
        ...
