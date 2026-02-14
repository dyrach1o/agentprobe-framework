"""Tests for the plugin base classes."""

from __future__ import annotations

from typing import Any

import pytest

from agentprobe.core.models import PluginType
from agentprobe.plugins.base import (
    AdapterPlugin,
    EvaluatorPlugin,
    PluginBase,
    ReporterPlugin,
    StoragePlugin,
)


class _ConcretePlugin(PluginBase):
    """Minimal concrete plugin for testing."""

    @property
    def name(self) -> str:
        return "test-plugin"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR


class _TrackingPlugin(_ConcretePlugin):
    """Plugin that tracks lifecycle calls."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def on_load(self) -> None:
        self.events.append("load")

    def on_unload(self) -> None:
        self.events.append("unload")

    def on_test_start(self, test_name: str, **kwargs: Any) -> None:
        self.events.append(f"test_start:{test_name}")

    def on_test_end(self, test_name: str, **kwargs: Any) -> None:
        self.events.append(f"test_end:{test_name}")

    def on_suite_start(self, **kwargs: Any) -> None:
        self.events.append("suite_start")

    def on_suite_end(self, **kwargs: Any) -> None:
        self.events.append("suite_end")


class TestPluginBase:
    """Test the abstract base class."""

    def test_concrete_plugin_name(self) -> None:
        plugin = _ConcretePlugin()
        assert plugin.name == "test-plugin"

    def test_concrete_plugin_type(self) -> None:
        plugin = _ConcretePlugin()
        assert plugin.plugin_type == PluginType.EVALUATOR

    def test_default_version(self) -> None:
        plugin = _ConcretePlugin()
        assert plugin.version == "0.1.0"

    def test_lifecycle_hooks_are_noops(self) -> None:
        plugin = _ConcretePlugin()
        plugin.on_load()
        plugin.on_unload()
        plugin.on_test_start("test")
        plugin.on_test_end("test")
        plugin.on_suite_start()
        plugin.on_suite_end()

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            PluginBase()  # type: ignore[abstract]


class TestTrackingPlugin:
    """Test lifecycle hook tracking."""

    def test_lifecycle_calls(self) -> None:
        plugin = _TrackingPlugin()
        plugin.on_load()
        plugin.on_suite_start()
        plugin.on_test_start("test_a")
        plugin.on_test_end("test_a")
        plugin.on_suite_end()
        plugin.on_unload()

        assert plugin.events == [
            "load",
            "suite_start",
            "test_start:test_a",
            "test_end:test_a",
            "suite_end",
            "unload",
        ]


class TestEvaluatorPlugin:
    """Test EvaluatorPlugin type."""

    def test_plugin_type(self) -> None:
        class MyEvalPlugin(EvaluatorPlugin):
            @property
            def name(self) -> str:
                return "my-eval"

            def create_evaluator(self) -> Any:
                return object()

        plugin = MyEvalPlugin()
        assert plugin.plugin_type == PluginType.EVALUATOR
        assert plugin.create_evaluator() is not None

    def test_cannot_instantiate_without_factory(self) -> None:
        with pytest.raises(TypeError):

            class IncompleteEval(EvaluatorPlugin):
                @property
                def name(self) -> str:
                    return "incomplete"

            IncompleteEval()  # type: ignore[abstract]


class TestAdapterPlugin:
    """Test AdapterPlugin type."""

    def test_plugin_type(self) -> None:
        class MyAdapterPlugin(AdapterPlugin):
            @property
            def name(self) -> str:
                return "my-adapter"

            def create_adapter(self) -> Any:
                return object()

        plugin = MyAdapterPlugin()
        assert plugin.plugin_type == PluginType.ADAPTER


class TestReporterPlugin:
    """Test ReporterPlugin type."""

    def test_plugin_type(self) -> None:
        class MyReporterPlugin(ReporterPlugin):
            @property
            def name(self) -> str:
                return "my-reporter"

            def create_reporter(self) -> Any:
                return object()

        plugin = MyReporterPlugin()
        assert plugin.plugin_type == PluginType.REPORTER


class TestStoragePlugin:
    """Test StoragePlugin type."""

    def test_plugin_type(self) -> None:
        class MyStoragePlugin(StoragePlugin):
            @property
            def name(self) -> str:
                return "my-storage"

            def create_storage(self) -> Any:
                return object()

        plugin = MyStoragePlugin()
        assert plugin.plugin_type == PluginType.STORAGE
