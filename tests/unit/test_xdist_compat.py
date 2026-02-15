"""Tests for pytest-xdist parallel execution compatibility."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agentprobe.pytest_plugin import (
    _get_xdist_worker_id,
    _is_xdist_worker,
    _resolve_db_path,
    pytest_configure,
)


def _make_config(
    *,
    worker_id: str | None = None,
    trace_dir: str | None = None,
    parallel: bool = False,
) -> MagicMock:
    """Create a mock pytest.Config with optional xdist worker attributes.

    Args:
        worker_id: Simulated xdist worker ID (e.g. 'gw0').
        trace_dir: Value for --agentprobe-trace-dir option.
        parallel: Value for --agentprobe-parallel option.
    """
    config = MagicMock(spec=pytest.Config)

    if worker_id is not None:
        config.workerinput = {"workerid": worker_id}
    else:
        # Remove workerinput attr so hasattr returns False.
        del config.workerinput

    def getoption(name: str, default: object = None) -> object:
        options = {
            "--agentprobe-trace-dir": trace_dir,
            "--agentprobe-parallel": parallel,
        }
        return options.get(name, default)

    config.getoption = MagicMock(side_effect=getoption)
    return config


class TestXdistDetection:
    """Tests for xdist worker detection helpers."""

    def test_is_xdist_worker_true_when_workerinput_present(self) -> None:
        config = _make_config(worker_id="gw0")
        assert _is_xdist_worker(config) is True

    def test_is_xdist_worker_false_when_no_workerinput(self) -> None:
        config = _make_config()
        assert _is_xdist_worker(config) is False

    def test_get_worker_id_returns_id(self) -> None:
        config = _make_config(worker_id="gw3")
        assert _get_xdist_worker_id(config) == "gw3"

    def test_get_worker_id_returns_none_without_xdist(self) -> None:
        config = _make_config()
        assert _get_xdist_worker_id(config) is None


class TestPytestConfigureXdist:
    """Tests for xdist handling in pytest_configure."""

    def test_sets_worker_id_attr_under_xdist(self) -> None:
        config = _make_config(worker_id="gw1")
        pytest_configure(config)
        assert config._agentprobe_worker_id == "gw1"

    def test_no_worker_id_attr_without_xdist(self) -> None:
        config = _make_config()
        pytest_configure(config)
        assert not hasattr(config, "_agentprobe_worker_id")


class TestResolveDbPath:
    """Tests for worker-specific database path resolution."""

    def test_default_path_without_xdist(self) -> None:
        config = _make_config()
        result = _resolve_db_path(config, ".agentprobe/traces.db")
        assert result == ".agentprobe/traces.db"

    def test_worker_specific_path_under_xdist(self) -> None:
        config = _make_config()
        config._agentprobe_worker_id = "gw0"
        result = _resolve_db_path(config, ".agentprobe/traces.db")
        assert result == str(Path(".agentprobe/traces_gw0.db"))

    def test_worker_specific_path_gw2(self) -> None:
        config = _make_config()
        config._agentprobe_worker_id = "gw2"
        result = _resolve_db_path(config, "/tmp/data/traces.db")
        expected = str(Path("/tmp/data/traces_gw2.db"))
        assert result == expected

    def test_parallel_flag_without_xdist(self) -> None:
        config = _make_config(parallel=True)
        result = _resolve_db_path(config, ".agentprobe/traces.db")
        assert result == str(Path(".agentprobe/traces_main.db"))

    def test_trace_dir_option_overrides_default(self) -> None:
        config = _make_config(trace_dir="/custom/dir")
        result = _resolve_db_path(config, ".agentprobe/traces.db")
        assert result == "/custom/dir/traces.db"

    def test_trace_dir_with_xdist_worker(self) -> None:
        config = _make_config(trace_dir="/custom/dir")
        config._agentprobe_worker_id = "gw1"
        result = _resolve_db_path(config, ".agentprobe/traces.db")
        assert result == str(Path("/custom/dir/traces_gw1.db"))

    def test_xdist_worker_id_takes_precedence_over_parallel_flag(self) -> None:
        config = _make_config(parallel=True)
        config._agentprobe_worker_id = "gw5"
        result = _resolve_db_path(config, ".agentprobe/traces.db")
        # Worker ID should be used, not "main"
        assert "gw5" in result
        assert "main" not in result
