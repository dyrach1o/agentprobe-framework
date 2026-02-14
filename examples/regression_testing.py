"""Regression testing example: Baseline save → compare → detect regressions.

This example demonstrates how to:
1. Run tests and save a baseline
2. Run tests again with different parameters
3. Compare results and detect regressions

Usage:
    python examples/regression_testing.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from agentprobe.core.models import TestCase, Trace
from agentprobe.core.runner import TestRunner
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec
from agentprobe.regression.baseline import BaselineManager
from agentprobe.regression.detector import RegressionDetector


# ── Demo adapters ──
class StableAdapter:
    """An adapter that always gives good answers."""

    @property
    def name(self) -> str:
        return "stable-agent"

    async def invoke(self, input_text: str, **kwargs: object) -> Trace:
        return Trace(
            agent_name=self.name,
            input_text=input_text,
            output_text="The capital of France is Paris.",
        )


class RegressedAdapter:
    """An adapter that sometimes gives bad answers (simulating regression)."""

    @property
    def name(self) -> str:
        return "regressed-agent"

    async def invoke(self, input_text: str, **kwargs: object) -> Trace:
        # Simulate a regression: the agent now gives wrong answers for some queries
        if "capital" in input_text.lower():
            return Trace(
                agent_name=self.name,
                input_text=input_text,
                output_text="I'm not sure about that.",
            )
        return Trace(
            agent_name=self.name,
            input_text=input_text,
            output_text="The capital of France is Paris.",
        )


async def main() -> None:
    """Run the regression testing example."""
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_dir = Path(tmpdir) / "baselines"
        manager = BaselineManager(baseline_dir=baseline_dir)
        detector = RegressionDetector(threshold=0.05)

        evaluator = RuleBasedEvaluator(
            name="accuracy",
            rules=[
                RuleSpec(
                    rule_type="contains_any",
                    params={"values": ["Paris"]},
                    description="Answer should contain Paris",
                ),
            ],
        )

        test_cases = [
            TestCase(name="test_capital", input_text="What is the capital of France?"),
            TestCase(name="test_greeting", input_text="Hello, how are you?"),
        ]

        # ── Step 1: Establish baseline with stable adapter ──
        print("Step 1: Establishing baseline...")
        runner = TestRunner(evaluators=[evaluator])
        baseline_run = await runner.run(test_cases, StableAdapter())

        manager.save("v1.0", list(baseline_run.test_results))
        print(f"  Baseline saved: {baseline_run.passed}/{baseline_run.total_tests} passed")

        # ── Step 2: Run with regressed adapter ──
        print("\nStep 2: Running with updated agent...")
        current_run = await runner.run(test_cases, RegressedAdapter())
        print(f"  Current run: {current_run.passed}/{current_run.total_tests} passed")

        # ── Step 3: Compare and detect regressions ──
        print("\nStep 3: Comparing results...")
        baseline_results = manager.load("v1.0")
        report = detector.compare("v1.0", baseline_results, list(current_run.test_results))

        print(f"\n{'=' * 50}")
        print("Regression Report")
        print(f"{'=' * 50}")
        print(f"  Baseline:     {report.baseline_name}")
        print(f"  Total tests:  {report.total_tests}")
        print(f"  Regressions:  {report.regressions}")
        print(f"  Improvements: {report.improvements}")
        print(f"  Unchanged:    {report.unchanged}")
        print(f"  Threshold:    {report.threshold}")

        for comp in report.comparisons:
            if comp.is_regression:
                status = "REGRESSION"
            elif comp.is_improvement:
                status = "IMPROVED"
            else:
                status = "UNCHANGED"
            print(f"\n  {comp.test_name}: {status}")
            print(f"    Baseline: {comp.baseline_score:.2f} → Current: {comp.current_score:.2f}")
            print(f"    Delta: {comp.delta:+.3f}")


if __name__ == "__main__":
    asyncio.run(main())
