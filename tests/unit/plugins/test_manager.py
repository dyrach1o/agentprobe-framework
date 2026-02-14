"""Tests for the plugin manager."""

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
from agentprobe.plugins.manager import PluginManager


class _StubPlugin(PluginBase):
    def __init__(self, name: str = "stub") -> None:
        self._name = name
        self.events: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

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


class _FaultyPlugin(PluginBase):
    def __init__(self, name: str = "faulty") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

    def on_test_start(self, test_name: str, **kwargs: Any) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    def on_test_end(self, test_name: str, **kwargs: Any) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    def on_suite_start(self, **kwargs: Any) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    def on_suite_end(self, **kwargs: Any) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    def on_unload(self) -> None:
        msg = "boom"
        raise RuntimeError(msg)


class _MockEvalPlugin(EvaluatorPlugin):
    def __init__(self, name: str = "mock-eval") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def create_evaluator(self) -> Any:
        return type("FakeEvaluator", (), {"name": "fake-eval"})()


class _MockAdapterPlugin(AdapterPlugin):
    def __init__(self, name: str = "mock-adapter") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def create_adapter(self) -> Any:
        return type("FakeAdapter", (), {"name": "fake-adapter"})()


class _MockReporterPlugin(ReporterPlugin):
    def __init__(self, name: str = "mock-reporter") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def create_reporter(self) -> Any:
        return type("FakeReporter", (), {"name": "fake-reporter"})()


class _MockStoragePlugin(StoragePlugin):
    def __init__(self, name: str = "mock-storage") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def create_storage(self) -> Any:
        return type("FakeStorage", (), {"name": "fake-storage"})()


class TestPluginManager:
    """Test plugin manager lifecycle and dispatch."""

    @pytest.fixture
    def manager(self) -> PluginManager:
        return PluginManager(entry_point_group="nonexistent.group")

    def test_load_from_classes(self, manager: PluginManager) -> None:
        plugins = manager.load_plugins(classes=[_StubPlugin])
        assert len(plugins) == 1
        assert "stub" in manager.registry

    def test_on_load_called(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_StubPlugin])
        plugin = manager.registry.get("stub")
        assert plugin is not None
        assert isinstance(plugin, _StubPlugin)
        assert "load" in plugin.events

    def test_unload_all(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_StubPlugin])
        plugin = manager.registry.get("stub")
        assert plugin is not None
        manager.unload_all()
        assert len(manager.registry) == 0
        assert isinstance(plugin, _StubPlugin)
        assert "unload" in plugin.events

    def test_dispatch_test_start(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_StubPlugin])
        manager.dispatch_test_start("test_a")
        plugin = manager.registry.get("stub")
        assert isinstance(plugin, _StubPlugin)
        assert "test_start:test_a" in plugin.events

    def test_dispatch_test_end(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_StubPlugin])
        manager.dispatch_test_end("test_a")
        plugin = manager.registry.get("stub")
        assert isinstance(plugin, _StubPlugin)
        assert "test_end:test_a" in plugin.events

    def test_dispatch_suite_start(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_StubPlugin])
        manager.dispatch_suite_start()
        plugin = manager.registry.get("stub")
        assert isinstance(plugin, _StubPlugin)
        assert "suite_start" in plugin.events

    def test_dispatch_suite_end(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_StubPlugin])
        manager.dispatch_suite_end()
        plugin = manager.registry.get("stub")
        assert isinstance(plugin, _StubPlugin)
        assert "suite_end" in plugin.events


class TestPluginManagerErrorIsolation:
    """Test that faulty plugins don't break the manager."""

    @pytest.fixture
    def manager(self) -> PluginManager:
        return PluginManager(entry_point_group="nonexistent.group")

    def test_faulty_test_start_isolated(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_FaultyPlugin])
        manager.dispatch_test_start("test_a")

    def test_faulty_test_end_isolated(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_FaultyPlugin])
        manager.dispatch_test_end("test_a")

    def test_faulty_suite_start_isolated(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_FaultyPlugin])
        manager.dispatch_suite_start()

    def test_faulty_suite_end_isolated(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_FaultyPlugin])
        manager.dispatch_suite_end()

    def test_faulty_unload_isolated(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_FaultyPlugin])
        manager.unload_all()


class TestPluginManagerFactories:
    """Test factory collection from typed plugins."""

    @pytest.fixture
    def manager(self) -> PluginManager:
        return PluginManager(entry_point_group="nonexistent.group")

    def test_get_evaluators(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_MockEvalPlugin])
        evaluators = manager.get_evaluators()
        assert len(evaluators) == 1

    def test_get_adapters(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_MockAdapterPlugin])
        adapters = manager.get_adapters()
        assert len(adapters) == 1

    def test_get_reporters(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_MockReporterPlugin])
        reporters = manager.get_reporters()
        assert len(reporters) == 1

    def test_get_storage_backends(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_MockStoragePlugin])
        backends = manager.get_storage_backends()
        assert len(backends) == 1

    def test_empty_when_no_plugins(self, manager: PluginManager) -> None:
        assert manager.get_evaluators() == []
        assert manager.get_adapters() == []
        assert manager.get_reporters() == []
        assert manager.get_storage_backends() == []

    def test_mixed_plugins(self, manager: PluginManager) -> None:
        manager.load_plugins(classes=[_MockEvalPlugin, _MockAdapterPlugin])
        assert len(manager.get_evaluators()) == 1
        assert len(manager.get_adapters()) == 1
        assert len(manager.get_reporters()) == 0
