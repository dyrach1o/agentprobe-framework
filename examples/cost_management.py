#!/usr/bin/env python3
"""Example: Cost tracking and budget enforcement.

Demonstrates how to use CostCalculator for per-trace cost analysis
and BudgetEnforcer for setting per-test and per-suite cost limits.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from agentprobe.core.models import (
    LLMCall,
    TestStatus,
    Trace,
)
from agentprobe.cost.budget import BudgetEnforcer
from agentprobe.cost.calculator import CostCalculator


def _build_trace(model: str, input_tokens: int, output_tokens: int) -> Trace:
    """Create a synthetic trace with a single LLM call for cost analysis."""
    call = LLMCall(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_text="sample prompt",
        output_text="sample response",
        latency_ms=200,
    )
    return Trace(
        trace_id=str(uuid4()),
        agent_name="cost-demo-agent",
        model=model,
        llm_calls=(call,),
        total_input_tokens=input_tokens,
        total_output_tokens=output_tokens,
        total_latency_ms=200,
        created_at=datetime.now(UTC),
    )


async def main() -> None:
    """Run the cost management demonstration."""
    # Set up a calculator with built-in pricing data
    calculator = CostCalculator()

    # Calculate cost for a single trace
    trace = _build_trace("claude-sonnet-4-5-20250929", input_tokens=2000, output_tokens=1000)
    summary = calculator.calculate_trace_cost(trace)

    print("=== Cost Summary ===")
    print(f"Total cost: ${summary.total_cost_usd:.6f}")
    print(f"Input tokens: {summary.total_input_tokens}")
    print(f"Output tokens: {summary.total_output_tokens}")
    for model_name, breakdown in summary.breakdown_by_model.items():
        print(f"  {model_name}: ${breakdown.total_cost_usd:.6f} ({breakdown.call_count} calls)")

    # Budget enforcement
    enforcer = BudgetEnforcer(test_budget_usd=0.10, suite_budget_usd=1.00)

    test_check = enforcer.check_test(summary)
    if test_check is not None:
        status = "WITHIN" if test_check.within_budget else "EXCEEDED"
        print(f"\nTest budget: {status}")
        print(f"  Actual: ${test_check.actual_cost_usd:.6f}")
        print(f"  Limit:  ${test_check.budget_limit_usd:.6f}")
        print(f"  Used:   {test_check.utilization_pct:.1f}%")

    # Suite-level check across multiple traces
    summaries = [
        calculator.calculate_trace_cost(
            _build_trace("claude-sonnet-4-5-20250929", input_tokens=1000, output_tokens=500)
        )
        for _ in range(5)
    ]
    suite_check = enforcer.check_suite(summaries)
    if suite_check is not None:
        status = "WITHIN" if suite_check.within_budget else "EXCEEDED"
        _ = TestStatus.PASSED  # suppress unused import if needed
        print(f"\nSuite budget: {status}")
        print(f"  Total:  ${suite_check.actual_cost_usd:.6f}")
        print(f"  Limit:  ${suite_check.budget_limit_usd:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
