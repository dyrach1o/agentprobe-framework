"""Plugin registry: stores and retrieves plugins by name and type.

Provides a simple dict-based registry with type filtering support.
"""

from __future__ import annotations

import logging

from agentprobe.core.exceptions import PluginError
from agentprobe.core.models import PluginType
from agentprobe.plugins.base import PluginBase

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing loaded plugins.

    Stores plugins by name and provides lookup by name or type.
    Prevents duplicate registrations.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginBase] = {}

    def register(self, plugin: PluginBase) -> None:
        """Register a plugin.

        Args:
            plugin: The plugin to register.

        Raises:
            PluginError: If a plugin with the same name is already registered.
        """
        if plugin.name in self._plugins:
            raise PluginError(f"Plugin '{plugin.name}' is already registered")
        self._plugins[plugin.name] = plugin
        logger.info("Registered plugin '%s' (type=%s)", plugin.name, plugin.plugin_type)

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name.

        Args:
            name: The plugin name to remove.

        Raises:
            PluginError: If no plugin with the given name is registered.
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' is not registered")
        del self._plugins[name]
        logger.info("Unregistered plugin '%s'", name)

    def get(self, name: str) -> PluginBase | None:
        """Get a plugin by name.

        Args:
            name: The plugin name to look up.

        Returns:
            The plugin if found, otherwise None.
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[PluginBase]:
        """Return all registered plugins.

        Returns:
            A list of all plugins in registration order.
        """
        return list(self._plugins.values())

    def list_by_type(self, plugin_type: PluginType) -> list[PluginBase]:
        """Return all plugins of a given type.

        Args:
            plugin_type: The type to filter by.

        Returns:
            A list of matching plugins.
        """
        return [p for p in self._plugins.values() if p.plugin_type == plugin_type]

    def clear(self) -> None:
        """Remove all registered plugins."""
        self._plugins.clear()
        logger.info("Plugin registry cleared")

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        return name in self._plugins
