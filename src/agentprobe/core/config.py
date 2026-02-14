"""Configuration loading and validation for AgentProbe.

Loads configuration from ``agentprobe.yaml`` with support for
``${ENV_VAR}`` interpolation and sensible defaults.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from agentprobe.core.exceptions import ConfigError

logger = logging.getLogger(__name__)

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _interpolate_env_vars(value: str) -> str:
    """Replace ``${VAR}`` references with environment variable values."""

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        env_val = os.environ.get(var_name)
        if env_val is None:
            logger.warning("Environment variable '%s' not set", var_name)
            return match.group(0)
        return env_val

    return _ENV_VAR_PATTERN.sub(_replace, value)


def _interpolate_recursive(data: Any) -> Any:
    """Recursively interpolate environment variables in a data structure."""
    if isinstance(data, str):
        return _interpolate_env_vars(data)
    if isinstance(data, dict):
        return {k: _interpolate_recursive(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_interpolate_recursive(item) for item in data]
    return data


class RunnerConfig(BaseModel):
    """Configuration for the test runner.

    Attributes:
        parallel: Whether to run tests in parallel.
        max_workers: Maximum number of concurrent tests.
        default_timeout: Default test timeout in seconds.
    """

    model_config = ConfigDict(extra="forbid")

    parallel: bool = False
    max_workers: int = Field(default=4, ge=1)
    default_timeout: float = Field(default=30.0, gt=0)


class EvalConfig(BaseModel):
    """Configuration for evaluators.

    Attributes:
        default_evaluators: Evaluator names to apply to all tests.
    """

    model_config = ConfigDict(extra="forbid")

    default_evaluators: list[str] = Field(default_factory=list)


class JudgeConfig(BaseModel):
    """Configuration for the judge evaluator.

    Attributes:
        model: Model to use for judging.
        provider: API provider name.
        temperature: Sampling temperature.
        max_tokens: Maximum response tokens.
    """

    model_config = ConfigDict(extra="forbid")

    model: str = "claude-sonnet-4-5-20250929"
    provider: str = "anthropic"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)


class TraceConfig(BaseModel):
    """Configuration for trace recording and storage.

    Attributes:
        enabled: Whether to record traces.
        storage_backend: Storage backend type.
        database_path: Path to SQLite database file.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    storage_backend: str = "sqlite"
    database_path: str = ".agentprobe/traces.db"


class CostConfig(BaseModel):
    """Configuration for cost tracking.

    Attributes:
        enabled: Whether to track costs.
        budget_limit_usd: Maximum allowed cost per run.
        pricing_dir: Directory containing pricing YAML files.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    budget_limit_usd: float | None = None
    pricing_dir: str | None = None


class SafetyConfig(BaseModel):
    """Configuration for safety testing.

    Attributes:
        enabled: Whether to run safety tests.
        suites: List of safety suite names to run.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    suites: list[str] = Field(default_factory=list)


class ChaosConfig(BaseModel):
    """Configuration for chaos fault injection testing.

    Attributes:
        enabled: Whether chaos testing is enabled.
        seed: Random seed for deterministic fault injection.
        default_probability: Default probability of applying a fault.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    seed: int = 42
    default_probability: float = Field(default=0.5, ge=0.0, le=1.0)


class SnapshotConfig(BaseModel):
    """Configuration for snapshot/golden file testing.

    Attributes:
        enabled: Whether snapshot testing is enabled.
        snapshot_dir: Directory for storing snapshot files.
        update_on_first_run: Whether to create snapshots on first run.
        threshold: Similarity threshold for snapshot matching.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    snapshot_dir: str = ".agentprobe/snapshots"
    update_on_first_run: bool = True
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class BudgetConfig(BaseModel):
    """Configuration for per-test and per-suite cost budgets.

    Attributes:
        test_budget_usd: Maximum cost per individual test.
        suite_budget_usd: Maximum cost per test suite run.
    """

    model_config = ConfigDict(extra="forbid")

    test_budget_usd: float | None = None
    suite_budget_usd: float | None = None


class RegressionConfig(BaseModel):
    """Configuration for regression detection.

    Attributes:
        enabled: Whether regression detection is enabled.
        baseline_dir: Directory for storing baseline files.
        threshold: Score delta threshold for flagging regressions.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    baseline_dir: str = ".agentprobe/baselines"
    threshold: float = Field(default=0.05, ge=0.0, le=1.0)


class MetricsConfig(BaseModel):
    """Configuration for metric collection and trending.

    Attributes:
        enabled: Whether metric collection is enabled.
        builtin_metrics: Whether to collect built-in metrics automatically.
        trend_window: Number of recent runs to use for trend analysis.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    builtin_metrics: bool = True
    trend_window: int = Field(default=10, ge=2)


class PluginConfig(BaseModel):
    """Configuration for the plugin system.

    Attributes:
        enabled: Whether the plugin system is enabled.
        directories: Additional directories to scan for plugins.
        entry_point_group: Entry point group name for plugin discovery.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    directories: list[str] = Field(default_factory=list)
    entry_point_group: str = "agentprobe.plugins"


class ReportingConfig(BaseModel):
    """Configuration for result reporting.

    Attributes:
        formats: Output format names.
        output_dir: Directory for report files.
    """

    model_config = ConfigDict(extra="forbid")

    formats: list[str] = Field(default_factory=lambda: ["terminal"])
    output_dir: str = "agentprobe-report"


class AgentProbeConfig(BaseModel):
    """Top-level AgentProbe configuration.

    Attributes:
        project_name: Name of the project being tested.
        test_dir: Directory containing test files.
        runner: Test runner configuration.
        eval: Evaluator configuration.
        judge: Judge evaluator configuration.
        trace: Trace recording configuration.
        cost: Cost tracking configuration.
        safety: Safety testing configuration.
        reporting: Reporting configuration.
    """

    model_config = ConfigDict(extra="forbid")

    project_name: str = "agentprobe"
    test_dir: str = "tests"
    runner: RunnerConfig = Field(default_factory=RunnerConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    trace: TraceConfig = Field(default_factory=TraceConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    chaos: ChaosConfig = Field(default_factory=ChaosConfig)
    snapshot: SnapshotConfig = Field(default_factory=SnapshotConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    regression: RegressionConfig = Field(default_factory=RegressionConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)


def load_config(
    path: str | Path | None = None,
) -> AgentProbeConfig:
    """Load configuration from a YAML file.

    Searches for ``agentprobe.yaml`` or ``agentprobe.yml`` in the
    current directory if no path is provided. Returns default config
    if no file is found.

    Args:
        path: Explicit path to a config file.

    Returns:
        A validated AgentProbeConfig instance.

    Raises:
        ConfigError: If the file exists but is invalid.
    """
    if path is not None:
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
    else:
        for candidate in ["agentprobe.yaml", "agentprobe.yml"]:
            config_path = Path(candidate)
            if config_path.exists():
                break
        else:
            logger.debug("No config file found, using defaults")
            return AgentProbeConfig()

    logger.info("Loading config from %s", config_path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if raw is None:
        return AgentProbeConfig()

    if not isinstance(raw, dict):
        raise ConfigError(f"Config file must be a YAML mapping, got {type(raw).__name__}")

    interpolated = _interpolate_recursive(raw)

    try:
        return AgentProbeConfig.model_validate(interpolated)
    except Exception as exc:
        raise ConfigError(f"Invalid configuration: {exc}") from exc
