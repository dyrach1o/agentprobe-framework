"""Plugin loader: discovers and loads plugins from entry points and paths.

Supports two discovery mechanisms:
1. Entry points (``importlib.metadata``) for installed packages.
2. File paths (``importlib.util``) for local plugin files.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import logging
from pathlib import Path
from typing import Any

from agentprobe.core.exceptions import PluginError
from agentprobe.plugins.base import PluginBase

logger = logging.getLogger(__name__)


class PluginLoader:
    """Loads plugin classes from various sources.

    Discovers and instantiates plugins from Python entry points,
    file paths, or direct class references.
    """

    def __init__(self, entry_point_group: str = "agentprobe.plugins") -> None:
        """Initialize the plugin loader.

        Args:
            entry_point_group: Entry point group name for discovery.
        """
        self._entry_point_group = entry_point_group

    def load_from_entry_points(self) -> list[PluginBase]:
        """Discover and load plugins from installed package entry points.

        Returns:
            A list of loaded plugin instances.
        """
        plugins: list[PluginBase] = []
        try:
            eps = importlib.metadata.entry_points()
        except Exception:
            logger.exception("Failed to read entry points")
            return plugins

        group_eps: list[Any] = []
        if hasattr(eps, "select"):
            group_eps = list(eps.select(group=self._entry_point_group))
        elif isinstance(eps, dict):
            group_eps = eps.get(self._entry_point_group, [])  # pragma: no cover

        for ep in group_eps:
            try:
                plugin_cls = ep.load()
                plugin = self._instantiate(plugin_cls, source=f"entry_point:{ep.name}")
                plugins.append(plugin)
            except Exception:
                logger.exception("Failed to load plugin from entry point '%s'", ep.name)

        return plugins

    def load_from_path(self, path: str | Path) -> PluginBase:
        """Load a plugin from a Python file path.

        The file must contain exactly one class that subclasses PluginBase.

        Args:
            path: Path to the Python file containing the plugin.

        Returns:
            The loaded plugin instance.

        Raises:
            PluginError: If the file cannot be loaded or contains no plugin class.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise PluginError(f"Plugin file not found: {file_path}")
        if not file_path.suffix == ".py":
            raise PluginError(f"Plugin file must be a .py file: {file_path}")

        module_name = f"agentprobe_plugin_{file_path.stem}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise PluginError(f"Cannot create module spec for: {file_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except PluginError:
            raise
        except Exception as exc:
            raise PluginError(f"Failed to load module from {file_path}: {exc}") from exc

        plugin_classes = [
            obj
            for name in dir(module)
            if not name.startswith("_")
            and isinstance(obj := getattr(module, name), type)
            and issubclass(obj, PluginBase)
            and obj is not PluginBase
        ]

        if not plugin_classes:
            raise PluginError(f"No PluginBase subclass found in {file_path}")

        return self._instantiate(plugin_classes[0], source=str(file_path))

    def load_from_class(self, cls: type[PluginBase]) -> PluginBase:
        """Load a plugin from a direct class reference.

        Args:
            cls: The plugin class to instantiate.

        Returns:
            The loaded plugin instance.

        Raises:
            PluginError: If the class is not a PluginBase subclass.
        """
        if not (isinstance(cls, type) and issubclass(cls, PluginBase)):
            raise PluginError(f"{cls} is not a PluginBase subclass")
        return self._instantiate(cls, source=f"class:{cls.__name__}")

    def load_all(
        self,
        directories: list[str] | None = None,
    ) -> list[PluginBase]:
        """Load plugins from entry points and optional directories.

        Args:
            directories: Additional directories to scan for .py plugin files.

        Returns:
            A list of all loaded plugin instances.
        """
        plugins = self.load_from_entry_points()

        for dir_path in directories or []:
            path = Path(dir_path)
            if not path.is_dir():
                logger.warning("Plugin directory not found: %s", dir_path)
                continue
            for py_file in sorted(path.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                try:
                    plugin = self.load_from_path(py_file)
                    plugins.append(plugin)
                except PluginError:
                    logger.exception("Failed to load plugin from %s", py_file)

        return plugins

    def _instantiate(self, cls: type, source: str) -> PluginBase:
        """Instantiate a plugin class with error handling.

        Args:
            cls: The class to instantiate.
            source: Description of where the class came from (for logging).

        Returns:
            The plugin instance.

        Raises:
            PluginError: If instantiation fails.
        """
        try:
            instance = cls()
        except Exception as exc:
            raise PluginError(f"Failed to instantiate plugin from {source}: {exc}") from exc

        if not isinstance(instance, PluginBase):
            raise PluginError(f"Plugin from {source} is not a PluginBase instance")

        logger.info("Loaded plugin '%s' from %s", instance.name, source)
        return instance
