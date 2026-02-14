# Plugins Overview

AgentProbe supports a plugin system for extending functionality with custom evaluators, reporters, adapters, and storage backends.

## Architecture

The plugin system has three main components:

1. **PluginBase** --- Abstract base class that all plugins extend
2. **PluginRegistry** --- Manages plugin registration and lookup
3. **PluginManager** --- Orchestrates plugin lifecycle and event dispatch

```
PluginManager
├── PluginRegistry (stores registered plugins)
├── PluginLoader (discovers plugins from entry points and directories)
└── Event Dispatch (test_start, test_end, suite_start, suite_end)
```

## Plugin Types

AgentProbe supports four plugin types:

| Type | Base Class | Purpose |
|------|-----------|---------|
| Evaluator | `EvaluatorPlugin` | Custom evaluation logic |
| Adapter | `AdapterPlugin` | Custom agent framework integration |
| Reporter | `ReporterPlugin` | Custom output formats |
| Storage | `StoragePlugin` | Custom storage backends |

See [Plugin Types](plugin-types.md) for detailed API reference.

## Plugin Discovery

Plugins are discovered from two sources:

### Entry Points

Register plugins in your package's `pyproject.toml`:

```toml
[project.entry-points."agentprobe.plugins"]
my-evaluator = "my_package.evaluator:MyEvaluatorPlugin"
```

### File-Based Discovery

Point AgentProbe to directories containing plugin modules:

```yaml
plugins:
  enabled: true
  directories:
    - plugins/
    - /path/to/shared/plugins/
```

## Plugin Lifecycle

Plugins receive lifecycle events:

1. **`on_load()`** --- Called when the plugin is loaded and registered
2. **`on_test_start(test_name)`** --- Called before each test execution
3. **`on_test_end(test_name)`** --- Called after each test execution
4. **`on_suite_start()`** --- Called before the test suite begins
5. **`on_suite_end()`** --- Called after the test suite completes
6. **`on_unload()`** --- Called when the plugin is unloaded

## Error Isolation

The `PluginManager` catches exceptions from individual plugins during event dispatch. A failing plugin does not affect other plugins or the test execution.

## Configuration

```yaml
plugins:
  enabled: true
  directories: []
  entry_point_group: agentprobe.plugins
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable the plugin system |
| `directories` | `list[str]` | `[]` | Additional plugin directories |
| `entry_point_group` | `str` | `"agentprobe.plugins"` | Entry point group name |

## Next Steps

- [Creating Plugins](creating-plugins.md) --- Step-by-step guide
- [Plugin Types](plugin-types.md) --- API reference for each type
