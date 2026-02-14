"""Plugin manager: orchestrates plugin lifecycle and event dispatch.

Coordinates loading, registration, lifecycle hooks, and factory
collection across all loaded plugins.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agentprobe.core.models import PluginType
from agentprobe.plugins.base import (
    AdapterPlugin,
    EvaluatorPlugin,
    PluginBase,
    ReporterPlugin,
    StoragePlugin,
)
from agentprobe.plugins.loader import PluginLoader
from agentprobe.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from agentprobe.core.protocols import (
        AdapterProtocol,
        EvaluatorProtocol,
        ReporterProtocol,
        StorageProtocol,
    )

logger = logging.getLogger(__name__)


class PluginManager:
    """Orchestrates plugin lifecycle and event dispatch.

    Manages the full lifecycle of plugins: loading from sources,
    registering, dispatching lifecycle events, and collecting
    factory-created objects from typed plugins.

    Attributes:
        registry: The plugin registry.
    """

    def __init__(
        self,
        entry_point_group: str = "agentprobe.plugins",
    ) -> None:
        """Initialize the plugin manager.

        Args:
            entry_point_group: Entry point group for plugin discovery.
        """
        self.registry = PluginRegistry()
        self._loader = PluginLoader(entry_point_group=entry_point_group)

    def load_plugins(
        self,
        directories: list[str] | None = None,
        classes: list[type[PluginBase]] | None = None,
    ) -> list[PluginBase]:
        """Load and register plugins from all sources.

        Args:
            directories: Additional directories to scan.
            classes: Direct class references to load.

        Returns:
            A list of all loaded and registered plugins.
        """
        loaded: list[PluginBase] = []

        discovered = self._loader.load_all(directories=directories)
        for plugin in discovered:
            self._safe_register(plugin)
            loaded.append(plugin)

        for cls in classes or []:
            try:
                plugin = self._loader.load_from_class(cls)
                self._safe_register(plugin)
                loaded.append(plugin)
            except Exception:
                logger.exception("Failed to load plugin class %s", cls.__name__)

        return loaded

    def unload_all(self) -> None:
        """Unload all plugins, calling on_unload for each."""
        for plugin in self.registry.list_plugins():
            try:
                plugin.on_unload()
            except Exception:
                logger.exception("Error during on_unload for plugin '%s'", plugin.name)
        self.registry.clear()

    def dispatch_test_start(self, test_name: str, **kwargs: Any) -> None:
        """Dispatch on_test_start to all registered plugins.

        Errors from individual plugins are logged but do not propagate.

        Args:
            test_name: Name of the test starting.
            **kwargs: Additional context.
        """
        for plugin in self.registry.list_plugins():
            try:
                plugin.on_test_start(test_name, **kwargs)
            except Exception:
                logger.exception("Plugin '%s' failed in on_test_start", plugin.name)

    def dispatch_test_end(self, test_name: str, **kwargs: Any) -> None:
        """Dispatch on_test_end to all registered plugins.

        Args:
            test_name: Name of the test ending.
            **kwargs: Additional context.
        """
        for plugin in self.registry.list_plugins():
            try:
                plugin.on_test_end(test_name, **kwargs)
            except Exception:
                logger.exception("Plugin '%s' failed in on_test_end", plugin.name)

    def dispatch_suite_start(self, **kwargs: Any) -> None:
        """Dispatch on_suite_start to all registered plugins.

        Args:
            **kwargs: Additional context.
        """
        for plugin in self.registry.list_plugins():
            try:
                plugin.on_suite_start(**kwargs)
            except Exception:
                logger.exception("Plugin '%s' failed in on_suite_start", plugin.name)

    def dispatch_suite_end(self, **kwargs: Any) -> None:
        """Dispatch on_suite_end to all registered plugins.

        Args:
            **kwargs: Additional context.
        """
        for plugin in self.registry.list_plugins():
            try:
                plugin.on_suite_end(**kwargs)
            except Exception:
                logger.exception("Plugin '%s' failed in on_suite_end", plugin.name)

    def get_evaluators(self) -> list[EvaluatorProtocol]:
        """Collect evaluators from all EvaluatorPlugin instances.

        Returns:
            A list of evaluator instances.
        """
        evaluators: list[EvaluatorProtocol] = []
        for plugin in self.registry.list_by_type(PluginType.EVALUATOR):
            if isinstance(plugin, EvaluatorPlugin):
                try:
                    evaluators.append(plugin.create_evaluator())
                except Exception:
                    logger.exception("Plugin '%s' failed to create evaluator", plugin.name)
        return evaluators

    def get_adapters(self) -> list[AdapterProtocol]:
        """Collect adapters from all AdapterPlugin instances.

        Returns:
            A list of adapter instances.
        """
        adapters: list[AdapterProtocol] = []
        for plugin in self.registry.list_by_type(PluginType.ADAPTER):
            if isinstance(plugin, AdapterPlugin):
                try:
                    adapters.append(plugin.create_adapter())
                except Exception:
                    logger.exception("Plugin '%s' failed to create adapter", plugin.name)
        return adapters

    def get_reporters(self) -> list[ReporterProtocol]:
        """Collect reporters from all ReporterPlugin instances.

        Returns:
            A list of reporter instances.
        """
        reporters: list[ReporterProtocol] = []
        for plugin in self.registry.list_by_type(PluginType.REPORTER):
            if isinstance(plugin, ReporterPlugin):
                try:
                    reporters.append(plugin.create_reporter())
                except Exception:
                    logger.exception("Plugin '%s' failed to create reporter", plugin.name)
        return reporters

    def get_storage_backends(self) -> list[StorageProtocol]:
        """Collect storage backends from all StoragePlugin instances.

        Returns:
            A list of storage backend instances.
        """
        backends: list[StorageProtocol] = []
        for plugin in self.registry.list_by_type(PluginType.STORAGE):
            if isinstance(plugin, StoragePlugin):
                try:
                    backends.append(plugin.create_storage())
                except Exception:
                    logger.exception("Plugin '%s' failed to create storage", plugin.name)
        return backends

    def _safe_register(self, plugin: PluginBase) -> None:
        """Register a plugin, calling on_load after registration.

        Args:
            plugin: The plugin to register.
        """
        self.registry.register(plugin)
        try:
            plugin.on_load()
        except Exception:
            logger.exception("Plugin '%s' failed in on_load", plugin.name)
