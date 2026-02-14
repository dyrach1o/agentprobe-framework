#!/usr/bin/env python3
"""Example: Metric collection, aggregation, and trend analysis.

Demonstrates how to use MetricCollector to extract metrics from traces
and results, MetricAggregator for statistical summaries, and
MetricTrend for detecting performance changes over time.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from agentprobe.core.models import (
    EvalResult,
    EvalVerdict,
    LLMCall,
    MetricValue,
    TestResult,
    TestStatus,
    Trace,
)
from agentprobe.metrics.aggregator import MetricAggregator
from agentprobe.metrics.collector import MetricCollector
from agentprobe.metrics.trend import MetricTrend


def _build_sample_result(latency_ms: int, score: float) -> TestResult:
    """Create a test result with a trace for metric collection."""
    call = LLMCall(
        model="test-model",
        input_tokens=100,
        output_tokens=50,
        latency_ms=latency_ms,
    )
    trace = Trace(
        trace_id=str(uuid4()),
        agent_name="metrics-demo",
        llm_calls=(call,),
        total_input_tokens=100,
        total_output_tokens=50,
        total_latency_ms=latency_ms,
        created_at=datetime.now(UTC),
    )
    return TestResult(
        test_name="demo_test",
        status=TestStatus.PASSED,
        score=score,
        duration_ms=latency_ms,
        trace=trace,
        eval_results=(
            EvalResult(
                evaluator_name="rules",
                verdict=EvalVerdict.PASS,
                score=score,
            ),
        ),
    )


async def main() -> None:
    """Run the metrics trending demonstration."""
    collector = MetricCollector()
    aggregator = MetricAggregator()
    trend = MetricTrend()

    # Collect metrics from several test results
    all_metrics: list[MetricValue] = []
    latencies = [150, 180, 120, 200, 160, 140, 190, 130, 170, 155]
    scores = [0.9, 0.85, 0.95, 0.80, 0.88, 0.92, 0.82, 0.91, 0.87, 0.89]

    for lat, sc in zip(latencies, scores, strict=True):
        result = _build_sample_result(latency_ms=lat, score=sc)
        metrics = collector.collect_from_result(result)
        all_metrics.extend(metrics)

    print(f"Collected {len(all_metrics)} metric values")

    # Aggregate by metric name
    aggregations = aggregator.aggregate_by_name(all_metrics)
    print("\n=== Metric Aggregations ===")
    for name, agg in aggregations.items():
        print(
            f"  {name}: mean={agg.mean:.2f}, median={agg.median:.2f}, "
            f"p95={agg.p95:.2f}, count={agg.count}"
        )

    # Trend analysis: simulate improving latency over time
    base_time = datetime.now(UTC)
    latency_values = [
        MetricValue(
            metric_name="latency_ms",
            value=float(200 - i * 5),
            timestamp=base_time + timedelta(hours=i),
        )
        for i in range(20)
    ]

    trend_result = trend.analyze(latency_values, lower_is_better=True)
    print("\n=== Trend Analysis (latency_ms) ===")
    print(f"  Direction: {trend_result.direction}")
    print(f"  Slope: {trend_result.slope:.4f}")
    print(f"  Confidence: {trend_result.confidence:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
