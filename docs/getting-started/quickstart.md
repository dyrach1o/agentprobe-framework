# Quickstart

Get up and running with AgentProbe in minutes.

## 1. Install AgentProbe

```bash
pip install agentprobe-framework
```

## 2. Initialize Your Project

```bash
agentprobe init
```

This creates an `agentprobe.yaml` configuration file with sensible defaults.

## 3. Write Your First Test

Create a file `tests/test_my_agent.py`:

```python
from agentprobe import scenario, expect

@scenario(
    name="greeting_test",
    input_text="Say hello to the user",
    tags=["smoke"],
)
def test_greeting():
    """Agent should produce a friendly greeting."""
    pass
```

The `@scenario` decorator registers the function as a test case. When AgentProbe discovers this file, it creates a `TestCase` with the specified name, input, and tags.

## 4. Discover Tests

```bash
agentprobe test -d tests/
```

Output:

```
Discovered 1 test case(s)
  - greeting_test [tags: smoke]
```

## 5. Working with Traces

AgentProbe records execution traces for every agent run. Traces capture tool calls, token usage, latency, and outputs.

### List Traces

```bash
agentprobe trace list
```

### View a Specific Trace

```bash
agentprobe trace show <trace-id>
```

This shows full trace details including agent name, model, input/output, token counts, latency, and tool calls.

## Example: Multi-Scenario Test File

```python
from agentprobe import scenario

@scenario(
    name="summarization_test",
    input_text="Summarize the following article: ...",
    tags=["eval", "summarization"],
)
def test_summarization():
    """Agent should produce a concise summary."""
    pass

@scenario(
    name="tool_usage_test",
    input_text="Search for the current weather in London",
    tags=["tools", "search"],
)
def test_tool_usage():
    """Agent should invoke the search tool."""
    pass

@scenario(
    name="error_handling_test",
    input_text="Process this invalid JSON: {broken",
    tags=["robustness"],
    timeout=10.0,
)
def test_error_handling():
    """Agent should handle malformed input gracefully."""
    pass
```

## Example: Using Assertions

```python
from agentprobe import scenario, expect

@scenario(name="math_test", input_text="What is 2 + 2?")
def test_math():
    pass

# After running, evaluate the trace:
# expect(trace).output_contains("4")
# expect(trace).has_tool_calls(count=0)
```

## Next Steps

- [Configuration](configuration.md) --- Customize AgentProbe for your project
- [Writing Tests](../guides/writing-tests.md) --- In-depth test authoring guide
- [Evaluators](../guides/evaluators.md) --- Set up behavioral evaluation
- [Safety Testing](../guides/safety-testing.md) --- Run security test suites
- [CLI Reference](../reference/cli.md) --- All available commands
