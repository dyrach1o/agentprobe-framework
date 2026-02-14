# Plugin Types

Reference for all supported plugin types in AgentProbe.

## Base Class: `PluginBase`

All plugins extend `PluginBase`, which defines the common interface:

```python
from agentprobe.plugins.base import PluginBase

class PluginBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType: ...

    @property
    def version(self) -> str:
        return "0.1.0"

    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
    def on_test_start(self, test_name: str, **kwargs) -> None: ...
    def on_test_end(self, test_name: str, **kwargs) -> None: ...
    def on_suite_start(self, **kwargs) -> None: ...
    def on_suite_end(self, **kwargs) -> None: ...
```

## `PluginType` Enum

```python
class PluginType(StrEnum):
    EVALUATOR = "evaluator"
    ADAPTER = "adapter"
    REPORTER = "reporter"
    STORAGE = "storage"
```

---

## EvaluatorPlugin

Provides a custom evaluator for scoring agent outputs.

```python
from agentprobe.plugins.base import EvaluatorPlugin, PluginType

class MyEvaluatorPlugin(EvaluatorPlugin):
    @property
    def name(self) -> str:
        return "my-evaluator"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR

    def create_evaluator(self):
        """Create and return an evaluator instance.

        The returned object must implement the evaluator protocol:
        - name: str (property)
        - evaluate(test_case, trace) -> EvalResult (async method)
        """
        return MyCustomEvaluator()
```

**Required method:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_evaluator()` | `EvaluatorProtocol` | Factory for custom evaluator |

---

## AdapterPlugin

Provides a custom adapter for integrating with agent frameworks.

```python
from agentprobe.plugins.base import AdapterPlugin, PluginType

class MyAdapterPlugin(AdapterPlugin):
    @property
    def name(self) -> str:
        return "my-adapter"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.ADAPTER

    def create_adapter(self):
        """Create and return an adapter instance.

        The returned object must implement the adapter protocol:
        - name: str (property)
        - invoke(input_text, **kwargs) -> Trace (async method)
        """
        return MyCustomAdapter()
```

**Required method:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_adapter()` | `AdapterProtocol` | Factory for custom adapter |

---

## ReporterPlugin

Provides a custom reporter for formatting test results.

```python
from agentprobe.plugins.base import ReporterPlugin, PluginType

class MyReporterPlugin(ReporterPlugin):
    @property
    def name(self) -> str:
        return "my-reporter"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.REPORTER

    def create_reporter(self):
        """Create and return a reporter instance.

        The returned object must implement the reporter protocol:
        - name: str (property)
        - generate(run) -> str (method)
        """
        return MyCustomReporter()
```

**Required method:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_reporter()` | `ReporterProtocol` | Factory for custom reporter |

---

## StoragePlugin

Provides a custom storage backend for traces and results.

```python
from agentprobe.plugins.base import StoragePlugin, PluginType

class MyStoragePlugin(StoragePlugin):
    @property
    def name(self) -> str:
        return "my-storage"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.STORAGE

    def create_storage(self):
        """Create and return a storage instance.

        The returned object must implement the storage protocol:
        - setup() (async method)
        - save_trace(trace) (async method)
        - load_trace(trace_id) -> Trace | None (async method)
        - list_traces(**filters) -> list[Trace] (async method)
        - close() (async method)
        """
        return MyCustomStorage()
```

**Required method:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_storage()` | `StorageProtocol` | Factory for custom backend |

---

## Collecting Plugin Artifacts

The `PluginManager` provides methods to collect artifacts from all loaded plugins:

```python
manager = PluginManager()
manager.load_plugins()

evaluators = manager.get_evaluators()      # From all EvaluatorPlugins
adapters = manager.get_adapters()          # From all AdapterPlugins
reporters = manager.get_reporters()        # From all ReporterPlugins
storage_backends = manager.get_storage_backends()  # From all StoragePlugins
```
