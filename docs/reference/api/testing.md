# Testing API Reference

::: agentprobe.testing

## Assert Helpers

### `assert_trace(trace)`

Create a fluent assertion chain for a `Trace`. Returns a `TraceAssertion`.

```python
from agentprobe.testing import assert_trace

assert_trace(trace).has_output().contains("hello").has_tool("search")
```

### `TraceAssertion`

Fluent chain returned by `assert_trace()`. All methods return `self` for chaining and raise `AssertionError` on failure.

| Method | Description |
|--------|-------------|
| `.has_output()` | Assert non-empty `output_text` |
| `.contains(s)` | Assert output contains substring `s` |
| `.not_contains(s)` | Assert output does NOT contain substring `s` |
| `.matches(pattern)` | Assert output matches regex `pattern` |
| `.has_tool_calls(min_count=1)` | Assert at least `min_count` tool calls |
| `.has_tool(name)` | Assert a tool call with `name` exists |
| `.has_llm_calls(min_count=1)` | Assert at least `min_count` LLM calls |
| `.output_length_less_than(n)` | Assert output length < `n` |
| `.output_is_valid_json()` | Assert output parses as valid JSON |

### `assert_score(trace, evaluator, *, min_score=0.7, ...)`

**Async.** Run an evaluator against a trace and assert the score meets a threshold.

```python
result = await assert_score(trace, evaluator, min_score=0.8)
# result is an EvalResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trace` | `Trace` | required | Execution trace to evaluate |
| `evaluator` | `BaseEvaluator` | required | Evaluator to run |
| `min_score` | `float` | `0.7` | Minimum acceptable score |
| `input_text` | `str` | `""` | Input text for test case context |
| `test_name` | `str` | `"assert_score"` | Name for synthetic test case |

**Returns:** `EvalResult`

**Raises:** `AssertionError` if `score < min_score`

### `assert_cost(trace, *, max_usd, calculator=None)`

**Sync.** Calculate trace cost and assert it is within budget.

```python
summary = assert_cost(trace, max_usd=0.01)
# summary is a CostSummary
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trace` | `Trace` | required | Execution trace to price |
| `max_usd` | `float` | required | Maximum allowed cost in USD |
| `calculator` | `CostCalculator \| None` | `None` | Custom calculator (uses defaults if None) |

**Returns:** `CostSummary`

**Raises:** `AssertionError` if `total_cost_usd > max_usd`

## pytest Plugin

::: agentprobe.pytest_plugin

### Fixtures

#### `agentprobe` (function-scoped)

Returns an `AgentProbeContext` for each test.

```python
async def test_agent(agentprobe):
    trace = await agentprobe.invoke("input", adapter=my_adapter)
```

#### `agentprobe_config` (session-scoped)

Returns `AgentProbeConfig` loaded from `--agentprobe-config` or defaults.

#### `agentprobe_storage` (session-scoped)

Returns an initialized `SQLiteStorage`. Only instantiated when `--agentprobe-store-traces` is used.

### `AgentProbeContext`

| Method / Property | Type | Description |
|-------------------|------|-------------|
| `invoke(input_text, adapter, **kwargs)` | async | Invoke adapter and collect trace |
| `evaluate(trace, evaluator, ...)` | async | Run evaluator on trace |
| `calculate_cost(trace)` | sync | Calculate cost summary |
| `traces` | `list[Trace]` | All traces collected in this test |
| `last_trace` | `Trace` | Most recent trace (raises if empty) |
| `config` | `AgentProbeConfig` | The loaded configuration |

### CLI Options

| Option | Description |
|--------|-------------|
| `--agentprobe-config PATH` | Path to `agentprobe.yaml` |
| `--agentprobe-trace-dir DIR` | Directory for trace database |
| `--agentprobe-store-traces` | Persist traces to SQLite |

### Marker

```python
@pytest.mark.agentprobe
async def test_my_agent(agentprobe):
    ...
```

Disable the plugin: `pytest -p no:agentprobe`
