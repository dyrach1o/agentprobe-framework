#!/usr/bin/env python3
"""Example: Implementing a custom agent adapter.

Demonstrates how to create an adapter that conforms to AdapterProtocol,
allowing any callable to be tested through the AgentProbe framework.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from agentprobe.core.models import (
    EvalVerdict,
    LLMCall,
    TestCase,
    TestStatus,
    Trace,
    TurnType,
)
from agentprobe.core.runner import TestRunner
from agentprobe.eval.rules import RuleBasedEvaluator


class CalculatorAdapter:
    """An adapter that wraps a simple calculator agent.

    The adapter implements the AdapterProtocol: it has a ``name``
    property and an ``invoke(input_text, **kwargs) -> Trace`` method.
    """

    @property
    def name(self) -> str:
        return "calculator-agent"

    def _compute(self, expression: str) -> str:
        """Evaluate a math expression safely."""
        # Only allow digits, operators, and whitespace
        allowed = set("0123456789+-*/.(). ")
        if not all(c in allowed for c in expression):
            return "Error: invalid characters in expression"
        try:
            result = eval(expression)
            return str(result)
        except Exception:
            return "Error: could not evaluate expression"

    def invoke(self, input_text: str, **kwargs: object) -> Trace:
        """Process an input and return a trace of the execution.

        Args:
            input_text: The math expression to evaluate.
            **kwargs: Additional arguments (unused).

        Returns:
            A Trace capturing the execution.
        """
        output = self._compute(input_text)

        call = LLMCall(
            model="calculator-v1",
            input_tokens=len(input_text.split()),
            output_tokens=len(output.split()),
            input_text=input_text,
            output_text=output,
            latency_ms=5,
        )

        return Trace(
            trace_id=str(uuid4()),
            agent_name=self.name,
            model="calculator-v1",
            input_text=input_text,
            output_text=output,
            llm_calls=(call,),
            total_input_tokens=call.input_tokens,
            total_output_tokens=call.output_tokens,
            total_latency_ms=5,
            created_at=datetime.now(UTC),
        )


async def main() -> None:
    """Demonstrate using a custom adapter with the test runner."""
    adapter = CalculatorAdapter()

    # Define test cases
    tests = [
        TestCase(
            name="addition",
            input_text="2 + 3",
            expected_output="5",
        ),
        TestCase(
            name="multiplication",
            input_text="7 * 8",
            expected_output="56",
        ),
        TestCase(
            name="complex_expression",
            input_text="(10 + 5) * 2",
            expected_output="30",
        ),
    ]

    # Set up evaluator
    evaluator = RuleBasedEvaluator(
        rules=[{"type": "exact_match"}],
    )

    # Run tests
    _ = (EvalVerdict, TurnType, TestStatus)  # ensure imports are used
    runner = TestRunner(evaluators=[evaluator])
    run = await runner.run(test_cases=tests, adapter=adapter)

    print("=== Custom Adapter Test Results ===")
    print(f"Agent: {run.agent_name}")
    print(f"Total: {run.total_tests} | Passed: {run.passed} | Failed: {run.failed}")
    for result in run.test_results:
        symbol = "pass" if result.status == TestStatus.PASSED else "FAIL"
        print(f"  [{symbol}] {result.test_name}: score={result.score:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
