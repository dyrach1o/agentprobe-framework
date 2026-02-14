"""Tests for the regression detector."""

from __future__ import annotations

from agentprobe.regression.detector import RegressionDetector
from tests.fixtures.results import make_test_result


class TestRegressionDetector:
    """Test RegressionDetector comparison logic."""

    def test_no_regression(self) -> None:
        baseline = [
            make_test_result(test_name="t1", score=0.8),
            make_test_result(test_name="t2", score=0.9),
        ]
        current = [
            make_test_result(test_name="t1", score=0.82),
            make_test_result(test_name="t2", score=0.88),
        ]
        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", baseline, current)

        assert report.regressions == 0
        assert report.improvements == 0
        assert report.unchanged == 2
        assert report.total_tests == 2

    def test_regression_detected(self) -> None:
        baseline = [make_test_result(test_name="t1", score=0.9)]
        current = [make_test_result(test_name="t1", score=0.7)]
        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", baseline, current)

        assert report.regressions == 1
        assert report.comparisons[0].is_regression is True
        assert report.comparisons[0].delta < 0

    def test_improvement_detected(self) -> None:
        baseline = [make_test_result(test_name="t1", score=0.5)]
        current = [make_test_result(test_name="t1", score=0.9)]
        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", baseline, current)

        assert report.improvements == 1
        assert report.comparisons[0].is_improvement is True
        assert report.comparisons[0].delta > 0

    def test_mixed_results(self) -> None:
        baseline = [
            make_test_result(test_name="t1", score=0.9),
            make_test_result(test_name="t2", score=0.5),
            make_test_result(test_name="t3", score=0.7),
        ]
        current = [
            make_test_result(test_name="t1", score=0.6),  # regression
            make_test_result(test_name="t2", score=0.8),  # improvement
            make_test_result(test_name="t3", score=0.72),  # unchanged
        ]
        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", baseline, current)

        assert report.regressions == 1
        assert report.improvements == 1
        assert report.unchanged == 1

    def test_threshold_edge_case_just_beyond(self) -> None:
        baseline = [make_test_result(test_name="t1", score=0.8)]
        current = [make_test_result(test_name="t1", score=0.74)]
        detector = RegressionDetector(threshold=0.05)
        report = detector.compare("v1", baseline, current)

        assert report.regressions == 1

    def test_at_threshold_is_unchanged(self) -> None:
        baseline = [make_test_result(test_name="t1", score=0.8)]
        current = [make_test_result(test_name="t1", score=0.75)]
        detector = RegressionDetector(threshold=0.1)
        report = detector.compare("v1", baseline, current)

        assert report.unchanged == 1

    def test_only_common_tests_compared(self) -> None:
        baseline = [
            make_test_result(test_name="t1", score=0.8),
            make_test_result(test_name="t2", score=0.7),
        ]
        current = [
            make_test_result(test_name="t1", score=0.85),
            make_test_result(test_name="t3", score=0.9),
        ]
        detector = RegressionDetector()
        report = detector.compare("v1", baseline, current)

        assert report.total_tests == 1
        assert report.comparisons[0].test_name == "t1"

    def test_empty_results(self) -> None:
        detector = RegressionDetector()
        report = detector.compare("v1", [], [])

        assert report.total_tests == 0
        assert report.regressions == 0

    def test_baseline_name_in_report(self) -> None:
        detector = RegressionDetector()
        report = detector.compare("baseline-v2.1", [], [])
        assert report.baseline_name == "baseline-v2.1"

    def test_custom_threshold_in_report(self) -> None:
        detector = RegressionDetector(threshold=0.1)
        report = detector.compare("v1", [], [])
        assert report.threshold == 0.1
