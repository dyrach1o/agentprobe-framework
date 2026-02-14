"""Tests for configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.config import (
    AgentProbeConfig,
    BudgetConfig,
    ChaosConfig,
    MetricsConfig,
    PluginConfig,
    RegressionConfig,
    RunnerConfig,
    SnapshotConfig,
    load_config,
)
from agentprobe.core.exceptions import ConfigError


class TestAgentProbeConfig:
    """Tests for config model defaults and validation."""

    def test_defaults(self) -> None:
        config = AgentProbeConfig()
        assert config.project_name == "agentprobe"
        assert config.runner.parallel is False
        assert config.runner.max_workers == 4
        assert config.trace.enabled is True
        assert config.cost.enabled is True

    def test_runner_config(self) -> None:
        config = RunnerConfig(parallel=True, max_workers=8, default_timeout=60.0)
        assert config.parallel is True
        assert config.max_workers == 8

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValueError):
            AgentProbeConfig(unknown_field="value")  # type: ignore[call-arg]


class TestLoadConfig:
    """Tests for config file loading."""

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_config(tmp_path / "nonexistent.yaml")

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text("", encoding="utf-8")
        config = load_config(config_file)
        assert config.project_name == "agentprobe"

    def test_valid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text(
            "project_name: my-project\nrunner:\n  parallel: true\n  max_workers: 8\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config.project_name == "my-project"
        assert config.runner.parallel is True
        assert config.runner.max_workers == 8

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text("{{invalid yaml", encoding="utf-8")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(config_file)

    def test_non_mapping_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(ConfigError, match="YAML mapping"):
            load_config(config_file)

    def test_env_var_interpolation(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AP_PROJECT", "env-project")
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text(
            "project_name: ${AP_PROJECT}\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config.project_name == "env-project"

    def test_no_config_file_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert config.project_name == "agentprobe"


class TestChaosConfig:
    """Tests for chaos configuration model."""

    def test_defaults(self) -> None:
        config = ChaosConfig()
        assert config.enabled is False
        assert config.seed == 42
        assert config.default_probability == 0.5

    def test_custom(self) -> None:
        config = ChaosConfig(enabled=True, seed=123, default_probability=0.8)
        assert config.enabled is True
        assert config.seed == 123


class TestSnapshotConfig:
    """Tests for snapshot configuration model."""

    def test_defaults(self) -> None:
        config = SnapshotConfig()
        assert config.enabled is False
        assert config.snapshot_dir == ".agentprobe/snapshots"
        assert config.update_on_first_run is True
        assert config.threshold == 0.8

    def test_custom(self) -> None:
        config = SnapshotConfig(enabled=True, threshold=0.95)
        assert config.threshold == 0.95


class TestBudgetConfig:
    """Tests for budget configuration model."""

    def test_defaults(self) -> None:
        config = BudgetConfig()
        assert config.test_budget_usd is None
        assert config.suite_budget_usd is None

    def test_custom(self) -> None:
        config = BudgetConfig(test_budget_usd=0.50, suite_budget_usd=10.0)
        assert config.test_budget_usd == 0.50
        assert config.suite_budget_usd == 10.0


class TestRegressionConfig:
    """Tests for regression configuration model."""

    def test_defaults(self) -> None:
        config = RegressionConfig()
        assert config.enabled is False
        assert config.baseline_dir == ".agentprobe/baselines"
        assert config.threshold == 0.05

    def test_custom(self) -> None:
        config = RegressionConfig(enabled=True, threshold=0.1)
        assert config.threshold == 0.1


class TestNewConfigsInAgentProbeConfig:
    """Tests that new config models are wired into the top-level config."""

    def test_default_chaos_config(self) -> None:
        config = AgentProbeConfig()
        assert config.chaos.enabled is False

    def test_default_snapshot_config(self) -> None:
        config = AgentProbeConfig()
        assert config.snapshot.enabled is False

    def test_default_budget_config(self) -> None:
        config = AgentProbeConfig()
        assert config.budget.test_budget_usd is None

    def test_default_regression_config(self) -> None:
        config = AgentProbeConfig()
        assert config.regression.enabled is False

    def test_yaml_with_new_configs(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text(
            "chaos:\n  enabled: true\n  seed: 99\n"
            "snapshot:\n  enabled: true\n"
            "budget:\n  test_budget_usd: 1.0\n"
            "regression:\n  enabled: true\n  threshold: 0.1\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config.chaos.enabled is True
        assert config.chaos.seed == 99
        assert config.snapshot.enabled is True
        assert config.budget.test_budget_usd == 1.0
        assert config.regression.threshold == 0.1


class TestMetricsConfig:
    """Tests for metrics configuration model."""

    def test_defaults(self) -> None:
        config = MetricsConfig()
        assert config.enabled is True
        assert config.builtin_metrics is True
        assert config.trend_window == 10

    def test_custom(self) -> None:
        config = MetricsConfig(enabled=False, builtin_metrics=False, trend_window=20)
        assert config.enabled is False
        assert config.trend_window == 20

    def test_trend_window_min(self) -> None:
        with pytest.raises(ValueError, match="greater than or equal to 2"):
            MetricsConfig(trend_window=1)


class TestPluginConfig:
    """Tests for plugin configuration model."""

    def test_defaults(self) -> None:
        config = PluginConfig()
        assert config.enabled is True
        assert config.directories == []
        assert config.entry_point_group == "agentprobe.plugins"

    def test_custom(self) -> None:
        config = PluginConfig(
            enabled=False,
            directories=["/path/to/plugins"],
            entry_point_group="my.plugins",
        )
        assert config.enabled is False
        assert config.directories == ["/path/to/plugins"]


class TestMetricsPluginConfigsInAgentProbeConfig:
    """Tests that metrics and plugin configs are wired into top-level config."""

    def test_default_metrics_config(self) -> None:
        config = AgentProbeConfig()
        assert config.metrics.enabled is True
        assert config.metrics.builtin_metrics is True

    def test_default_plugin_config(self) -> None:
        config = AgentProbeConfig()
        assert config.plugins.enabled is True

    def test_yaml_with_metrics_and_plugins(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text(
            "metrics:\n  enabled: false\n  trend_window: 20\n"
            "plugins:\n  enabled: false\n  directories:\n    - /my/plugins\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config.metrics.enabled is False
        assert config.metrics.trend_window == 20
        assert config.plugins.enabled is False
        assert config.plugins.directories == ["/my/plugins"]
