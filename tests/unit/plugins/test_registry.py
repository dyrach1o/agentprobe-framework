"""Tests for the plugin registry."""

from __future__ import annotations

import pytest

from agentprobe.core.exceptions import PluginError
from agentprobe.core.models import PluginType
from agentprobe.plugins.base import PluginBase
from agentprobe.plugins.registry import PluginRegistry


class _FakePlugin(PluginBase):
    def __init__(self, name: str = "fake", plugin_type: PluginType = PluginType.EVALUATOR) -> None:
        self._name = name
        self._plugin_type = plugin_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def plugin_type(self) -> PluginType:
        return self._plugin_type


class TestPluginRegistry:
    """Test registry CRUD operations."""

    @pytest.fixture
    def registry(self) -> PluginRegistry:
        return PluginRegistry()

    def test_register_and_get(self, registry: PluginRegistry) -> None:
        plugin = _FakePlugin("test")
        registry.register(plugin)
        assert registry.get("test") is plugin

    def test_register_duplicate_raises(self, registry: PluginRegistry) -> None:
        plugin = _FakePlugin("test")
        registry.register(plugin)
        with pytest.raises(PluginError, match="already registered"):
            registry.register(_FakePlugin("test"))

    def test_unregister(self, registry: PluginRegistry) -> None:
        registry.register(_FakePlugin("test"))
        registry.unregister("test")
        assert registry.get("test") is None

    def test_unregister_nonexistent_raises(self, registry: PluginRegistry) -> None:
        with pytest.raises(PluginError, match="not registered"):
            registry.unregister("ghost")

    def test_get_nonexistent_returns_none(self, registry: PluginRegistry) -> None:
        assert registry.get("nonexistent") is None

    def test_list_plugins(self, registry: PluginRegistry) -> None:
        registry.register(_FakePlugin("a"))
        registry.register(_FakePlugin("b"))
        plugins = registry.list_plugins()
        assert len(plugins) == 2
        names = {p.name for p in plugins}
        assert names == {"a", "b"}

    def test_list_by_type(self, registry: PluginRegistry) -> None:
        registry.register(_FakePlugin("eval1", PluginType.EVALUATOR))
        registry.register(_FakePlugin("adapter1", PluginType.ADAPTER))
        registry.register(_FakePlugin("eval2", PluginType.EVALUATOR))

        evals = registry.list_by_type(PluginType.EVALUATOR)
        assert len(evals) == 2
        adapters = registry.list_by_type(PluginType.ADAPTER)
        assert len(adapters) == 1
        reporters = registry.list_by_type(PluginType.REPORTER)
        assert len(reporters) == 0

    def test_clear(self, registry: PluginRegistry) -> None:
        registry.register(_FakePlugin("a"))
        registry.register(_FakePlugin("b"))
        registry.clear()
        assert len(registry) == 0
        assert registry.list_plugins() == []

    def test_len(self, registry: PluginRegistry) -> None:
        assert len(registry) == 0
        registry.register(_FakePlugin("a"))
        assert len(registry) == 1

    def test_contains(self, registry: PluginRegistry) -> None:
        registry.register(_FakePlugin("test"))
        assert "test" in registry
        assert "other" not in registry
