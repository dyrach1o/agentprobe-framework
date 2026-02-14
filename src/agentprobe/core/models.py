"""Core data models and enumerations for AgentProbe.

This module defines all Pydantic models used throughout the framework,
including traces, test cases, results, and cost summaries. Output types
are frozen (immutable); input/configuration types are mutable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Enumerations ──


class TestStatus(StrEnum):
    """Status of a single test case execution."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class RunStatus(StrEnum):
    """Status of an overall agent run or test suite execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TurnType(StrEnum):
    """Type of event within a trace turn."""

    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"


class EvalVerdict(StrEnum):
    """Verdict produced by an evaluator."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    ERROR = "error"


# ── Trace Models (frozen — assembled once, never mutated) ──


class LLMCall(BaseModel):
    """A single call to a language model within a trace.

    Attributes:
        call_id: Unique identifier for this call.
        model: Model identifier string (e.g. 'claude-sonnet-4-5-20250929').
        input_tokens: Number of input/prompt tokens consumed.
        output_tokens: Number of output/completion tokens produced.
        input_text: The prompt or input sent to the model.
        output_text: The response text from the model.
        latency_ms: Round-trip latency in milliseconds.
        metadata: Additional provider-specific metadata.
        timestamp: When the call was made.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    call_id: str = Field(default_factory=lambda: str(uuid4()))
    model: str
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    input_text: str = ""
    output_text: str = ""
    latency_ms: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolCall(BaseModel):
    """A single tool invocation within a trace.

    Attributes:
        call_id: Unique identifier for this call.
        tool_name: Name of the tool invoked.
        tool_input: Arguments passed to the tool.
        tool_output: Output returned by the tool.
        success: Whether the tool call succeeded.
        error: Error message if the call failed.
        latency_ms: Round-trip latency in milliseconds.
        timestamp: When the call was made.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    call_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: Any = None
    success: bool = True
    error: str | None = None
    latency_ms: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Turn(BaseModel):
    """A single turn (event) within a trace timeline.

    Attributes:
        turn_id: Unique identifier for this turn.
        turn_type: The type of event this turn represents.
        content: Text content of the turn.
        llm_call: Associated LLM call, if this is an LLM turn.
        tool_call: Associated tool call, if this is a tool turn.
        timestamp: When the turn occurred.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    turn_id: str = Field(default_factory=lambda: str(uuid4()))
    turn_type: TurnType
    content: str = ""
    llm_call: LLMCall | None = None
    tool_call: ToolCall | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Trace(BaseModel):
    """Complete execution trace of an agent run.

    A trace captures the full timeline of LLM calls, tool invocations,
    and message exchanges during a single agent execution. Once assembled
    by the TraceRecorder, traces are immutable.

    Attributes:
        trace_id: Unique identifier for this trace.
        agent_name: Name of the agent that produced this trace.
        model: Primary model used during the run.
        input_text: The input/prompt given to the agent.
        output_text: The final output produced by the agent.
        turns: Ordered list of turns in the execution timeline.
        llm_calls: All LLM calls made during the run.
        tool_calls: All tool calls made during the run.
        total_input_tokens: Aggregate input tokens across all LLM calls.
        total_output_tokens: Aggregate output tokens across all LLM calls.
        total_latency_ms: Total execution time in milliseconds.
        tags: Tags for filtering and grouping.
        metadata: Additional run metadata.
        created_at: When the trace was created.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    model: str | None = None
    input_text: str = ""
    output_text: str = ""
    turns: tuple[Turn, ...] = ()
    llm_calls: tuple[LLMCall, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    total_input_tokens: int = Field(default=0, ge=0)
    total_output_tokens: int = Field(default=0, ge=0)
    total_latency_ms: int = Field(default=0, ge=0)
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Evaluation Models (frozen) ──


class EvalResult(BaseModel):
    """Result produced by an evaluator.

    Attributes:
        eval_id: Unique identifier for this evaluation.
        evaluator_name: Name of the evaluator that produced this result.
        verdict: Pass/fail/partial/error verdict.
        score: Numeric score between 0.0 and 1.0.
        reason: Human-readable explanation of the verdict.
        metadata: Additional evaluator-specific data.
        created_at: When the evaluation was performed.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    eval_id: str = Field(default_factory=lambda: str(uuid4()))
    evaluator_name: str
    verdict: EvalVerdict
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AssertionResult(BaseModel):
    """Result of a single test assertion.

    Attributes:
        assertion_type: Type of assertion (e.g. 'contain', 'match').
        passed: Whether the assertion passed.
        expected: The expected value.
        actual: The actual value.
        message: Descriptive message about the result.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    assertion_type: str
    passed: bool
    expected: Any = None
    actual: Any = None
    message: str = ""


# ── Test Models ──


class TestCase(BaseModel):
    """A single test scenario to be executed against an agent.

    TestCase is mutable because the runner populates fields during execution
    (e.g. status transitions, attaching results).

    Attributes:
        test_id: Unique identifier for this test case.
        name: Human-readable name (usually from the @scenario decorator).
        description: Detailed description of what this test validates.
        input_text: The input prompt to send to the agent.
        expected_output: Optional expected output for comparison.
        tags: Tags for filtering and grouping.
        timeout_seconds: Maximum allowed execution time.
        evaluators: Names of evaluators to run on this test.
        metadata: Additional test configuration.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    test_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    input_text: str = ""
    expected_output: str | None = None
    tags: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=30.0, gt=0)
    evaluators: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure test name contains only valid characters."""
        cleaned = v.replace("_", "").replace("-", "").replace(" ", "")
        if not cleaned.replace(".", "").isalnum():
            msg = "Test name must be alphanumeric with underscores, hyphens, spaces, or dots"
            raise ValueError(msg)
        return v


class TestResult(BaseModel):
    """Complete result of executing a single test case.

    Attributes:
        result_id: Unique identifier for this result.
        test_name: Name of the test that was executed.
        status: Final status of the test execution.
        score: Aggregate score from evaluators (0.0 to 1.0).
        duration_ms: Execution time in milliseconds.
        trace: The execution trace, if recording was enabled.
        eval_results: Results from all evaluators run on this test.
        assertion_results: Results from all assertions.
        error_message: Error description if the test errored.
        created_at: When the result was recorded.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    result_id: str = Field(default_factory=lambda: str(uuid4()))
    test_name: str = Field(..., min_length=1, max_length=200)
    status: TestStatus
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_ms: int = Field(default=0, ge=0)
    trace: Trace | None = None
    eval_results: tuple[EvalResult, ...] = ()
    assertion_results: tuple[AssertionResult, ...] = ()
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Aggregate Models (frozen) ──


class CostBreakdown(BaseModel):
    """Cost breakdown for a single model.

    Attributes:
        model: The model identifier.
        input_tokens: Total input tokens for this model.
        output_tokens: Total output tokens for this model.
        input_cost_usd: Cost for input tokens in USD.
        output_cost_usd: Cost for output tokens in USD.
        total_cost_usd: Total cost in USD.
        call_count: Number of calls to this model.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    model: str
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    input_cost_usd: float = Field(default=0.0, ge=0.0)
    output_cost_usd: float = Field(default=0.0, ge=0.0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    call_count: int = Field(default=0, ge=0)


class CostSummary(BaseModel):
    """Aggregate cost summary for a trace or test suite.

    Attributes:
        total_llm_cost_usd: Total cost of all LLM calls in USD.
        total_tool_cost_usd: Total cost of tool usage in USD.
        total_cost_usd: Grand total cost in USD.
        breakdown_by_model: Per-model cost breakdown.
        total_input_tokens: Aggregate input tokens.
        total_output_tokens: Aggregate output tokens.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    total_llm_cost_usd: float = Field(default=0.0, ge=0.0)
    total_tool_cost_usd: float = Field(default=0.0, ge=0.0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    breakdown_by_model: dict[str, CostBreakdown] = Field(default_factory=dict)
    total_input_tokens: int = Field(default=0, ge=0)
    total_output_tokens: int = Field(default=0, ge=0)


class MetricType(StrEnum):
    """Type of metric being measured."""

    LATENCY = "latency"
    COST = "cost"
    TOKENS = "tokens"
    SCORE = "score"
    COUNT = "count"
    RATE = "rate"


class TrendDirection(StrEnum):
    """Direction of a metric trend over time."""

    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class PluginType(StrEnum):
    """Type of plugin extension."""

    EVALUATOR = "evaluator"
    ADAPTER = "adapter"
    REPORTER = "reporter"
    STORAGE = "storage"


class ChaosType(StrEnum):
    """Type of chaos fault to inject during testing."""

    TIMEOUT = "timeout"
    ERROR = "error"
    MALFORMED = "malformed"
    RATE_LIMIT = "rate_limit"
    SLOW = "slow"
    EMPTY = "empty"


# ── Conversation Models (frozen) ──


class ConversationTurn(BaseModel):
    """Specification for a single turn in a multi-turn conversation test.

    Attributes:
        turn_id: Unique identifier for this turn.
        input_text: The input to send for this turn.
        expected_output: Optional expected output for this turn.
        evaluators: Evaluator names to run on this turn's result.
        metadata: Additional turn-level configuration.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    turn_id: str = Field(default_factory=lambda: str(uuid4()))
    input_text: str
    expected_output: str | None = None
    evaluators: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class TurnResult(BaseModel):
    """Result from executing a single conversation turn.

    Attributes:
        turn_index: Zero-based index of this turn.
        input_text: The input sent for this turn.
        trace: Execution trace from this turn.
        eval_results: Results from evaluators run on this turn.
        duration_ms: Execution time for this turn in milliseconds.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    turn_index: int = Field(ge=0)
    input_text: str = ""
    trace: Trace | None = None
    eval_results: tuple[EvalResult, ...] = ()
    duration_ms: int = Field(default=0, ge=0)


class ConversationResult(BaseModel):
    """Aggregate result from a multi-turn conversation test.

    Attributes:
        conversation_id: Unique identifier for this conversation.
        agent_name: Name of the agent tested.
        turn_results: Per-turn results in order.
        total_turns: Number of turns executed.
        passed_turns: Number of turns where all evaluators passed.
        aggregate_score: Mean score across all turns.
        total_duration_ms: Total execution time in milliseconds.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    turn_results: tuple[TurnResult, ...] = ()
    total_turns: int = Field(default=0, ge=0)
    passed_turns: int = Field(default=0, ge=0)
    aggregate_score: float = Field(default=0.0, ge=0.0, le=1.0)
    total_duration_ms: int = Field(default=0, ge=0)


# ── Statistical Models (frozen) ──


class StatisticalSummary(BaseModel):
    """Summary statistics from repeated evaluations.

    Attributes:
        evaluator_name: Name of the evaluator that produced these stats.
        sample_count: Number of evaluation runs.
        scores: Raw scores from each run (for reproducibility).
        mean: Arithmetic mean of scores.
        std_dev: Standard deviation of scores.
        median: Median score.
        p5: 5th percentile score.
        p95: 95th percentile score.
        ci_lower: Lower bound of 95% confidence interval.
        ci_upper: Upper bound of 95% confidence interval.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    evaluator_name: str
    sample_count: int = Field(ge=1)
    scores: tuple[float, ...] = ()
    mean: float = Field(default=0.0, ge=0.0, le=1.0)
    std_dev: float = Field(default=0.0, ge=0.0)
    median: float = Field(default=0.0, ge=0.0, le=1.0)
    p5: float = Field(default=0.0, ge=0.0, le=1.0)
    p95: float = Field(default=0.0, ge=0.0, le=1.0)
    ci_lower: float = Field(default=0.0, ge=0.0, le=1.0)
    ci_upper: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Regression Models (frozen) ──


class TestComparison(BaseModel):
    """Comparison of a single test between baseline and current results.

    Attributes:
        test_name: Name of the compared test.
        baseline_score: Score from the baseline run.
        current_score: Score from the current run.
        delta: Score change (current - baseline).
        is_regression: Whether the change constitutes a regression.
        is_improvement: Whether the change constitutes an improvement.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    test_name: str
    baseline_score: float = Field(ge=0.0, le=1.0)
    current_score: float = Field(ge=0.0, le=1.0)
    delta: float = 0.0
    is_regression: bool = False
    is_improvement: bool = False


class RegressionReport(BaseModel):
    """Report from comparing current results against a baseline.

    Attributes:
        baseline_name: Name of the baseline used for comparison.
        comparisons: Per-test comparisons.
        total_tests: Number of tests compared.
        regressions: Number of tests that regressed.
        improvements: Number of tests that improved.
        unchanged: Number of tests with no significant change.
        threshold: Score delta threshold used for regression detection.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    baseline_name: str
    comparisons: tuple[TestComparison, ...] = ()
    total_tests: int = Field(default=0, ge=0)
    regressions: int = Field(default=0, ge=0)
    improvements: int = Field(default=0, ge=0)
    unchanged: int = Field(default=0, ge=0)
    threshold: float = Field(default=0.05, ge=0.0, le=1.0)


# ── Budget Models (frozen) ──


class BudgetCheckResult(BaseModel):
    """Result of checking a cost against a budget.

    Attributes:
        within_budget: Whether the cost is within the budget.
        actual_cost_usd: The actual cost incurred.
        budget_limit_usd: The budget limit.
        remaining_usd: Budget remaining (may be negative if exceeded).
        utilization_pct: Percentage of budget used.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    within_budget: bool
    actual_cost_usd: float = Field(ge=0.0)
    budget_limit_usd: float = Field(ge=0.0)
    remaining_usd: float = 0.0
    utilization_pct: float = Field(default=0.0, ge=0.0)


# ── Snapshot/Diff Models (frozen) ──


class DiffItem(BaseModel):
    """A single difference between two snapshots.

    Attributes:
        dimension: The dimension being compared (e.g. 'tool_calls', 'cost').
        expected: The expected (baseline) value.
        actual: The actual (current) value.
        similarity: Similarity score for this dimension (0.0 to 1.0).
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    dimension: str
    expected: Any = None
    actual: Any = None
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class SnapshotDiff(BaseModel):
    """Comparison result between a snapshot and current output.

    Attributes:
        snapshot_name: Name of the snapshot being compared.
        overall_similarity: Weighted average similarity across dimensions.
        diffs: Per-dimension comparison details.
        is_match: Whether the overall similarity meets the threshold.
        threshold: Similarity threshold used.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    snapshot_name: str
    overall_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    diffs: tuple[DiffItem, ...] = ()
    is_match: bool = False
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)


# ── Trace Replay Models (frozen) ──


class TraceStep(BaseModel):
    """A single step in a time-travel trace, with cumulative metrics.

    Attributes:
        step_index: Zero-based index of this step.
        turn: The trace turn at this step.
        cumulative_input_tokens: Total input tokens up to this step.
        cumulative_output_tokens: Total output tokens up to this step.
        cumulative_cost_usd: Estimated cumulative cost up to this step.
        cumulative_latency_ms: Total latency up to this step.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    step_index: int = Field(ge=0)
    turn: Turn
    cumulative_input_tokens: int = Field(default=0, ge=0)
    cumulative_output_tokens: int = Field(default=0, ge=0)
    cumulative_cost_usd: float = Field(default=0.0, ge=0.0)
    cumulative_latency_ms: int = Field(default=0, ge=0)


class ReplayDiff(BaseModel):
    """Diff between an original trace and a replay trace.

    Attributes:
        original_trace_id: ID of the original trace.
        replay_trace_id: ID of the replay trace.
        tool_call_diffs: Differences in tool calls.
        output_matches: Whether the outputs match.
        original_output: Output from the original trace.
        replay_output: Output from the replay trace.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    original_trace_id: str = ""
    replay_trace_id: str = ""
    tool_call_diffs: tuple[DiffItem, ...] = ()
    output_matches: bool = False
    original_output: str = ""
    replay_output: str = ""


# ── Chaos Models (frozen) ──


class ChaosOverride(BaseModel):
    """Configuration for a single chaos fault injection.

    Attributes:
        chaos_type: Type of fault to inject.
        probability: Probability of applying this fault (0.0 to 1.0).
        target_tool: If set, only apply to this specific tool.
        delay_ms: Delay in ms for SLOW type.
        error_message: Custom error message for ERROR type.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    chaos_type: ChaosType
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    target_tool: str | None = None
    delay_ms: int = Field(default=5000, ge=0)
    error_message: str = "Chaos fault injected"


# ── Aggregate Models (frozen) ──


class AgentRun(BaseModel):
    """A complete agent test run encompassing multiple test results.

    Attributes:
        run_id: Unique identifier for this run.
        agent_name: Name of the agent tested.
        status: Overall run status.
        test_results: All test results from this run.
        total_tests: Total number of tests.
        passed: Number of tests that passed.
        failed: Number of tests that failed.
        errors: Number of tests that errored.
        skipped: Number of tests skipped.
        cost_summary: Aggregate cost for the run.
        duration_ms: Total run duration in milliseconds.
        tags: Tags for filtering.
        metadata: Additional run metadata.
        created_at: When the run started.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    status: RunStatus
    test_results: tuple[TestResult, ...] = ()
    total_tests: int = Field(default=0, ge=0)
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    cost_summary: CostSummary | None = None
    duration_ms: int = Field(default=0, ge=0)
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Metric Models (frozen) ──


class MetricDefinition(BaseModel):
    """Definition of a named metric that can be collected and tracked.

    Attributes:
        name: Unique metric identifier (e.g. 'latency_ms', 'token_cost_usd').
        metric_type: Category of the metric.
        description: Human-readable description.
        unit: Unit of measurement (e.g. 'ms', 'usd', 'count').
        lower_is_better: Whether lower values indicate better performance.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    lower_is_better: bool = True


class MetricValue(BaseModel):
    """A single metric measurement at a point in time.

    Attributes:
        metric_name: Name of the metric this value belongs to.
        value: The numeric measurement.
        tags: Tags for filtering and grouping.
        metadata: Additional context about this measurement.
        timestamp: When the measurement was taken.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    metric_name: str = Field(..., min_length=1)
    value: float
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MetricAggregation(BaseModel):
    """Aggregated statistics for a collection of metric values.

    Attributes:
        metric_name: Name of the metric.
        count: Number of values aggregated.
        mean: Arithmetic mean.
        median: Median value.
        min_value: Minimum value.
        max_value: Maximum value.
        p95: 95th percentile.
        p99: 99th percentile.
        std_dev: Standard deviation.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    metric_name: str = Field(..., min_length=1)
    count: int = Field(ge=1)
    mean: float = 0.0
    median: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    std_dev: float = Field(default=0.0, ge=0.0)


# ── Trace Diff Models (frozen) ──


class TraceDiffReport(BaseModel):
    """Report from comparing two independent traces.

    Compares output text, tool call sequences, model usage,
    token counts, and latency between any two traces.

    Attributes:
        trace_a_id: ID of the first trace.
        trace_b_id: ID of the second trace.
        tool_call_diffs: Per-tool-call comparison items.
        output_matches: Whether the output texts match exactly.
        token_delta: Difference in total tokens (B - A).
        latency_delta_ms: Difference in total latency (B - A).
        overall_similarity: Weighted similarity score (0.0 to 1.0).
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    trace_a_id: str = ""
    trace_b_id: str = ""
    tool_call_diffs: tuple[DiffItem, ...] = ()
    output_matches: bool = False
    token_delta: int = 0
    latency_delta_ms: int = 0
    overall_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
