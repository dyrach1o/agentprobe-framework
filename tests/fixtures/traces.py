"""Factory functions for creating test traces and related objects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from agentprobe.core.models import (
    ChaosOverride,
    ChaosType,
    ConversationResult,
    DiffItem,
    EvalResult,
    LLMCall,
    MetricDefinition,
    MetricType,
    MetricValue,
    ReplayDiff,
    SnapshotDiff,
    StatisticalSummary,
    ToolCall,
    Trace,
    TraceStep,
    Turn,
    TurnResult,
    TurnType,
)


def make_llm_call(
    *,
    model: str = "test-model",
    input_tokens: int = 100,
    output_tokens: int = 50,
    input_text: str = "test prompt",
    output_text: str = "test response",
    latency_ms: int = 200,
    metadata: dict[str, Any] | None = None,
    call_id: str | None = None,
) -> LLMCall:
    """Create an LLMCall with sensible defaults for testing."""
    kwargs: dict[str, Any] = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_text": input_text,
        "output_text": output_text,
        "latency_ms": latency_ms,
        "metadata": metadata or {},
    }
    if call_id is not None:
        kwargs["call_id"] = call_id
    return LLMCall(**kwargs)


def make_tool_call(
    *,
    tool_name: str = "test_tool",
    tool_input: dict[str, Any] | None = None,
    tool_output: Any = "tool result",
    success: bool = True,
    error: str | None = None,
    latency_ms: int = 50,
    call_id: str | None = None,
) -> ToolCall:
    """Create a ToolCall with sensible defaults for testing."""
    kwargs: dict[str, Any] = {
        "tool_name": tool_name,
        "tool_input": tool_input or {},
        "tool_output": tool_output,
        "success": success,
        "error": error,
        "latency_ms": latency_ms,
    }
    if call_id is not None:
        kwargs["call_id"] = call_id
    return ToolCall(**kwargs)


def make_turn(
    *,
    turn_type: TurnType = TurnType.LLM_CALL,
    content: str = "test content",
    llm_call: LLMCall | None = None,
    tool_call: ToolCall | None = None,
) -> Turn:
    """Create a Turn with sensible defaults for testing."""
    return Turn(
        turn_type=turn_type,
        content=content,
        llm_call=llm_call,
        tool_call=tool_call,
    )


def make_trace(
    *,
    agent_name: str = "test-agent",
    model: str | None = "test-model",
    input_text: str = "test input",
    output_text: str = "test output",
    llm_calls: list[LLMCall] | None = None,
    tool_calls: list[ToolCall] | None = None,
    turns: list[Turn] | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    trace_id: str | None = None,
    created_at: datetime | None = None,
) -> Trace:
    """Create a Trace with sensible defaults for testing.

    Automatically computes token totals from LLM calls if not overridden.
    """
    resolved_llm_calls = llm_calls or []
    resolved_tool_calls = tool_calls or []

    total_input = sum(c.input_tokens for c in resolved_llm_calls)
    total_output = sum(c.output_tokens for c in resolved_llm_calls)
    total_latency = sum(c.latency_ms for c in resolved_llm_calls) + sum(
        c.latency_ms for c in resolved_tool_calls
    )

    kwargs: dict[str, Any] = {
        "agent_name": agent_name,
        "model": model,
        "input_text": input_text,
        "output_text": output_text,
        "llm_calls": tuple(resolved_llm_calls),
        "tool_calls": tuple(resolved_tool_calls),
        "turns": tuple(turns or []),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_latency_ms": total_latency,
        "tags": tuple(tags or []),
        "metadata": metadata or {},
    }
    if trace_id is not None:
        kwargs["trace_id"] = trace_id
    if created_at is not None:
        kwargs["created_at"] = created_at
    else:
        kwargs["created_at"] = datetime.now(UTC)
    return Trace(**kwargs)


def make_turn_result(
    *,
    turn_index: int = 0,
    input_text: str = "test turn input",
    trace: Trace | None = None,
    eval_results: list[EvalResult] | None = None,
    duration_ms: int = 100,
) -> TurnResult:
    """Create a TurnResult with sensible defaults for testing."""
    return TurnResult(
        turn_index=turn_index,
        input_text=input_text,
        trace=trace,
        eval_results=tuple(eval_results or []),
        duration_ms=duration_ms,
    )


def make_conversation_result(
    *,
    agent_name: str = "test-agent",
    turn_results: list[TurnResult] | None = None,
    total_turns: int | None = None,
    passed_turns: int | None = None,
    aggregate_score: float = 0.8,
    total_duration_ms: int = 500,
) -> ConversationResult:
    """Create a ConversationResult with sensible defaults for testing."""
    resolved_turns = turn_results or []
    return ConversationResult(
        agent_name=agent_name,
        turn_results=tuple(resolved_turns),
        total_turns=total_turns if total_turns is not None else len(resolved_turns),
        passed_turns=passed_turns if passed_turns is not None else len(resolved_turns),
        aggregate_score=aggregate_score,
        total_duration_ms=total_duration_ms,
    )


def make_statistical_summary(
    *,
    evaluator_name: str = "test-evaluator",
    scores: tuple[float, ...] = (0.8, 0.85, 0.9, 0.75, 0.88),
    mean: float = 0.836,
    std_dev: float = 0.057,
    median: float = 0.85,
    p5: float = 0.75,
    p95: float = 0.9,
    ci_lower: float = 0.786,
    ci_upper: float = 0.886,
) -> StatisticalSummary:
    """Create a StatisticalSummary with sensible defaults for testing."""
    return StatisticalSummary(
        evaluator_name=evaluator_name,
        sample_count=len(scores),
        scores=scores,
        mean=mean,
        std_dev=std_dev,
        median=median,
        p5=p5,
        p95=p95,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
    )


def make_metric_definition(
    *,
    name: str = "latency_ms",
    metric_type: MetricType = MetricType.LATENCY,
    description: str = "Request latency in milliseconds",
    unit: str = "ms",
    lower_is_better: bool = True,
) -> MetricDefinition:
    """Create a MetricDefinition with sensible defaults for testing."""
    return MetricDefinition(
        name=name,
        metric_type=metric_type,
        description=description,
        unit=unit,
        lower_is_better=lower_is_better,
    )


def make_metric_value(
    *,
    metric_name: str = "latency_ms",
    value: float = 150.0,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> MetricValue:
    """Create a MetricValue with sensible defaults for testing."""
    return MetricValue(
        metric_name=metric_name,
        value=value,
        tags=tuple(tags or []),
        metadata=metadata or {},
    )


def make_diff_item(
    *,
    dimension: str = "output",
    expected: Any = "expected value",
    actual: Any = "actual value",
    similarity: float = 0.85,
) -> DiffItem:
    """Create a DiffItem with sensible defaults for testing."""
    return DiffItem(
        dimension=dimension,
        expected=expected,
        actual=actual,
        similarity=similarity,
    )


def make_snapshot_diff(
    *,
    snapshot_name: str = "test-snapshot",
    overall_similarity: float = 0.9,
    diffs: list[DiffItem] | None = None,
    is_match: bool = True,
    threshold: float = 0.8,
) -> SnapshotDiff:
    """Create a SnapshotDiff with sensible defaults for testing."""
    return SnapshotDiff(
        snapshot_name=snapshot_name,
        overall_similarity=overall_similarity,
        diffs=tuple(diffs or []),
        is_match=is_match,
        threshold=threshold,
    )


def make_trace_step(
    *,
    step_index: int = 0,
    turn: Turn | None = None,
    cumulative_input_tokens: int = 100,
    cumulative_output_tokens: int = 50,
    cumulative_cost_usd: float = 0.005,
    cumulative_latency_ms: int = 200,
) -> TraceStep:
    """Create a TraceStep with sensible defaults for testing."""
    return TraceStep(
        step_index=step_index,
        turn=turn or make_turn(),
        cumulative_input_tokens=cumulative_input_tokens,
        cumulative_output_tokens=cumulative_output_tokens,
        cumulative_cost_usd=cumulative_cost_usd,
        cumulative_latency_ms=cumulative_latency_ms,
    )


def make_replay_diff(
    *,
    original_trace_id: str = "orig-trace-1",
    replay_trace_id: str = "replay-trace-1",
    tool_call_diffs: list[DiffItem] | None = None,
    output_matches: bool = True,
    original_output: str = "original output",
    replay_output: str = "original output",
) -> ReplayDiff:
    """Create a ReplayDiff with sensible defaults for testing."""
    return ReplayDiff(
        original_trace_id=original_trace_id,
        replay_trace_id=replay_trace_id,
        tool_call_diffs=tuple(tool_call_diffs or []),
        output_matches=output_matches,
        original_output=original_output,
        replay_output=replay_output,
    )


def make_chaos_override(
    *,
    chaos_type: ChaosType = ChaosType.ERROR,
    probability: float = 1.0,
    target_tool: str | None = None,
    delay_ms: int = 5000,
    error_message: str = "Chaos fault injected",
) -> ChaosOverride:
    """Create a ChaosOverride with sensible defaults for testing."""
    return ChaosOverride(
        chaos_type=chaos_type,
        probability=probability,
        target_tool=target_tool,
        delay_ms=delay_ms,
        error_message=error_message,
    )
