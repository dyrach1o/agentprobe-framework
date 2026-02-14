#!/usr/bin/env python3
"""Example: Creating and registering a custom plugin.

Demonstrates how to create a plugin by subclassing PluginBase,
register it with the PluginRegistry, and dispatch lifecycle
hooks through the PluginManager.
"""

from __future__ import annotations

import asyncio
import logging

from agentprobe.core.models import PluginType
from agentprobe.plugins.base import PluginBase
from agentprobe.plugins.manager import PluginManager
from agentprobe.plugins.registry import PluginRegistry

logging.basicConfig(level=logging.INFO)


class TimingPlugin(PluginBase):
    """A plugin that logs timing information for test lifecycle events."""

    @property
    def name(self) -> str:
        return "timing-plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

    def on_test_start(self, test_name: str) -> None:
        """Log when a test begins."""
        print(f"  [TimingPlugin] Test started: {test_name}")

    def on_test_end(self, test_name: str, passed: bool) -> None:
        """Log when a test ends with its outcome."""
        status = "PASSED" if passed else "FAILED"
        print(f"  [TimingPlugin] Test ended: {test_name} -> {status}")

    def on_suite_start(self) -> None:
        """Log when a test suite begins."""
        print("  [TimingPlugin] Suite started")

    def on_suite_end(self) -> None:
        """Log when a test suite ends."""
        print("  [TimingPlugin] Suite ended")


async def main() -> None:
    """Demonstrate plugin registration and lifecycle dispatch."""
    # Create and register the plugin
    registry = PluginRegistry()
    plugin = TimingPlugin()
    registry.register(plugin)

    print("=== Registered Plugins ===")
    for p in registry.list_plugins():
        print(f"  {p.name} v{p.version} ({p.plugin_type})")

    # Create a manager and dispatch lifecycle events
    manager = PluginManager(plugins=registry.list_plugins())

    print("\n=== Simulated Test Suite ===")
    manager.dispatch_suite_start()

    for test_name in ["test_greeting", "test_calculation", "test_error_handling"]:
        manager.dispatch_test_start(test_name)
        passed = test_name != "test_error_handling"
        manager.dispatch_test_end(test_name, passed=passed)

    manager.dispatch_suite_end()
    print("\nPlugin lifecycle demonstration complete.")


if __name__ == "__main__":
    asyncio.run(main())
