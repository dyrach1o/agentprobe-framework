# Custom Evaluator Cookbook

Practical recipes for building custom evaluators with AgentProbe. Each recipe includes complete, runnable code, example usage, and a brief explanation.

Before diving in, make sure you're familiar with the built-in evaluators covered in the [Evaluators guide](evaluators.md).

---

## Basics

### Minimal Evaluator

The simplest possible evaluator --- it checks that the agent produced non-empty output.

```python
from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class NonEmptyOutputEvaluator(BaseEvaluator):
    """Passes if the agent produced any output at all."""

    def __init__(self) -> None:
        super().__init__(name="non-empty-output")

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        if trace.output_text.strip():
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.PASS,
                score=1.0,
                reason="Output is non-empty",
            )
        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.FAIL,
            score=0.0,
            reason="Output is empty",
        )
```

**Usage:**

```python
evaluator = NonEmptyOutputEvaluator()
result = await evaluator.evaluate(test_case, trace)
assert result.verdict == EvalVerdict.PASS
```

The key points:

- Subclass `BaseEvaluator` and call `super().__init__(name=...)`.
- Implement `async def _evaluate(self, test_case, trace) -> EvalResult`.
- The base class wraps your `_evaluate()` with timing and error handling automatically.
- Always return an `EvalResult` with `evaluator_name`, `verdict`, `score`, and `reason`.

---

### Evaluator with Configuration

Add `__init__` parameters to make your evaluator configurable. Here, we add a minimum word count threshold:

```python
from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class MinWordCountEvaluator(BaseEvaluator):
    """Passes if the output contains at least `min_words` words."""

    def __init__(self, min_words: int = 10) -> None:
        super().__init__(name="min-word-count")
        self.min_words = min_words

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        word_count = len(trace.output_text.split())
        score = min(1.0, word_count / self.min_words)

        if word_count >= self.min_words:
            verdict = EvalVerdict.PASS
            reason = f"Word count {word_count} meets minimum of {self.min_words}"
        else:
            verdict = EvalVerdict.FAIL
            reason = f"Word count {word_count} is below minimum of {self.min_words}"

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=reason,
            metadata={"word_count": word_count, "min_words": self.min_words},
        )
```

**Usage:**

```python
# Strict threshold for detailed responses
strict = MinWordCountEvaluator(min_words=50)

# Lenient threshold for short answers
lenient = MinWordCountEvaluator(min_words=5)
```

Notice that `score` is a continuous value between 0.0 and 1.0, while `verdict` is a discrete enum. This lets downstream systems threshold on either.

---

## Recipes

### Output Format Validator

Validates that agent output conforms to a JSON Schema. Useful when your agent must produce structured data.

```python
import json
from typing import Any

from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class JsonSchemaEvaluator(BaseEvaluator):
    """Validates agent output against a JSON Schema.

    Checks two things:
    1. The output is valid JSON.
    2. The parsed JSON conforms to the provided schema.

    Requires the ``jsonschema`` package (pip install jsonschema).
    """

    def __init__(self, schema: dict[str, Any], name: str = "json-schema") -> None:
        super().__init__(name=name)
        self.schema = schema

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        import jsonschema

        # Step 1: parse JSON
        try:
            data = json.loads(trace.output_text)
        except json.JSONDecodeError as exc:
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.FAIL,
                score=0.0,
                reason=f"Output is not valid JSON: {exc}",
            )

        # Step 2: validate against schema
        validator = jsonschema.Draft7Validator(self.schema)
        errors = list(validator.iter_errors(data))

        if not errors:
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.PASS,
                score=1.0,
                reason="Output conforms to schema",
            )

        # Partial credit: fraction of top-level properties that are valid
        total_props = len(self.schema.get("properties", {})) or 1
        failing_props = len({e.path[0] for e in errors if e.path})
        score = max(0.0, 1.0 - (failing_props / total_props))

        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.PARTIAL if score > 0.0 else EvalVerdict.FAIL,
            score=score,
            reason=f"{len(errors)} schema violation(s): {errors[0].message}",
            metadata={"error_count": len(errors), "first_error": errors[0].message},
        )
```

**Usage:**

```python
schema = {
    "type": "object",
    "required": ["city", "temperature"],
    "properties": {
        "city": {"type": "string"},
        "temperature": {"type": "number"},
        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
    },
}

evaluator = JsonSchemaEvaluator(schema=schema)
result = await evaluator.evaluate(test_case, trace)
```

---

### Latency Budget Evaluator

Checks that the agent's total execution time stays within a budget. Useful for SLA enforcement or performance regression testing.

```python
from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class LatencyBudgetEvaluator(BaseEvaluator):
    """Passes if total trace latency is within the budget.

    Args:
        budget_ms: Maximum allowed latency in milliseconds.
        warn_pct: Percentage of budget at which to issue a PARTIAL verdict.
                  For example, 0.8 means PARTIAL if latency exceeds 80% of the budget.
    """

    def __init__(
        self,
        budget_ms: int = 5000,
        warn_pct: float = 0.8,
        name: str = "latency-budget",
    ) -> None:
        super().__init__(name=name)
        self.budget_ms = budget_ms
        self.warn_pct = warn_pct

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        actual_ms = trace.total_latency_ms
        utilization = actual_ms / self.budget_ms if self.budget_ms > 0 else 0.0

        # Score: 1.0 when at 0ms, linearly decreasing to 0.0 at budget_ms
        score = max(0.0, min(1.0, 1.0 - utilization))

        if actual_ms <= self.budget_ms * self.warn_pct:
            verdict = EvalVerdict.PASS
            reason = f"Latency {actual_ms}ms is within budget ({self.budget_ms}ms)"
        elif actual_ms <= self.budget_ms:
            verdict = EvalVerdict.PARTIAL
            reason = (
                f"Latency {actual_ms}ms is approaching budget "
                f"({self.warn_pct:.0%} of {self.budget_ms}ms)"
            )
        else:
            verdict = EvalVerdict.FAIL
            reason = f"Latency {actual_ms}ms exceeds budget of {self.budget_ms}ms"

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=reason,
            metadata={
                "actual_ms": actual_ms,
                "budget_ms": self.budget_ms,
                "utilization": round(utilization, 4),
            },
        )
```

**Usage:**

```python
evaluator = LatencyBudgetEvaluator(budget_ms=3000, warn_pct=0.75)
result = await evaluator.evaluate(test_case, trace)

if result.verdict == EvalVerdict.PARTIAL:
    print(f"Warning: {result.reason}")
```

---

### Tool Usage Auditor

Verifies that the agent called the expected tools in the expected order. This is useful for workflows where the sequence of tool calls matters (e.g., "search first, then summarize").

```python
from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class ToolUsageAuditor(BaseEvaluator):
    """Checks that the agent used the expected tools in the expected order.

    Args:
        expected_tools: Ordered list of tool names the agent should have called.
        strict_order: If True, tools must appear in the exact order given.
                      If False, all expected tools must appear but order is ignored.
    """

    def __init__(
        self,
        expected_tools: list[str],
        strict_order: bool = True,
        name: str = "tool-usage-auditor",
    ) -> None:
        super().__init__(name=name)
        self.expected_tools = expected_tools
        self.strict_order = strict_order

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        actual_tools = [tc.tool_name for tc in trace.tool_calls]

        if not self.expected_tools:
            # No expectations defined --- pass if no tools were called
            if not actual_tools:
                return EvalResult(
                    evaluator_name=self.name,
                    verdict=EvalVerdict.PASS,
                    score=1.0,
                    reason="No tools expected and none called",
                )
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.FAIL,
                score=0.0,
                reason=f"No tools expected but {len(actual_tools)} were called",
                metadata={"actual_tools": actual_tools},
            )

        if self.strict_order:
            return self._check_strict_order(actual_tools)
        return self._check_unordered(actual_tools)

    def _check_strict_order(self, actual_tools: list[str]) -> EvalResult:
        """Check that expected tools appear in exact order as a subsequence."""
        expected_idx = 0
        for tool in actual_tools:
            if expected_idx < len(self.expected_tools):
                if tool == self.expected_tools[expected_idx]:
                    expected_idx += 1

        matched = expected_idx
        total = len(self.expected_tools)
        score = matched / total if total > 0 else 1.0

        if matched == total:
            verdict = EvalVerdict.PASS
            reason = f"All {total} expected tools found in order"
        elif matched > 0:
            verdict = EvalVerdict.PARTIAL
            reason = f"{matched}/{total} expected tools found in order"
        else:
            verdict = EvalVerdict.FAIL
            reason = f"None of the {total} expected tools found in order"

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=reason,
            metadata={
                "expected_tools": self.expected_tools,
                "actual_tools": actual_tools,
                "matched_count": matched,
            },
        )

    def _check_unordered(self, actual_tools: list[str]) -> EvalResult:
        """Check that all expected tools were called, regardless of order."""
        actual_set = set(actual_tools)
        expected_set = set(self.expected_tools)
        found = expected_set & actual_set
        missing = expected_set - actual_set

        score = len(found) / len(expected_set) if expected_set else 1.0

        if not missing:
            verdict = EvalVerdict.PASS
            reason = f"All {len(expected_set)} expected tools were called"
        elif found:
            verdict = EvalVerdict.PARTIAL
            reason = f"Missing tools: {sorted(missing)}"
        else:
            verdict = EvalVerdict.FAIL
            reason = f"None of the expected tools were called"

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=reason,
            metadata={
                "expected_tools": self.expected_tools,
                "actual_tools": actual_tools,
                "missing_tools": sorted(missing),
            },
        )
```

**Usage:**

```python
# Strict: agent must search, then filter, then summarize --- in that order
auditor = ToolUsageAuditor(
    expected_tools=["search", "filter_results", "summarize"],
    strict_order=True,
)

# Lenient: all three tools must be called, but order does not matter
auditor_lenient = ToolUsageAuditor(
    expected_tools=["search", "filter_results", "summarize"],
    strict_order=False,
)

result = await auditor.evaluate(test_case, trace)
```

---

### Token Budget Evaluator

Checks that the total token consumption stays within a budget. Helps enforce cost discipline and detect prompts that cause excessive token usage.

```python
from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class TokenBudgetEvaluator(BaseEvaluator):
    """Passes if total tokens (input + output) are within the budget.

    Args:
        max_total_tokens: Maximum allowed total tokens.
        max_input_tokens: Maximum allowed input tokens (0 = no limit).
        max_output_tokens: Maximum allowed output tokens (0 = no limit).
    """

    def __init__(
        self,
        max_total_tokens: int = 10_000,
        max_input_tokens: int = 0,
        max_output_tokens: int = 0,
        name: str = "token-budget",
    ) -> None:
        super().__init__(name=name)
        self.max_total_tokens = max_total_tokens
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        total = trace.total_input_tokens + trace.total_output_tokens
        violations: list[str] = []

        if total > self.max_total_tokens:
            violations.append(
                f"Total tokens {total} exceeds budget of {self.max_total_tokens}"
            )

        if self.max_input_tokens > 0 and trace.total_input_tokens > self.max_input_tokens:
            violations.append(
                f"Input tokens {trace.total_input_tokens} exceeds limit of {self.max_input_tokens}"
            )

        if self.max_output_tokens > 0 and trace.total_output_tokens > self.max_output_tokens:
            violations.append(
                f"Output tokens {trace.total_output_tokens} exceeds limit of {self.max_output_tokens}"
            )

        if not violations:
            utilization = total / self.max_total_tokens if self.max_total_tokens > 0 else 0.0
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.PASS,
                score=max(0.0, 1.0 - utilization),
                reason=f"Token usage {total} is within budget of {self.max_total_tokens}",
                metadata={
                    "total_tokens": total,
                    "input_tokens": trace.total_input_tokens,
                    "output_tokens": trace.total_output_tokens,
                    "utilization": round(utilization, 4),
                },
            )

        # Score degrades based on how far over budget
        overage_ratio = total / self.max_total_tokens if self.max_total_tokens > 0 else 0.0
        score = max(0.0, min(1.0, 2.0 - overage_ratio))

        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.FAIL,
            score=score,
            reason="; ".join(violations),
            metadata={
                "total_tokens": total,
                "input_tokens": trace.total_input_tokens,
                "output_tokens": trace.total_output_tokens,
                "violations": violations,
            },
        )
```

**Usage:**

```python
evaluator = TokenBudgetEvaluator(
    max_total_tokens=8_000,
    max_input_tokens=6_000,
    max_output_tokens=2_000,
)
result = await evaluator.evaluate(test_case, trace)
print(f"Token utilization: {result.metadata.get('utilization', 'N/A')}")
```

---

### Regex Pattern Matcher

A custom evaluator that checks multiple regex patterns against the output, each with an individual weight. More flexible than the built-in `regex` rule type when you need multiple patterns with scoring.

```python
import re
from typing import Any

from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class RegexPatternMatcher(BaseEvaluator):
    """Checks multiple regex patterns against agent output with weighted scoring.

    Each pattern is a dict with keys:
        - ``pattern``: The regex string.
        - ``weight``: Relative importance (default 1.0).
        - ``description``: What the pattern checks (optional).
        - ``must_match``: If True (default), the pattern should match.
                          If False, the pattern should NOT match.
    """

    def __init__(
        self,
        patterns: list[dict[str, Any]],
        name: str = "regex-matcher",
    ) -> None:
        super().__init__(name=name)
        self.patterns = patterns

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        output = trace.output_text
        total_weight = 0.0
        earned_weight = 0.0
        details: list[dict[str, Any]] = []

        for spec in self.patterns:
            pattern = spec["pattern"]
            weight = spec.get("weight", 1.0)
            must_match = spec.get("must_match", True)
            description = spec.get("description", pattern)

            matched = re.search(pattern, output) is not None
            passed = matched if must_match else not matched

            total_weight += weight
            if passed:
                earned_weight += weight

            details.append({
                "pattern": pattern,
                "description": description,
                "matched": matched,
                "must_match": must_match,
                "passed": passed,
                "weight": weight,
            })

        score = earned_weight / total_weight if total_weight > 0 else 1.0
        all_passed = all(d["passed"] for d in details)
        any_passed = any(d["passed"] for d in details)

        if all_passed:
            verdict = EvalVerdict.PASS
        elif any_passed:
            verdict = EvalVerdict.PARTIAL
        else:
            verdict = EvalVerdict.FAIL

        failed = [d for d in details if not d["passed"]]
        if failed:
            reason = f"{len(failed)} pattern(s) failed: {failed[0]['description']}"
        else:
            reason = f"All {len(details)} patterns passed"

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=reason,
            metadata={"pattern_results": details},
        )
```

**Usage:**

```python
evaluator = RegexPatternMatcher(
    patterns=[
        {
            "pattern": r"\d{4}-\d{2}-\d{2}",
            "weight": 2.0,
            "description": "Contains ISO date",
        },
        {
            "pattern": r"https?://\S+",
            "weight": 1.0,
            "description": "Contains a URL",
        },
        {
            "pattern": r"(?i)error|exception|traceback",
            "weight": 3.0,
            "must_match": False,
            "description": "Must not contain error terms",
        },
    ],
)

result = await evaluator.evaluate(test_case, trace)
```

---

### Composite Evaluator

Runs multiple sub-evaluators and aggregates their results into a single score. This is the most powerful pattern --- compose any evaluators together with custom weighting.

```python
from agentprobe.eval.base import BaseEvaluator
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace


class CompositeEvaluator(BaseEvaluator):
    """Runs multiple sub-evaluators and aggregates their results.

    Each sub-evaluator contributes to the final score proportional to its weight.
    The overall verdict is determined by the aggregated score.

    Args:
        evaluators: List of (evaluator, weight) tuples.
        pass_threshold: Minimum score for a PASS verdict.
        partial_threshold: Minimum score for a PARTIAL verdict.
    """

    def __init__(
        self,
        evaluators: list[tuple[BaseEvaluator, float]],
        pass_threshold: float = 0.8,
        partial_threshold: float = 0.5,
        name: str = "composite",
    ) -> None:
        super().__init__(name=name)
        self.evaluators = evaluators
        self.pass_threshold = pass_threshold
        self.partial_threshold = partial_threshold

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        sub_results: list[dict] = []
        total_weight = 0.0
        weighted_score = 0.0

        for evaluator, weight in self.evaluators:
            result = await evaluator.evaluate(test_case, trace)
            total_weight += weight
            weighted_score += result.score * weight

            sub_results.append({
                "evaluator": result.evaluator_name,
                "verdict": result.verdict.value,
                "score": result.score,
                "reason": result.reason,
                "weight": weight,
            })

        score = weighted_score / total_weight if total_weight > 0 else 0.0

        if score >= self.pass_threshold:
            verdict = EvalVerdict.PASS
        elif score >= self.partial_threshold:
            verdict = EvalVerdict.PARTIAL
        else:
            verdict = EvalVerdict.FAIL

        passed_count = sum(1 for r in sub_results if r["verdict"] == "pass")
        total_count = len(sub_results)

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=round(score, 4),
            reason=f"{passed_count}/{total_count} sub-evaluators passed (weighted score: {score:.2f})",
            metadata={"sub_results": sub_results},
        )
```

**Usage:**

```python
composite = CompositeEvaluator(
    evaluators=[
        (NonEmptyOutputEvaluator(), 1.0),
        (LatencyBudgetEvaluator(budget_ms=5000), 2.0),
        (TokenBudgetEvaluator(max_total_tokens=8000), 1.5),
        (ToolUsageAuditor(expected_tools=["search"]), 3.0),
    ],
    pass_threshold=0.75,
    partial_threshold=0.4,
)

result = await composite.evaluate(test_case, trace)
print(f"Composite score: {result.score}")

# Inspect individual sub-evaluator results
for sub in result.metadata["sub_results"]:
    print(f"  {sub['evaluator']}: {sub['verdict']} ({sub['score']:.2f})")
```

---

## Testing Your Evaluator

Unit test custom evaluators by constructing `TestCase` and `Trace` objects directly. No agent or adapter is required.

```python
import asyncio
import pytest
from agentprobe.core.models import (
    EvalVerdict,
    TestCase,
    Trace,
    ToolCall,
)


# -- Fixtures for building test data --

def make_test_case(
    name: str = "test-case",
    input_text: str = "Hello",
    expected_output: str | None = None,
) -> TestCase:
    """Create a TestCase for testing evaluators."""
    return TestCase(
        name=name,
        input_text=input_text,
        expected_output=expected_output,
    )


def make_trace(
    output_text: str = "",
    agent_name: str = "test-agent",
    total_latency_ms: int = 100,
    total_input_tokens: int = 50,
    total_output_tokens: int = 50,
    tool_calls: tuple[ToolCall, ...] = (),
) -> Trace:
    """Create a Trace for testing evaluators."""
    return Trace(
        agent_name=agent_name,
        output_text=output_text,
        total_latency_ms=total_latency_ms,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        tool_calls=tool_calls,
    )


# -- Tests for the LatencyBudgetEvaluator --

class TestLatencyBudgetEvaluator:
    @pytest.mark.asyncio
    async def test_within_budget(self) -> None:
        evaluator = LatencyBudgetEvaluator(budget_ms=5000)
        tc = make_test_case()
        trace = make_trace(output_text="result", total_latency_ms=2000)

        result = await evaluator.evaluate(tc, trace)

        assert result.verdict == EvalVerdict.PASS
        assert result.score > 0.5

    @pytest.mark.asyncio
    async def test_over_budget(self) -> None:
        evaluator = LatencyBudgetEvaluator(budget_ms=1000)
        tc = make_test_case()
        trace = make_trace(output_text="result", total_latency_ms=3000)

        result = await evaluator.evaluate(tc, trace)

        assert result.verdict == EvalVerdict.FAIL
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_approaching_budget(self) -> None:
        evaluator = LatencyBudgetEvaluator(budget_ms=1000, warn_pct=0.8)
        tc = make_test_case()
        trace = make_trace(output_text="result", total_latency_ms=900)

        result = await evaluator.evaluate(tc, trace)

        assert result.verdict == EvalVerdict.PARTIAL


# -- Tests for the ToolUsageAuditor --

class TestToolUsageAuditor:
    @pytest.mark.asyncio
    async def test_correct_tool_order(self) -> None:
        auditor = ToolUsageAuditor(
            expected_tools=["search", "summarize"],
            strict_order=True,
        )
        tc = make_test_case()
        trace = make_trace(
            output_text="summary",
            tool_calls=(
                ToolCall(tool_name="search"),
                ToolCall(tool_name="summarize"),
            ),
        )

        result = await auditor.evaluate(tc, trace)

        assert result.verdict == EvalVerdict.PASS

    @pytest.mark.asyncio
    async def test_missing_tool(self) -> None:
        auditor = ToolUsageAuditor(
            expected_tools=["search", "summarize"],
            strict_order=False,
        )
        tc = make_test_case()
        trace = make_trace(
            output_text="output",
            tool_calls=(ToolCall(tool_name="search"),),
        )

        result = await auditor.evaluate(tc, trace)

        assert result.verdict == EvalVerdict.PARTIAL
        assert "summarize" in result.metadata["missing_tools"]
```

Run your evaluator tests with pytest:

```bash
pytest tests/test_evaluators.py -v
```

!!! tip "Construct minimal Trace objects"
    You only need to populate the fields your evaluator actually reads. The `Trace` model has sensible defaults for everything --- pass only what matters for the test.

---

## Distributing as a Plugin

Wrap your custom evaluator in an `EvaluatorPlugin` so other users can install and use it via the plugin system.

### 1. Create the plugin class

```python
from agentprobe.plugins.base import EvaluatorPlugin
from agentprobe.core.models import PluginType


class LatencyBudgetPlugin(EvaluatorPlugin):
    """Plugin that provides the LatencyBudgetEvaluator."""

    @property
    def name(self) -> str:
        return "latency-budget"

    @property
    def version(self) -> str:
        return "1.0.0"

    def create_evaluator(self):
        return LatencyBudgetEvaluator(budget_ms=5000)
```

### 2. Register via entry points

In your `pyproject.toml`:

```toml
[project.entry-points."agentprobe.plugins"]
latency-budget = "my_package.evaluators:LatencyBudgetPlugin"
```

### 3. Use the plugin

Once installed, the plugin is discovered automatically:

```python
from agentprobe.plugins.manager import PluginManager

manager = PluginManager()
manager.load_plugins()

# The evaluator is now available
evaluators = manager.get_evaluators()
```

Or register it programmatically:

```python
manager = PluginManager()
manager.load_plugins(classes=[LatencyBudgetPlugin])
```

See the [Creating Plugins](../plugins/creating-plugins.md) guide for the full plugin lifecycle, including hooks, file-based discovery, and testing patterns.
