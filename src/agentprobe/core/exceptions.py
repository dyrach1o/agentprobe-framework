"""Exception hierarchy for the AgentProbe framework.

All exceptions inherit from AgentProbeError, allowing callers to catch
the base type for generic error handling or specific subclasses for
targeted recovery.
"""


class AgentProbeError(Exception):
    """Base exception for all AgentProbe errors."""


class ConfigError(AgentProbeError):
    """Raised when configuration is invalid or missing."""


class RunnerError(AgentProbeError):
    """Raised when the test runner encounters an execution failure."""


class TestTimeoutError(RunnerError):
    """Raised when a test exceeds its configured timeout."""

    def __init__(self, test_name: str, timeout_seconds: float) -> None:
        self.test_name = test_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Test '{test_name}' exceeded {timeout_seconds}s timeout")


class AdapterError(AgentProbeError):
    """Raised when an agent adapter fails during invocation."""

    def __init__(self, adapter_name: str, message: str) -> None:
        self.adapter_name = adapter_name
        super().__init__(f"Adapter '{adapter_name}' error: {message}")


class EvaluatorError(AgentProbeError):
    """Base exception for evaluation errors."""


class JudgeAPIError(EvaluatorError):
    """Raised when the judge model API call fails."""

    def __init__(self, model: str, status_code: int, message: str) -> None:
        self.model = model
        self.status_code = status_code
        super().__init__(f"Judge API error ({model}): {status_code} — {message}")


class StorageError(AgentProbeError):
    """Raised when a storage backend operation fails."""


class TraceError(AgentProbeError):
    """Raised when trace recording or processing fails."""


class CostError(AgentProbeError):
    """Raised when cost calculation encounters an error."""


class BudgetExceededError(CostError):
    """Raised when a cost budget limit is exceeded."""

    def __init__(self, actual: float, limit: float, currency: str = "USD") -> None:
        self.actual = actual
        self.limit = limit
        self.currency = currency
        super().__init__(f"Budget exceeded: ${actual:.4f} > ${limit:.4f} {currency} limit")


class SafetyError(AgentProbeError):
    """Raised when a safety check fails or encounters an error."""


class SecurityError(AgentProbeError):
    """Raised when a security violation is detected."""


class MetricsError(AgentProbeError):
    """Raised when metric collection, aggregation, or trending fails."""


class PluginError(AgentProbeError):
    """Raised when a plugin fails to load or execute."""


class ChaosError(AgentProbeError):
    """Raised when a chaos fault injection causes a failure."""


class SnapshotError(AgentProbeError):
    """Raised when a snapshot operation fails."""


class ReplayError(AgentProbeError):
    """Raised when trace replay encounters an error."""


class RegressionError(AgentProbeError):
    """Raised when regression detection encounters an error."""


class ConversationError(AgentProbeError):
    """Raised when a multi-turn conversation test fails."""


class DashboardError(AgentProbeError):
    """Raised when dashboard operations fail."""


class AssertionFailedError(AgentProbeError):
    """Raised when a test assertion fails.

    Attributes:
        assertion_type: The type of assertion that failed (e.g. 'contain', 'match').
        expected: The expected value or pattern.
        actual: The actual value received.
    """

    def __init__(
        self,
        assertion_type: str,
        expected: object,
        actual: object,
        message: str | None = None,
    ) -> None:
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
        msg = message or (
            f"Assertion '{assertion_type}' failed: expected {expected!r}, got {actual!r}"
        )
        super().__init__(msg)
