# Creating Plugins

Step-by-step guide for building custom AgentProbe plugins.

## Step 1: Choose a Plugin Type

Decide what kind of plugin you need:

- **EvaluatorPlugin** --- Custom scoring logic for agent outputs
- **AdapterPlugin** --- Integration with a new agent framework
- **ReporterPlugin** --- Custom output format for test results
- **StoragePlugin** --- Custom backend for traces and results

## Step 2: Create the Plugin Class

Every plugin extends one of the typed base classes. Here's an evaluator plugin example:

```python
from agentprobe.plugins.base import EvaluatorPlugin, PluginType


class SentimentEvaluatorPlugin(EvaluatorPlugin):
    """Plugin that evaluates agent output sentiment."""

    @property
    def name(self) -> str:
        return "sentiment-evaluator"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

    @property
    def version(self) -> str:
        return "1.0.0"

    def on_load(self) -> None:
        print(f"Loaded {self.name} v{self.version}")

    def create_evaluator(self):
        from my_package.sentiment import SentimentEvaluator
        return SentimentEvaluator()
```

## Step 3: Implement Lifecycle Hooks

Override any lifecycle hooks you need:

```python
class MyPlugin(EvaluatorPlugin):
    def on_load(self) -> None:
        """Initialize resources when plugin loads."""
        self._client = create_client()

    def on_unload(self) -> None:
        """Clean up resources when plugin unloads."""
        self._client.close()

    def on_test_start(self, test_name: str, **kwargs) -> None:
        """Called before each test."""
        self._start_time = time.time()

    def on_test_end(self, test_name: str, **kwargs) -> None:
        """Called after each test."""
        elapsed = time.time() - self._start_time
        print(f"Test {test_name} took {elapsed:.2f}s")

    def on_suite_start(self, **kwargs) -> None:
        """Called before the test suite."""
        pass

    def on_suite_end(self, **kwargs) -> None:
        """Called after the test suite."""
        pass
```

All hooks have default no-op implementations, so you only need to override the ones you use.

## Step 4: Register the Plugin

### Option A: Entry Points (Recommended)

Add an entry point in your `pyproject.toml`:

```toml
[project.entry-points."agentprobe.plugins"]
sentiment = "my_package.plugins:SentimentEvaluatorPlugin"
```

Install your package and AgentProbe will discover it automatically.

### Option B: File-Based

Place your plugin module in a directory and configure AgentProbe:

```yaml
plugins:
  enabled: true
  directories:
    - plugins/
```

### Option C: Programmatic

Register plugins directly in code:

```python
from agentprobe import PluginManager

manager = PluginManager()
manager.load_plugins(classes=[SentimentEvaluatorPlugin])
```

## Step 5: Use the Plugin

Once registered, the plugin's artifacts are available through the `PluginManager`:

```python
manager = PluginManager()
manager.load_plugins()

# Get all evaluators from plugins
evaluators = manager.get_evaluators()

# Dispatch lifecycle events
manager.dispatch_suite_start()
manager.dispatch_test_start("my_test")
manager.dispatch_test_end("my_test")
manager.dispatch_suite_end()

# Clean up
manager.unload_all()
```

## Testing Your Plugin

```python
import pytest
from my_package.plugins import SentimentEvaluatorPlugin


class TestSentimentPlugin:
    def test_name(self) -> None:
        plugin = SentimentEvaluatorPlugin()
        assert plugin.name == "sentiment-evaluator"

    def test_creates_evaluator(self) -> None:
        plugin = SentimentEvaluatorPlugin()
        evaluator = plugin.create_evaluator()
        assert evaluator is not None

    def test_lifecycle(self) -> None:
        plugin = SentimentEvaluatorPlugin()
        plugin.on_load()
        plugin.on_test_start("test_1")
        plugin.on_test_end("test_1")
        plugin.on_unload()
```
