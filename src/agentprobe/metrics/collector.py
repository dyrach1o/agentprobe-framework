"""Stateless metric collector that extracts measurements from traces and results.

Converts traces, test results, and agent runs into MetricValue instances
for storage and analysis.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from agentprobe.core.models import (
    AgentRun,
    MetricValue,
    TestResult,
    TestStatus,
    Trace,
)

logger = logging.getLogger(__name__)


class MetricCollector:
    """Extracts metric values from traces, results, and runs.

    Stateless: receives objects and returns lists of MetricValue.
    Does not store or persist anything.
    """

    def collect_from_trace(self, trace: Trace) -> list[MetricValue]:
        """Extract metric values from a single trace.

        Collects latency, tool call count, and response length metrics.

        Args:
            trace: The execution trace to extract metrics from.

        Returns:
            A list of metric values extracted from the trace.
        """
        now = datetime.now(UTC)
        tags = tuple(trace.tags)
        metrics: list[MetricValue] = []

        metrics.append(
            MetricValue(
                metric_name="latency_ms",
                value=float(trace.total_latency_ms),
                tags=tags,
                metadata={"trace_id": trace.trace_id, "agent_name": trace.agent_name},
                timestamp=now,
            )
        )

        metrics.append(
            MetricValue(
                metric_name="tool_call_count",
                value=float(len(trace.tool_calls)),
                tags=tags,
                metadata={"trace_id": trace.trace_id, "agent_name": trace.agent_name},
                timestamp=now,
            )
        )

        metrics.append(
            MetricValue(
                metric_name="response_length",
                value=float(len(trace.output_text)),
                tags=tags,
                metadata={"trace_id": trace.trace_id, "agent_name": trace.agent_name},
                timestamp=now,
            )
        )

        return metrics

    def collect_from_result(self, result: TestResult) -> list[MetricValue]:
        """Extract metric values from a test result.

        Collects latency, eval score, and any trace-level metrics.

        Args:
            result: The test result to extract metrics from.

        Returns:
            A list of metric values extracted from the result.
        """
        now = datetime.now(UTC)
        metrics: list[MetricValue] = []

        metrics.append(
            MetricValue(
                metric_name="latency_ms",
                value=float(result.duration_ms),
                metadata={"test_name": result.test_name, "result_id": result.result_id},
                timestamp=now,
            )
        )

        metrics.append(
            MetricValue(
                metric_name="eval_score",
                value=result.score,
                metadata={"test_name": result.test_name, "result_id": result.result_id},
                timestamp=now,
            )
        )

        if result.trace is not None:
            trace_metrics = self.collect_from_trace(result.trace)
            metrics.extend(trace_metrics)

        return metrics

    def collect_from_run(self, run: AgentRun) -> list[MetricValue]:
        """Extract metric values from a complete agent run.

        Collects pass rate plus per-result metrics for all results.

        Args:
            run: The agent run to extract metrics from.

        Returns:
            A list of metric values extracted from the run.
        """
        now = datetime.now(UTC)
        metrics: list[MetricValue] = []

        if run.total_tests > 0:
            passed = sum(1 for r in run.test_results if r.status == TestStatus.PASSED)
            pass_rate = passed / run.total_tests
        else:
            pass_rate = 0.0

        metrics.append(
            MetricValue(
                metric_name="pass_rate",
                value=pass_rate,
                metadata={"run_id": run.run_id, "agent_name": run.agent_name},
                timestamp=now,
            )
        )

        for result in run.test_results:
            result_metrics = self.collect_from_result(result)
            metrics.extend(result_metrics)

        return metrics
