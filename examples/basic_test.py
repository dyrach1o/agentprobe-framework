"""Basic test example: TestCase + MockAdapter + RuleBasedEvaluator + TestRunner.

This standalone example demonstrates the core testing workflow:
1. Define test cases
2. Create a mock adapter (replace with your real agent adapter)
3. Configure evaluators
4. Run the tests and inspect results

Usage:
    python examples/basic_test.py
"""

from __future__ import annotations

import asyncio

from agentprobe.core.models import LLMCall, TestCase, Trace
from agentprobe.core.runner import TestRunner
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec


# ── Step 1: Define a simple adapter ──
# In production, replace this with your real agent adapter.
class DemoAdapter:
    """A simple adapter that echoes back a canned response."""

    @property
    def name(self) -> str:
        return "demo-agent"

    async def invoke(self, input_text: str, **kwargs: object) -> Trace:
        return Trace(
            agent_name=self.name,
            input_text=input_text,
            output_text=f"The answer to '{input_text}' is 42.",
            llm_calls=(
                LLMCall(
                    model="demo-model",
                    input_tokens=len(input_text.split()) * 2,
                    output_tokens=10,
                    input_text=input_text,
                    output_text=f"The answer to '{input_text}' is 42.",
                    latency_ms=50,
                ),
            ),
        )


async def main() -> None:
    """Run the basic test example."""
    # ── Step 2: Define test cases ──
    test_cases = [
        TestCase(
            name="test_contains_answer",
            input_text="What is the meaning of life?",
        ),
        TestCase(
            name="test_reasonable_length",
            input_text="Give me a short answer",
        ),
    ]

    # ── Step 3: Configure evaluators ──
    evaluator = RuleBasedEvaluator(
        name="basic-rules",
        rules=[
            RuleSpec(
                rule_type="contains_any",
                params={"values": ["42", "answer"]},
                description="Output should contain the answer",
            ),
            RuleSpec(
                rule_type="max_length",
                params={"max": 500},
                description="Output should be concise",
            ),
        ],
    )

    # ── Step 4: Run tests ──
    runner = TestRunner(evaluators=[evaluator])
    adapter = DemoAdapter()

    run = await runner.run(test_cases, adapter)

    # ── Step 5: Inspect results ──
    print(f"Agent: {run.agent_name}")
    print(f"Status: {run.status.value}")
    print(f"Total: {run.total_tests} | Passed: {run.passed} | Failed: {run.failed}")
    print(f"Duration: {run.duration_ms}ms")
    print()

    for result in run.test_results:
        status_icon = "PASS" if result.status.value == "passed" else "FAIL"
        print(f"  [{status_icon}] {result.test_name} (score={result.score:.2f})")
        for er in result.eval_results:
            print(f"         {er.evaluator_name}: {er.verdict.value} — {er.reason}")


if __name__ == "__main__":
    asyncio.run(main())
