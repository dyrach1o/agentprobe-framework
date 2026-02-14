# Adapters Reference

Adapters connect AgentProbe to agent frameworks. Each adapter wraps a specific framework's agent, invokes it with test inputs, and returns a structured `Trace`.

## Adapter Interface

All adapters implement the same interface:

```python
class BaseAdapter:
    @property
    def name(self) -> str:
        """Return the adapter name."""
        ...

    async def invoke(self, input_text: str, **kwargs) -> Trace:
        """Invoke the agent and return a trace."""
        ...
```

The `invoke` method handles trace recording internally using a `_TraceBuilder`:

1. Create a `_TraceBuilder` via `_create_builder()`
2. Record LLM calls and tool calls during execution
3. Build and return a frozen `Trace`

## Built-in Adapters

### LangChain

```python
from agentprobe.adapters.langchain import LangChainAdapter
```

Wraps LangChain agents and chains. Records all LLM calls and tool invocations captured by LangChain's callback system.

**Usage:**

```python
adapter = LangChainAdapter(name="my-langchain-agent")
trace = await adapter.invoke("What is the weather?")
```

### CrewAI

```python
from agentprobe.adapters.crewai import CrewAIAdapter
```

Wraps CrewAI crews and agents. Captures crew execution including agent delegation and tool usage.

### AutoGen

```python
from agentprobe.adapters.autogen import AutoGenAdapter
```

Wraps AutoGen agent conversations. Records messages between agents and tool calls.

### MCP (Model Context Protocol)

```python
from agentprobe.adapters.mcp import MCPAdapter
```

Wraps MCP-compatible servers. Records tool calls made through the MCP protocol.

## Creating Custom Adapters

Subclass `BaseAdapter` and implement the `_invoke` method:

```python
from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.models import LLMCall, Trace

class MyAdapter(BaseAdapter):
    def __init__(self, agent, name: str = "my-adapter") -> None:
        super().__init__(name)
        self._agent = agent

    async def _invoke(self, input_text: str, **kwargs) -> Trace:
        builder = self._create_builder(model="my-model")
        builder.input_text = input_text

        # Call your agent
        response = await self._agent.run(input_text)

        # Record the LLM call
        builder.add_llm_call(LLMCall(
            model="my-model",
            input_text=input_text,
            output_text=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
        ))

        builder.output_text = response.text
        return builder.build()
```

### Using the Trace Builder

The `_TraceBuilder` provides methods for recording execution events:

| Method | Description |
|--------|-------------|
| `add_llm_call(call)` | Record a model call with tokens and latency |
| `add_tool_call(call)` | Record a tool invocation with input/output |
| `build()` | Produce a frozen, immutable `Trace` |

Set `input_text`, `output_text`, `tags`, and `metadata` as attributes on the builder before calling `build()`.

## Registering Adapters via Plugins

Adapters can be distributed as plugins. See [Plugin Types](../plugins/plugin-types.md) for the `AdapterPlugin` interface.
