"""Tests for built-in metric definitions registry."""

from __future__ import annotations

from agentprobe.core.models import MetricType
from agentprobe.metrics.definitions import (
    BUILTIN_METRICS,
    get_builtin_definitions,
    get_definition,
)


class TestBuiltinMetrics:
    """Test the built-in metric definitions."""

    def test_all_six_builtins_present(self) -> None:
        expected = {
            "latency_ms",
            "token_cost_usd",
            "tool_call_count",
            "response_length",
            "eval_score",
            "pass_rate",
        }
        assert set(BUILTIN_METRICS.keys()) == expected

    def test_latency_definition(self) -> None:
        defn = BUILTIN_METRICS["latency_ms"]
        assert defn.metric_type == MetricType.LATENCY
        assert defn.unit == "ms"
        assert defn.lower_is_better is True

    def test_cost_definition(self) -> None:
        defn = BUILTIN_METRICS["token_cost_usd"]
        assert defn.metric_type == MetricType.COST
        assert defn.lower_is_better is True

    def test_pass_rate_higher_is_better(self) -> None:
        defn = BUILTIN_METRICS["pass_rate"]
        assert defn.metric_type == MetricType.RATE
        assert defn.lower_is_better is False

    def test_eval_score_higher_is_better(self) -> None:
        defn = BUILTIN_METRICS["eval_score"]
        assert defn.metric_type == MetricType.SCORE
        assert defn.lower_is_better is False

    def test_response_length_higher_is_better(self) -> None:
        defn = BUILTIN_METRICS["response_length"]
        assert defn.lower_is_better is False


class TestGetBuiltinDefinitions:
    """Test get_builtin_definitions returns a copy."""

    def test_returns_all_definitions(self) -> None:
        defs = get_builtin_definitions()
        assert len(defs) == 6

    def test_returns_copy(self) -> None:
        defs = get_builtin_definitions()
        defs["custom"] = BUILTIN_METRICS["latency_ms"]
        assert "custom" not in BUILTIN_METRICS


class TestGetDefinition:
    """Test get_definition lookup."""

    def test_existing_metric(self) -> None:
        defn = get_definition("latency_ms")
        assert defn is not None
        assert defn.name == "latency_ms"

    def test_nonexistent_metric(self) -> None:
        assert get_definition("nonexistent_metric") is None

    def test_all_builtins_retrievable(self) -> None:
        for name in BUILTIN_METRICS:
            assert get_definition(name) is not None
