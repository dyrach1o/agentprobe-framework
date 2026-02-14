"""Multi-turn conversation runner for sequential dialogue testing.

Executes a series of conversation turns against an agent adapter,
collecting per-turn traces and evaluation results, then aggregates
into a ConversationResult.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from agentprobe.core.models import (
    ConversationResult,
    ConversationTurn,
    EvalResult,
    EvalVerdict,
    TestCase,
    TurnResult,
)
from agentprobe.core.protocols import AdapterProtocol, EvaluatorProtocol

logger = logging.getLogger(__name__)


class ConversationRunner:
    """Runs multi-turn conversation tests against an agent.

    Executes each turn sequentially, optionally passing the previous
    output as context to the next turn's input. Collects per-turn
    evaluation results and aggregates into a final ConversationResult.

    Attributes:
        evaluators: Mapping of evaluator names to instances.
    """

    def __init__(
        self,
        evaluators: dict[str, EvaluatorProtocol] | None = None,
    ) -> None:
        """Initialize the conversation runner.

        Args:
            evaluators: Named evaluator instances for per-turn evaluation.
        """
        self._evaluators = evaluators or {}

    async def run(
        self,
        adapter: AdapterProtocol,
        turns: Sequence[ConversationTurn],
        *,
        pass_context: bool = True,
    ) -> ConversationResult:
        """Execute a multi-turn conversation.

        Args:
            adapter: The agent adapter to invoke for each turn.
            turns: The conversation turns to execute in order.
            pass_context: If True, prepend previous output to next turn's input.

        Returns:
            A ConversationResult with per-turn details and aggregate metrics.

        Raises:
            ConversationError: If a critical error occurs during execution.
        """
        turn_results: list[TurnResult] = []
        previous_output = ""
        total_start = time.monotonic()

        for i, turn in enumerate(turns):
            input_text = turn.input_text
            if pass_context and previous_output:
                input_text = f"{previous_output}\n\n{turn.input_text}"

            turn_start = time.monotonic()
            try:
                trace = await adapter.invoke(input_text)
                previous_output = trace.output_text
            except Exception as exc:
                logger.error("Turn %d failed: %s", i, exc)
                turn_results.append(
                    TurnResult(
                        turn_index=i,
                        input_text=turn.input_text,
                        trace=None,
                        eval_results=(),
                        duration_ms=int((time.monotonic() - turn_start) * 1000),
                    )
                )
                continue

            # Run per-turn evaluators
            eval_results: list[EvalResult] = []
            if turn.evaluators:
                test_case = TestCase(
                    name=f"turn_{i}",
                    input_text=turn.input_text,
                    expected_output=turn.expected_output,
                )
                for eval_name in turn.evaluators:
                    evaluator = self._evaluators.get(eval_name)
                    if evaluator is None:
                        logger.warning("Turn %d: evaluator '%s' not found", i, eval_name)
                        continue
                    result = await evaluator.evaluate(test_case, trace)
                    eval_results.append(result)

            duration_ms = int((time.monotonic() - turn_start) * 1000)
            turn_results.append(
                TurnResult(
                    turn_index=i,
                    input_text=turn.input_text,
                    trace=trace,
                    eval_results=tuple(eval_results),
                    duration_ms=duration_ms,
                )
            )

        total_duration = int((time.monotonic() - total_start) * 1000)
        return self._build_result(adapter.name, turn_results, total_duration)

    @staticmethod
    def _build_result(
        agent_name: str,
        turn_results: list[TurnResult],
        total_duration_ms: int,
    ) -> ConversationResult:
        """Aggregate per-turn results into a ConversationResult."""
        passed = 0
        scores: list[float] = []

        for tr in turn_results:
            if tr.eval_results:
                turn_passed = all(er.verdict == EvalVerdict.PASS for er in tr.eval_results)
                if turn_passed:
                    passed += 1
                turn_score = sum(er.score for er in tr.eval_results) / len(tr.eval_results)
                scores.append(turn_score)
            elif tr.trace is not None:
                # No evaluators but trace exists = pass
                passed += 1
                scores.append(1.0)
            else:
                scores.append(0.0)

        aggregate_score = sum(scores) / len(scores) if scores else 0.0

        return ConversationResult(
            agent_name=agent_name,
            turn_results=tuple(turn_results),
            total_turns=len(turn_results),
            passed_turns=passed,
            aggregate_score=round(min(aggregate_score, 1.0), 6),
            total_duration_ms=total_duration_ms,
        )
