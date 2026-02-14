"""Plugin system: loader, registry, and base classes for extensibility."""

from agentprobe.plugins.base import (
    AdapterPlugin,
    EvaluatorPlugin,
    PluginBase,
    ReporterPlugin,
    StoragePlugin,
)
from agentprobe.plugins.loader import PluginLoader
from agentprobe.plugins.manager import PluginManager
from agentprobe.plugins.registry import PluginRegistry

__all__ = [
    "AdapterPlugin",
    "EvaluatorPlugin",
    "PluginBase",
    "PluginLoader",
    "PluginManager",
    "PluginRegistry",
    "ReporterPlugin",
    "StoragePlugin",
]
