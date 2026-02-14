"""Tests for the baseline manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.exceptions import RegressionError
from agentprobe.regression.baseline import BaselineManager
from tests.fixtures.results import make_test_result


class TestBaselineManager:
    """Test BaselineManager CRUD operations."""

    @pytest.fixture
    def baseline_dir(self, tmp_path: Path) -> Path:
        return tmp_path / "baselines"

    @pytest.fixture
    def manager(self, baseline_dir: Path) -> BaselineManager:
        return BaselineManager(baseline_dir)

    def test_save_and_load_roundtrip(self, manager: BaselineManager) -> None:
        results = [
            make_test_result(test_name="t1", score=0.9),
            make_test_result(test_name="t2", score=0.8),
        ]
        manager.save("v1", results)
        loaded = manager.load("v1")

        assert len(loaded) == 2
        assert loaded[0].test_name == "t1"
        assert loaded[0].score == 0.9
        assert loaded[1].test_name == "t2"

    def test_load_nonexistent_raises(self, manager: BaselineManager) -> None:
        with pytest.raises(RegressionError, match="not found"):
            manager.load("nonexistent")

    def test_exists(self, manager: BaselineManager) -> None:
        assert not manager.exists("v1")
        manager.save("v1", [make_test_result()])
        assert manager.exists("v1")

    def test_list_baselines(self, manager: BaselineManager) -> None:
        assert manager.list_baselines() == []
        manager.save("alpha", [make_test_result()])
        manager.save("beta", [make_test_result()])
        names = manager.list_baselines()
        assert names == ["alpha", "beta"]

    def test_list_baselines_no_dir(self, tmp_path: Path) -> None:
        manager = BaselineManager(tmp_path / "nonexistent")
        assert manager.list_baselines() == []

    def test_delete(self, manager: BaselineManager) -> None:
        manager.save("to-delete", [make_test_result()])
        assert manager.delete("to-delete") is True
        assert not manager.exists("to-delete")

    def test_delete_nonexistent(self, manager: BaselineManager) -> None:
        assert manager.delete("nonexistent") is False

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        deep_dir = tmp_path / "a" / "b" / "c"
        manager = BaselineManager(deep_dir)
        manager.save("test", [make_test_result()])
        assert deep_dir.is_dir()
        assert manager.exists("test")

    def test_save_empty_results(self, manager: BaselineManager) -> None:
        manager.save("empty", [])
        loaded = manager.load("empty")
        assert loaded == []

    def test_overwrite_existing(self, manager: BaselineManager) -> None:
        manager.save("v1", [make_test_result(test_name="original")])
        manager.save("v1", [make_test_result(test_name="updated")])
        loaded = manager.load("v1")
        assert loaded[0].test_name == "updated"
