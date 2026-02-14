"""Integration test: BaselineManager + RegressionDetector roundtrip."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.regression.baseline import BaselineManager
from agentprobe.regression.detector import RegressionDetector
from tests.fixtures.results import make_test_result


@pytest.mark.integration
class TestRegressionFlow:
    """End-to-end regression detection pipeline."""

    def test_save_load_compare_no_regression(self, tmp_path: Path) -> None:
        """Save baseline, load it, compare identical results — no regressions."""
        manager = BaselineManager(baseline_dir=tmp_path / "baselines")
        results = [
            make_test_result(test_name="test_a", score=0.9),
            make_test_result(test_name="test_b", score=0.8),
            make_test_result(test_name="test_c", score=1.0),
        ]

        # Save baseline
        path = manager.save("v1", results)
        assert path.exists()
        assert manager.exists("v1")

        # Load baseline
        loaded = manager.load("v1")
        assert len(loaded) == 3

        # Compare identical results → no regressions
        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", loaded, results)

        assert report.regressions == 0
        assert report.improvements == 0
        assert report.unchanged == 3
        assert report.total_tests == 3

    def test_detect_regression(self, tmp_path: Path) -> None:
        """Detect a regression when current score drops."""
        manager = BaselineManager(baseline_dir=tmp_path / "baselines")
        baseline = [
            make_test_result(test_name="test_a", score=0.9),
            make_test_result(test_name="test_b", score=0.8),
        ]
        manager.save("v1", baseline)
        loaded = manager.load("v1")

        # Current results: test_a regressed, test_b same
        current = [
            make_test_result(test_name="test_a", score=0.5),
            make_test_result(test_name="test_b", score=0.8),
        ]

        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", loaded, current)

        assert report.regressions == 1
        assert report.unchanged == 1
        # Verify the regression is for test_a
        regressed = [c for c in report.comparisons if c.is_regression]
        assert len(regressed) == 1
        assert regressed[0].test_name == "test_a"
        assert regressed[0].delta < 0

    def test_detect_improvement(self, tmp_path: Path) -> None:
        """Detect an improvement when current score increases."""
        manager = BaselineManager(baseline_dir=tmp_path / "baselines")
        baseline = [
            make_test_result(test_name="test_a", score=0.5),
        ]
        manager.save("v1", baseline)
        loaded = manager.load("v1")

        current = [
            make_test_result(test_name="test_a", score=0.95),
        ]

        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", loaded, current)

        assert report.improvements == 1
        assert report.regressions == 0

    def test_multiple_baselines(self, tmp_path: Path) -> None:
        """Manage multiple named baselines."""
        manager = BaselineManager(baseline_dir=tmp_path / "baselines")

        manager.save("v1", [make_test_result(test_name="t1", score=0.7)])
        manager.save("v2", [make_test_result(test_name="t1", score=0.9)])

        assert manager.list_baselines() == ["v1", "v2"]

        v1 = manager.load("v1")
        v2 = manager.load("v2")
        assert v1[0].score == pytest.approx(0.7)
        assert v2[0].score == pytest.approx(0.9)

    def test_delete_baseline(self, tmp_path: Path) -> None:
        """Delete a baseline and verify it's gone."""
        manager = BaselineManager(baseline_dir=tmp_path / "baselines")
        manager.save("temp", [make_test_result(test_name="t1")])
        assert manager.exists("temp")

        deleted = manager.delete("temp")
        assert deleted is True
        assert not manager.exists("temp")

    def test_compare_mismatched_tests(self, tmp_path: Path) -> None:
        """Only common tests are compared; extras are ignored."""
        manager = BaselineManager(baseline_dir=tmp_path / "baselines")
        baseline = [
            make_test_result(test_name="test_a", score=0.9),
            make_test_result(test_name="test_b", score=0.8),
        ]
        manager.save("v1", baseline)
        loaded = manager.load("v1")

        # Current has test_a and test_c (no test_b)
        current = [
            make_test_result(test_name="test_a", score=0.9),
            make_test_result(test_name="test_c", score=1.0),
        ]

        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", loaded, current)

        # Only test_a is in common
        assert report.total_tests == 1
        assert report.unchanged == 1
