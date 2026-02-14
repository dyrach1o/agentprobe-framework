"""Integration test: PluginManager load → dispatch hooks → collect evaluators."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.core.models import EvalResult, EvalVerdict, PluginType, TestCase, Trace
from agentprobe.core.protocols import EvaluatorProtocol
from agentprobe.plugins.base import EvaluatorPlugin, PluginBase, ReporterPlugin
from agentprobe.plugins.manager import PluginManager


class _TestEvalPlugin(EvaluatorPlugin):
    """A test evaluator plugin."""

    @property
    def name(self) -> str:
        return "test-eval-plugin"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

    def on_load(self) -> None:
        self.loaded = True  # type: ignore[attr-defined]

    def on_unload(self) -> None:
        self.unloaded = True  # type: ignore[attr-defined]

    def on_test_start(self, test_name: str, **kwargs: Any) -> None:
        self.last_test_start = test_name  # type: ignore[attr-defined]

    def on_test_end(self, test_name: str, **kwargs: Any) -> None:
        self.last_test_end = test_name  # type: ignore[attr-defined]

    def create_evaluator(self) -> EvaluatorProtocol:
        return _SimpleEvaluator()


class _SimpleEvaluator:
    """A minimal evaluator from a plugin."""

    @property
    def name(self) -> str:
        return "plugin-evaluator"

    async def evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.PASS,
            score=1.0,
            reason="Plugin evaluator passed",
        )


class _TestReporterPlugin(ReporterPlugin):
    """A test reporter plugin."""

    @property
    def name(self) -> str:
        return "test-reporter-plugin"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.REPORTER

    def create_reporter(self) -> Any:
        return {"type": "reporter", "name": self.name}


class _BrokenPlugin(PluginBase):
    """A plugin that errors on lifecycle hooks."""

    @property
    def name(self) -> str:
        return "broken-plugin"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

    def on_test_start(self, test_name: str, **kwargs: Any) -> None:
        raise RuntimeError("Plugin failed in on_test_start")


@pytest.mark.integration
class TestPluginLifecycle:
    """End-to-end plugin loading, lifecycle, and collection."""

    def test_load_plugins_from_classes(self) -> None:
        """Load plugins directly from class references."""
        manager = PluginManager(entry_point_group="nonexistent.group")
        plugins = manager.load_plugins(classes=[_TestEvalPlugin, _TestReporterPlugin])

        assert len(plugins) == 2
        # Verify on_load was called
        eval_plugin = next(p for p in plugins if p.name == "test-eval-plugin")
        assert getattr(eval_plugin, "loaded", False) is True

    def test_dispatch_lifecycle_hooks(self) -> None:
        """Dispatch suite and test lifecycle events."""
        manager = PluginManager(entry_point_group="nonexistent.group")
        plugins = manager.load_plugins(classes=[_TestEvalPlugin])

        manager.dispatch_suite_start()
        manager.dispatch_test_start("test_example")
        manager.dispatch_test_end("test_example")
        manager.dispatch_suite_end()

        eval_plugin = next(p for p in plugins if p.name == "test-eval-plugin")
        assert getattr(eval_plugin, "last_test_start", None) == "test_example"
        assert getattr(eval_plugin, "last_test_end", None) == "test_example"

    def test_collect_evaluators(self) -> None:
        """Collect evaluators from evaluator plugins."""
        manager = PluginManager(entry_point_group="nonexistent.group")
        manager.load_plugins(classes=[_TestEvalPlugin, _TestReporterPlugin])

        evaluators = manager.get_evaluators()
        assert len(evaluators) == 1
        assert evaluators[0].name == "plugin-evaluator"

    def test_collect_reporters(self) -> None:
        """Collect reporters from reporter plugins."""
        manager = PluginManager(entry_point_group="nonexistent.group")
        manager.load_plugins(classes=[_TestEvalPlugin, _TestReporterPlugin])

        reporters = manager.get_reporters()
        assert len(reporters) == 1

    def test_unload_all(self) -> None:
        """Unload triggers on_unload for each plugin."""
        manager = PluginManager(entry_point_group="nonexistent.group")
        plugins = manager.load_plugins(classes=[_TestEvalPlugin])

        eval_plugin = plugins[0]
        manager.unload_all()

        assert getattr(eval_plugin, "unloaded", False) is True

    def test_broken_plugin_error_isolation(self) -> None:
        """A broken plugin doesn't break dispatch for other plugins."""
        manager = PluginManager(entry_point_group="nonexistent.group")
        plugins = manager.load_plugins(classes=[_BrokenPlugin, _TestEvalPlugin])

        # Should not raise — error is caught per-plugin
        manager.dispatch_test_start("test_isolation")

        # The good plugin still got the event
        eval_plugin = next(p for p in plugins if p.name == "test-eval-plugin")
        assert getattr(eval_plugin, "last_test_start", None) == "test_isolation"

    @pytest.mark.asyncio
    async def test_plugin_evaluator_in_runner(self) -> None:
        """Plugin-produced evaluator works in the test runner."""
        from agentprobe.core.models import TestCase
        from agentprobe.core.runner import TestRunner
        from tests.fixtures.agents import MockAdapter

        manager = PluginManager(entry_point_group="nonexistent.group")
        manager.load_plugins(classes=[_TestEvalPlugin])
        evaluators = manager.get_evaluators()

        runner = TestRunner(evaluators=evaluators)
        adapter = MockAdapter(name="plugin-test", output="plugin output")
        cases = [TestCase(name="test_plugin_eval", input_text="Hello")]

        run = await runner.run(cases, adapter)

        assert run.passed == 1
        assert run.test_results[0].eval_results[0].evaluator_name == "plugin-evaluator"
