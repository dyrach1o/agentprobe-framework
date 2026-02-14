# Evaluators

Evaluators score agent outputs against expected behavior. AgentProbe includes several built-in evaluators and supports custom implementations.

## Built-in Evaluators

### Rules-Based Evaluator

The `RuleBasedEvaluator` applies declarative rules with weighted scoring. Each rule checks a specific aspect of the output and contributes to the overall score.

```python
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec

evaluator = RuleBasedEvaluator(
    name="my-rules",
    rules=[
        RuleSpec(
            rule_type="contains_any",
            params={"substrings": ["hello", "hi", "hey"]},
            weight=1.0,
            description="Output should contain a greeting",
        ),
        RuleSpec(
            rule_type="not_contains",
            params={"substrings": ["error", "fail"]},
            weight=2.0,
            description="Output should not contain error terms",
        ),
        RuleSpec(
            rule_type="max_length",
            params={"max_length": 500},
            weight=0.5,
            description="Output should be concise",
        ),
    ],
)

result = await evaluator.evaluate(test_case, trace)
```

**Available rule types:**

| Rule Type | Parameters | Description |
|-----------|-----------|-------------|
| `contains_any` | `substrings: list[str]` | Output contains at least one substring |
| `not_contains` | `substrings: list[str]` | Output does not contain any substring |
| `max_length` | `max_length: int` | Output length does not exceed limit |
| `regex` | `pattern: str` | Output matches a regex pattern |
| `json_valid` | (none) | Output is valid JSON |

### Embedding Similarity Evaluator

Compares agent output against expected output using embedding vector cosine similarity:

```python
from agentprobe.eval.embedding import EmbeddingSimilarityEvaluator

evaluator = EmbeddingSimilarityEvaluator(
    model="text-embedding-3-small",
    provider="openai",
    threshold=0.8,
)

result = await evaluator.evaluate(test_case, trace)
# result.score is the cosine similarity (0.0 to 1.0)
```

Requires `expected_output` to be set on the `TestCase`. Uses caching to avoid redundant API calls.

### Judge Evaluator

Uses a language model to evaluate agent output against a rubric:

```python
from agentprobe.eval.llm_judge import LLMJudge

evaluator = LLMJudge(
    model="claude-sonnet-4-5-20250929",
    provider="anthropic",
    temperature=0.0,
    rubric="Evaluate whether the response is helpful, accurate, and concise.",
)

result = await evaluator.evaluate(test_case, trace)
```

The judge returns a structured verdict (PASS, FAIL, PARTIAL) with a score and reasoning.

### Statistical Evaluator

Wraps another evaluator and runs it across multiple traces to compute aggregate statistics:

```python
from agentprobe import StatisticalEvaluator
from agentprobe.eval.rules import RuleBasedEvaluator

inner = RuleBasedEvaluator(rules=[...])
evaluator = StatisticalEvaluator(inner, pass_threshold=0.7)

summary = await evaluator.evaluate_multiple(test_case, traces)
# summary.mean, summary.std_dev, summary.median, summary.p5, summary.p95
```

### Trace Comparison Evaluator

Compares a trace against a reference trace across multiple dimensions:

```python
from agentprobe import TraceComparisonEvaluator

evaluator = TraceComparisonEvaluator(
    reference_trace=baseline_trace,
    pass_threshold=0.7,
    weights={
        "tool_sequence": 0.3,
        "tool_parameters": 0.2,
        "output_similarity": 0.35,
        "cost_deviation": 0.15,
    },
)

result = await evaluator.evaluate(test_case, current_trace)
```

## Configuring Default Evaluators

Set default evaluators in `agentprobe.yaml`:

```yaml
eval:
  default_evaluators:
    - rules

judge:
  model: claude-sonnet-4-5-20250929
  provider: anthropic
  temperature: 0.0
  max_tokens: 1024
```

## Evaluation Results

Every evaluator returns an `EvalResult`:

| Field | Type | Description |
|-------|------|-------------|
| `evaluator_name` | `str` | Name of the evaluator |
| `verdict` | `EvalVerdict` | PASS, FAIL, PARTIAL, or ERROR |
| `score` | `float` | Numeric score (0.0 to 1.0) |
| `reason` | `str` | Human-readable explanation |
| `metadata` | `dict` | Additional evaluator-specific data |

**Verdicts:**

- `PASS` --- Output meets all criteria
- `FAIL` --- Output does not meet criteria
- `PARTIAL` --- Output partially meets criteria
- `ERROR` --- Evaluation itself failed
