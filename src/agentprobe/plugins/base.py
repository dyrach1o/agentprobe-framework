"""Base plugin classes with lifecycle hooks and typed subclasses.

Plugins extend AgentProbe's functionality by implementing lifecycle hooks
and providing factory methods for evaluators, adapters, reporters, or
storage backends.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from agentprobe.core.models import PluginType

if TYPE_CHECKING:
    from agentprobe.core.protocols import (
        AdapterProtocol,
        EvaluatorProtocol,
        ReporterProtocol,
        StorageProtocol,
    )

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """Abstract base for all AgentProbe plugins.

    Plugins implement lifecycle hooks that are called at various points
    during test execution. Subclasses should override only the hooks
    they need — default implementations are no-ops.

    Attributes:
        name: Unique plugin identifier.
        plugin_type: The type of extension this plugin provides.
        version: Plugin version string.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique plugin name."""
        ...

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Return the plugin type."""
        ...

    @property
    def version(self) -> str:
        """Return the plugin version."""
        return "0.1.0"

    def on_load(self) -> None:  # noqa: B027
        """Called when the plugin is loaded into the registry."""

    def on_unload(self) -> None:  # noqa: B027
        """Called when the plugin is unloaded from the registry."""

    def on_test_start(self, test_name: str, **kwargs: Any) -> None:  # noqa: B027
        """Called before a test case begins execution.

        Args:
            test_name: Name of the test about to run.
            **kwargs: Additional context.
        """

    def on_test_end(self, test_name: str, **kwargs: Any) -> None:  # noqa: B027
        """Called after a test case completes execution.

        Args:
            test_name: Name of the test that completed.
            **kwargs: Additional context.
        """

    def on_suite_start(self, **kwargs: Any) -> None:  # noqa: B027
        """Called before a test suite begins execution.

        Args:
            **kwargs: Additional context.
        """

    def on_suite_end(self, **kwargs: Any) -> None:  # noqa: B027
        """Called after a test suite completes execution.

        Args:
            **kwargs: Additional context.
        """


class EvaluatorPlugin(PluginBase):
    """Plugin that provides a custom evaluator.

    Subclasses must implement ``create_evaluator()`` to return an object
    satisfying :class:`~agentprobe.core.protocols.EvaluatorProtocol`.
    """

    @property
    def plugin_type(self) -> PluginType:
        """Return EVALUATOR type."""
        return PluginType.EVALUATOR

    @abstractmethod
    def create_evaluator(self) -> EvaluatorProtocol:
        """Create and return an evaluator instance.

        Returns:
            An evaluator conforming to EvaluatorProtocol.
        """
        ...


class AdapterPlugin(PluginBase):
    """Plugin that provides a custom adapter.

    Subclasses must implement ``create_adapter()`` to return an object
    satisfying :class:`~agentprobe.core.protocols.AdapterProtocol`.
    """

    @property
    def plugin_type(self) -> PluginType:
        """Return ADAPTER type."""
        return PluginType.ADAPTER

    @abstractmethod
    def create_adapter(self) -> AdapterProtocol:
        """Create and return an adapter instance.

        Returns:
            An adapter conforming to AdapterProtocol.
        """
        ...


class ReporterPlugin(PluginBase):
    """Plugin that provides a custom reporter.

    Subclasses must implement ``create_reporter()`` to return an object
    satisfying :class:`~agentprobe.core.protocols.ReporterProtocol`.
    """

    @property
    def plugin_type(self) -> PluginType:
        """Return REPORTER type."""
        return PluginType.REPORTER

    @abstractmethod
    def create_reporter(self) -> ReporterProtocol:
        """Create and return a reporter instance.

        Returns:
            A reporter conforming to ReporterProtocol.
        """
        ...


class StoragePlugin(PluginBase):
    """Plugin that provides a custom storage backend.

    Subclasses must implement ``create_storage()`` to return an object
    satisfying :class:`~agentprobe.core.protocols.StorageProtocol`.
    """

    @property
    def plugin_type(self) -> PluginType:
        """Return STORAGE type."""
        return PluginType.STORAGE

    @abstractmethod
    def create_storage(self) -> StorageProtocol:
        """Create and return a storage instance.

        Returns:
            A storage backend conforming to StorageProtocol.
        """
        ...
