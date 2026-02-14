"""Tests for the AgentProbe exception hierarchy."""

from agentprobe.core.exceptions import (
    AdapterError,
    AgentProbeError,
    AssertionFailedError,
    BudgetExceededError,
    ChaosError,
    ConfigError,
    ConversationError,
    CostError,
    EvaluatorError,
    JudgeAPIError,
    PluginError,
    RegressionError,
    ReplayError,
    RunnerError,
    SafetyError,
    SecurityError,
    SnapshotError,
    StorageError,
    TestTimeoutError,
    TraceError,
)


class TestExceptionHierarchy:
    """Verify all exceptions inherit from AgentProbeError."""

    def test_all_inherit_from_base(self) -> None:
        exceptions = [
            ConfigError,
            RunnerError,
            TestTimeoutError,
            AdapterError,
            EvaluatorError,
            JudgeAPIError,
            StorageError,
            TraceError,
            CostError,
            BudgetExceededError,
            SafetyError,
            SecurityError,
            PluginError,
            AssertionFailedError,
            ChaosError,
            SnapshotError,
            ReplayError,
            RegressionError,
            ConversationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, AgentProbeError)

    def test_timeout_inherits_from_runner_error(self) -> None:
        assert issubclass(TestTimeoutError, RunnerError)

    def test_judge_api_inherits_from_evaluator_error(self) -> None:
        assert issubclass(JudgeAPIError, EvaluatorError)

    def test_budget_exceeded_inherits_from_cost_error(self) -> None:
        assert issubclass(BudgetExceededError, CostError)


class TestTestTimeoutError:
    """Verify TestTimeoutError attributes and message."""

    def test_attributes(self) -> None:
        exc = TestTimeoutError("my_test", 30.0)
        assert exc.test_name == "my_test"
        assert exc.timeout_seconds == 30.0
        assert "my_test" in str(exc)
        assert "30.0" in str(exc)


class TestAdapterError:
    """Verify AdapterError attributes and message."""

    def test_attributes(self) -> None:
        exc = AdapterError("langchain", "connection failed")
        assert exc.adapter_name == "langchain"
        assert "langchain" in str(exc)
        assert "connection failed" in str(exc)


class TestJudgeAPIError:
    """Verify JudgeAPIError attributes and message."""

    def test_attributes(self) -> None:
        exc = JudgeAPIError("claude-sonnet-4-5-20250929", 429, "rate limited")
        assert exc.model == "claude-sonnet-4-5-20250929"
        assert exc.status_code == 429
        assert "429" in str(exc)
        assert "rate limited" in str(exc)


class TestBudgetExceededError:
    """Verify BudgetExceededError attributes and message."""

    def test_attributes(self) -> None:
        exc = BudgetExceededError(1.5, 1.0)
        assert exc.actual == 1.5
        assert exc.limit == 1.0
        assert exc.currency == "USD"
        assert "$1.5000" in str(exc)
        assert "$1.0000" in str(exc)


class TestAssertionFailedError:
    """Verify AssertionFailedError attributes and message."""

    def test_default_message(self) -> None:
        exc = AssertionFailedError("contain", "hello", "world")
        assert exc.assertion_type == "contain"
        assert exc.expected == "hello"
        assert exc.actual == "world"
        assert "contain" in str(exc)

    def test_custom_message(self) -> None:
        exc = AssertionFailedError("match", "a", "b", message="custom msg")
        assert str(exc) == "custom msg"


class TestNewExceptions:
    """Verify extended exception classes."""

    def test_chaos_error(self) -> None:
        exc = ChaosError("fault injected")
        assert "fault injected" in str(exc)
        assert isinstance(exc, AgentProbeError)

    def test_snapshot_error(self) -> None:
        exc = SnapshotError("snapshot not found")
        assert "snapshot not found" in str(exc)
        assert isinstance(exc, AgentProbeError)

    def test_replay_error(self) -> None:
        exc = ReplayError("replay failed")
        assert "replay failed" in str(exc)
        assert isinstance(exc, AgentProbeError)

    def test_regression_error(self) -> None:
        exc = RegressionError("baseline missing")
        assert "baseline missing" in str(exc)
        assert isinstance(exc, AgentProbeError)

    def test_conversation_error(self) -> None:
        exc = ConversationError("turn 3 failed")
        assert "turn 3 failed" in str(exc)
        assert isinstance(exc, AgentProbeError)
