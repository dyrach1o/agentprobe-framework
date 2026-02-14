# Writing Tests

This guide covers how to write effective tests for your software agents using AgentProbe.

## pytest Plugin (Recommended)

The fastest way to test agents is with the built-in pytest plugin. Install AgentProbe and the `agentprobe` fixture is automatically available in your tests --- no configuration needed.

### Basic Test

```python
# test_my_agent.py
from agentprobe.testing import assert_trace, assert_score, assert_cost
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

evaluator = RuleBasedEvaluator(rules=[
    RuleSpec(rule_type="max_length", params={"max": 3000}),
    RuleSpec(rule_type="not_contains", params={"values": ["error", "fail"]}),
])

async def test_greeting(agentprobe):
    trace = await agentprobe.invoke("Say hello", adapter=my_adapter)

    # Fluent trace assertions (raise AssertionError on failure)
    assert_trace(trace).has_output().contains("hello").not_contains("error")

    # Evaluator threshold check
    result = await assert_score(trace, evaluator, min_score=0.8)

    # Cost budget check
    assert_cost(trace, max_usd=0.01)
```

Run with standard pytest:

```bash
pytest tests/ -v
```

### The `agentprobe` Fixture

The `agentprobe` fixture provides an `AgentProbeContext` with these methods:

| Method | Type | Description |
|--------|------|-------------|
| `invoke(input_text, adapter, **kwargs)` | async | Invoke adapter, collect trace |
| `evaluate(trace, evaluator, ...)` | async | Run evaluator on trace |
| `calculate_cost(trace)` | sync | Calculate cost summary |
| `traces` | property | All traces collected in this test |
| `last_trace` | property | Most recent trace |

The adapter is passed per-call, so you create it in your own fixture or at module level:

```python
import pytest

@pytest.fixture
def my_adapter():
    return MyAgentAdapter(name="my-agent", model="claude-sonnet-4-5-20250929")

async def test_agent(agentprobe, my_adapter):
    trace = await agentprobe.invoke("What is 2+2?", adapter=my_adapter)
    assert_trace(trace).has_output().has_tool("calculator")
```

### Assert Helpers

#### `assert_trace(trace)`

Returns a `TraceAssertion` with chainable methods:

```python
(
    assert_trace(trace)
    .has_output()                   # non-empty output
    .contains("Paris")              # substring check
    .not_contains("error")          # absence check
    .matches(r"\d+ degrees")        # regex match
    .has_tool_calls(min_count=2)    # at least N tool calls
    .has_tool("search")             # specific tool was called
    .has_llm_calls(min_count=1)     # at least N model calls
    .output_length_less_than(5000)  # length limit
    .output_is_valid_json()         # JSON parse check
)
```

All methods raise `AssertionError` on failure --- pytest natively introspects these for rich failure output.

#### `await assert_score(trace, evaluator, min_score=0.7)`

Runs the evaluator and asserts `score >= min_score`. Returns the `EvalResult`.

#### `assert_cost(trace, max_usd=0.01)`

Calculates cost and asserts `total_cost_usd <= max_usd`. Returns a `CostSummary`.

### Plugin Options

```bash
pytest --agentprobe-config path/to/agentprobe.yaml
pytest --agentprobe-trace-dir ./traces
pytest --agentprobe-store-traces  # persist traces to SQLite
```

Disable the plugin with `-p no:agentprobe`.

---

## Scenario-Based Tests

For the standalone AgentProbe runner, use the `@scenario` decorator:

### The `@scenario` Decorator

```python
from agentprobe import scenario

@scenario(
    name="greeting_test",
    input_text="Say hello to the user",
    expected_output="Hello! How can I help you?",
    tags=["smoke", "greeting"],
    timeout=15.0,
    evaluators=["rules"],
)
def test_greeting():
    """Agent should produce a friendly greeting."""
    pass
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str \| None` | Function name | Test case identifier |
| `input_text` | `str` | `""` | Input prompt for the agent |
| `expected_output` | `str \| None` | `None` | Expected output for comparison |
| `tags` | `list[str] \| None` | `None` | Tags for filtering and grouping |
| `timeout` | `float` | `30.0` | Maximum execution time in seconds |
| `evaluators` | `list[str] \| None` | `None` | Evaluator names to apply |

### Test Discovery

```bash
agentprobe test                          # default test_dir
agentprobe test -d tests/agent_tests/    # specific directory
agentprobe test -p "check_*.py"          # custom pattern
```

## Fluent Assertions (Legacy)

The `expect()` / `expect_tool_calls()` API collects results without raising:

```python
from agentprobe import expect, expect_tool_calls

passed = (
    expect(output)
    .to_contain("result")
    .to_not_contain("error")
    .to_have_length_less_than(1000)
    .all_passed()
)

assert expect_tool_calls(trace.tool_calls).to_contain("search").all_passed()
```

For new tests, prefer `assert_trace()` which raises immediately on failure.

## Multi-Turn Conversations

Use `ConversationRunner` for testing multi-turn dialogue:

```python
from agentprobe import ConversationRunner

runner = ConversationRunner(adapter=my_adapter, evaluators=[my_evaluator])
result = await runner.run(
    turns=["Hello", "Tell me about X", "Thanks, goodbye"],
    agent_name="support-agent",
)

assert result.passed_turns == result.total_turns
```

## Running Tests

### With pytest (Recommended)

```bash
pytest tests/ -v                        # standard run
pytest tests/ -v --agentprobe-store-traces  # persist traces
pytest tests/ -k "test_greeting"        # filter by name
pytest tests/ -m agentprobe             # only @pytest.mark.agentprobe tests
```

### With the AgentProbe CLI

```bash
agentprobe test -d tests/
agentprobe test --parallel
agentprobe test -c path/to/agentprobe.yaml
```

## Test Organization

```
tests/
├── test_greeting.py       # Basic interaction tests
├── test_search.py         # Search tool tests
├── test_calculation.py    # Math/calculation tests
├── test_error_handling.py # Edge cases and errors
└── test_multi_turn.py     # Conversation tests
```
