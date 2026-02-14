# Multi-Agent Testing

AgentProbe supports testing multiple agents and comparing their behavior side-by-side.

## Testing Multiple Agents

Use adapters to connect AgentProbe to different agent frameworks:

```python
from agentprobe.adapters.langchain import LangChainAdapter
from agentprobe.core.runner import TestRunner
from agentprobe.core.config import load_config

config = load_config()

adapters = [
    LangChainAdapter(name="agent-v1"),
    LangChainAdapter(name="agent-v2"),
]

runner = TestRunner(config=config)

for adapter in adapters:
    run = await runner.run(test_cases, adapter)
    print(f"{adapter.name}: {run.passed}/{run.total_tests} passed")
```

## Comparing Agent Versions

Use trace comparison to quantify differences between agent versions:

```python
from agentprobe import TraceComparisonEvaluator

trace_v1 = await adapter_v1.invoke("What is the weather?")
trace_v2 = await adapter_v2.invoke("What is the weather?")

evaluator = TraceComparisonEvaluator(
    reference_trace=trace_v1,
    pass_threshold=0.7,
)

result = await evaluator.evaluate(test_case, trace_v2)
print(f"Similarity score: {result.score:.2f}")
```

## Multi-Turn Conversations

Test agents across multi-turn dialogues:

```python
from agentprobe import ConversationRunner

runner = ConversationRunner(
    adapter=my_adapter,
    evaluators=[my_evaluator],
)

result = await runner.run(
    turns=[
        "Book a flight to London",
        "Make it for next Tuesday",
        "Economy class, please",
    ],
    agent_name="booking-agent",
)

print(f"Turns passed: {result.passed_turns}/{result.total_turns}")
print(f"Aggregate score: {result.aggregate_score:.2f}")
```

## Statistical Comparison

Compare agents across multiple runs using the `StatisticalEvaluator`:

```python
from agentprobe import StatisticalEvaluator
from agentprobe.eval.rules import RuleBasedEvaluator

inner = RuleBasedEvaluator(rules=[...])
evaluator = StatisticalEvaluator(inner, pass_threshold=0.7)

traces = [await adapter.invoke(input_text) for _ in range(10)]

summary = await evaluator.evaluate_multiple(test_case, traces)
print(f"Mean score: {summary.mean:.3f} +/- {summary.std_dev:.3f}")
```

## Best Practices

1. **Use the same test cases** across agents for fair comparison
2. **Run multiple iterations** to account for non-deterministic behavior
3. **Compare costs** alongside quality scores
4. **Track metrics over time** with the metrics system
5. **Save baselines** per agent version for regression tracking
