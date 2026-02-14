"""Tests for the @scenario decorator and registry."""

from __future__ import annotations

import pytest

from agentprobe.core.scenario import clear_registry, get_scenarios, scenario


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Clear the scenario registry before each test."""
    clear_registry()


class TestScenarioDecorator:
    """Tests for the @scenario decorator."""

    def test_basic_registration(self) -> None:
        @scenario(name="test_hello", input_text="Hello!")
        def test_func() -> None:
            pass

        cases = get_scenarios()
        assert len(cases) == 1
        assert cases[0].name == "test_hello"
        assert cases[0].input_text == "Hello!"

    def test_name_defaults_to_function_name(self) -> None:
        @scenario(input_text="Hi")
        def my_test_func() -> None:
            pass

        cases = get_scenarios()
        assert cases[0].name == "my_test_func"

    def test_tags_and_timeout(self) -> None:
        @scenario(name="tagged_test", tags=["fast", "smoke"], timeout=10.0)
        def test_func() -> None:
            pass

        case = get_scenarios()[0]
        assert case.tags == ["fast", "smoke"]
        assert case.timeout_seconds == 10.0

    def test_expected_output(self) -> None:
        @scenario(name="expected_test", expected_output="world")
        def test_func() -> None:
            pass

        case = get_scenarios()[0]
        assert case.expected_output == "world"

    def test_evaluators(self) -> None:
        @scenario(name="eval_test", evaluators=["rule-based", "judge"])
        def test_func() -> None:
            pass

        case = get_scenarios()[0]
        assert case.evaluators == ["rule-based", "judge"]

    def test_multiple_scenarios(self) -> None:
        @scenario(name="test_a")
        def test_a() -> None:
            pass

        @scenario(name="test_b")
        def test_b() -> None:
            pass

        cases = get_scenarios()
        assert len(cases) == 2

    def test_scenario_attached_to_function(self) -> None:
        @scenario(name="attached_test")
        def test_func() -> None:
            pass

        assert hasattr(test_func, "_agentprobe_scenario")
        assert test_func._agentprobe_scenario.name == "attached_test"

    def test_decorated_function_still_callable(self) -> None:
        @scenario(name="callable_test")
        def test_func() -> str:
            return "result"

        assert test_func() == "result"

    def test_metadata_includes_source_function(self) -> None:
        @scenario(name="meta_test")
        def test_func() -> None:
            pass

        case = get_scenarios()[0]
        assert "source_function" in case.metadata


class TestGetScenarios:
    """Tests for get_scenarios with module filtering."""

    def test_empty_registry(self) -> None:
        assert get_scenarios() == []

    def test_filter_by_module(self) -> None:
        @scenario(name="test_one")
        def test_one() -> None:
            pass

        current_module = test_one.__module__
        assert len(get_scenarios(current_module)) == 1
        assert get_scenarios("nonexistent.module") == []


class TestClearRegistry:
    """Tests for clear_registry."""

    def test_clears_all(self) -> None:
        @scenario(name="test_clear")
        def test_func() -> None:
            pass

        assert len(get_scenarios()) == 1
        clear_registry()
        assert len(get_scenarios()) == 0
