"""Rule-based evaluator with configurable rules and weighted scoring.

Provides a declarative evaluation approach using built-in rule handlers
like ``contains_any``, ``not_contains``, ``max_length``, ``regex``, and
``json_valid``.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace
from agentprobe.eval.base import BaseEvaluator

logger = logging.getLogger(__name__)


class RuleSpec(BaseModel):
    """Specification for a single evaluation rule.

    Attributes:
        rule_type: The type of rule (e.g. 'contains_any', 'regex').
        params: Parameters for the rule handler.
        weight: Relative weight of this rule in the overall score.
        description: Human-readable description of what this rule checks.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    rule_type: str
    params: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, gt=0)
    description: str = ""


# ── Built-in rule handlers ──


def _contains_any(output: str, params: dict[str, Any]) -> bool:
    """Check if output contains any of the specified substrings."""
    substrings: list[str] = params.get("values", [])
    return any(s in output for s in substrings)


def _not_contains(output: str, params: dict[str, Any]) -> bool:
    """Check that output does NOT contain any of the specified substrings."""
    substrings: list[str] = params.get("values", [])
    return all(s not in output for s in substrings)


def _max_length(output: str, params: dict[str, Any]) -> bool:
    """Check that output length does not exceed the maximum."""
    max_len: int = params.get("max", 10000)
    return len(output) <= max_len


def _regex(output: str, params: dict[str, Any]) -> bool:
    """Check that output matches a regex pattern."""
    pattern: str = params.get("pattern", "")
    return re.search(pattern, output) is not None


def _json_valid(output: str, params: dict[str, Any]) -> bool:
    """Check that output is valid JSON."""
    try:
        json.loads(output)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


_RULE_HANDLERS: dict[str, Any] = {
    "contains_any": _contains_any,
    "not_contains": _not_contains,
    "max_length": _max_length,
    "regex": _regex,
    "json_valid": _json_valid,
}


class RuleBasedEvaluator(BaseEvaluator):
    """Evaluator that applies a set of declarative rules with weighted scoring.

    Each rule is checked against the agent output. The final score is
    the weighted average of passing rules.

    Attributes:
        rules: List of rule specifications to evaluate.
    """

    def __init__(
        self,
        name: str = "rule-based",
        rules: list[RuleSpec] | None = None,
    ) -> None:
        """Initialize the rule-based evaluator.

        Args:
            name: Evaluator name.
            rules: List of rule specifications. Defaults to empty.
        """
        super().__init__(name)
        self.rules = rules or []

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Evaluate the trace output against all configured rules.

        Args:
            test_case: The test case that was executed.
            trace: The execution trace to evaluate.

        Returns:
            An evaluation result with weighted score.
        """
        if not self.rules:
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.PASS,
                score=1.0,
                reason="No rules configured — pass by default",
            )

        output = trace.output_text
        total_weight = 0.0
        weighted_score = 0.0
        results: list[dict[str, Any]] = []

        for rule in self.rules:
            handler = _RULE_HANDLERS.get(rule.rule_type)
            if handler is None:
                logger.warning("Unknown rule type: %s", rule.rule_type)
                results.append(
                    {
                        "rule": rule.rule_type,
                        "passed": False,
                        "error": "unknown rule type",
                    }
                )
                total_weight += rule.weight
                continue

            passed = handler(output, rule.params)
            total_weight += rule.weight
            if passed:
                weighted_score += rule.weight

            results.append(
                {
                    "rule": rule.rule_type,
                    "description": rule.description,
                    "passed": passed,
                    "weight": rule.weight,
                }
            )

        score = weighted_score / total_weight if total_weight > 0 else 0.0
        all_passed = all(r["passed"] for r in results)

        _partial_threshold = 0.5
        if all_passed:
            verdict = EvalVerdict.PASS
        elif score >= _partial_threshold:
            verdict = EvalVerdict.PARTIAL
        else:
            verdict = EvalVerdict.FAIL

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=f"{int(weighted_score)}/{int(total_weight)} rules passed (weighted)",
            metadata={"rule_results": results},
        )
