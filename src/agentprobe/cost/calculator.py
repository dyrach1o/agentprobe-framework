"""Cost calculator for agent execution traces.

Loads pricing data from YAML files and computes per-call and
per-trace costs based on token usage.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from agentprobe.core.exceptions import BudgetExceededError
from agentprobe.core.models import CostBreakdown, CostSummary, LLMCall, Trace

logger = logging.getLogger(__name__)

_DEFAULT_PRICING_DIR = Path(__file__).parent / "pricing_data"


class PricingEntry(BaseModel):
    """Pricing for a single model.

    Attributes:
        model: Model identifier.
        input_cost_per_1k: Cost per 1,000 input tokens in USD.
        output_cost_per_1k: Cost per 1,000 output tokens in USD.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    model: str
    input_cost_per_1k: float = Field(ge=0.0)
    output_cost_per_1k: float = Field(ge=0.0)


class PricingConfig(BaseModel):
    """Collection of pricing entries.

    Attributes:
        entries: Mapping of model name to pricing entry.
    """

    model_config = ConfigDict(extra="forbid")

    entries: dict[str, PricingEntry] = Field(default_factory=dict)

    @classmethod
    def load_from_dir(cls, pricing_dir: str | Path | None = None) -> PricingConfig:
        """Load pricing data from all YAML files in a directory.

        Args:
            pricing_dir: Directory containing pricing YAML files.
                Defaults to the bundled pricing_data directory.

        Returns:
            A PricingConfig with all entries loaded.
        """
        directory = Path(pricing_dir) if pricing_dir else _DEFAULT_PRICING_DIR
        entries: dict[str, PricingEntry] = {}

        if not directory.is_dir():
            logger.warning("Pricing directory not found: %s", directory)
            return cls(entries=entries)

        for yaml_file in sorted(directory.glob("*.yaml")):
            try:
                raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    continue
                models = raw.get("models", [])
                for model_data in models:
                    if isinstance(model_data, dict) and "model" in model_data:
                        entry = PricingEntry.model_validate(model_data)
                        entries[entry.model] = entry
            except Exception:
                logger.exception("Failed to load pricing from %s", yaml_file)

        logger.info("Loaded pricing for %d models", len(entries))
        return cls(entries=entries)


class CostCalculator:
    """Calculates costs for agent execution traces.

    Uses pricing data to compute per-call costs, aggregates by model,
    and optionally enforces budget limits.

    Attributes:
        pricing: The pricing configuration.
        budget_limit_usd: Optional maximum cost per trace.
    """

    def __init__(
        self,
        pricing: PricingConfig | None = None,
        budget_limit_usd: float | None = None,
    ) -> None:
        """Initialize the cost calculator.

        Args:
            pricing: Pricing configuration. Loads defaults if None.
            budget_limit_usd: Optional budget limit in USD.
        """
        self._pricing = pricing or PricingConfig.load_from_dir()
        self._budget_limit = budget_limit_usd

    def calculate_llm_cost(self, call: LLMCall) -> float:
        """Calculate the cost of a single LLM call.

        Args:
            call: The LLM call to price.

        Returns:
            Cost in USD.
        """
        entry = self._pricing.entries.get(call.model)
        if entry is None:
            logger.warning("No pricing found for model: %s", call.model)
            return 0.0

        input_cost = (call.input_tokens / 1000.0) * entry.input_cost_per_1k
        output_cost = (call.output_tokens / 1000.0) * entry.output_cost_per_1k
        return input_cost + output_cost

    def calculate_trace_cost(self, trace: Trace) -> CostSummary:
        """Calculate the total cost for a trace.

        Args:
            trace: The execution trace to price.

        Returns:
            A CostSummary with per-model breakdown.

        Raises:
            BudgetExceededError: If budget_limit_usd is set and exceeded.
        """
        breakdowns: dict[str, dict[str, Any]] = {}

        for call in trace.llm_calls:
            cost = self.calculate_llm_cost(call)
            entry = self._pricing.entries.get(call.model)
            input_cost = 0.0
            output_cost = 0.0
            if entry is not None:
                input_cost = (call.input_tokens / 1000.0) * entry.input_cost_per_1k
                output_cost = (call.output_tokens / 1000.0) * entry.output_cost_per_1k

            if call.model not in breakdowns:
                breakdowns[call.model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "input_cost_usd": 0.0,
                    "output_cost_usd": 0.0,
                    "total_cost_usd": 0.0,
                    "call_count": 0,
                }

            bd = breakdowns[call.model]
            bd["input_tokens"] += call.input_tokens
            bd["output_tokens"] += call.output_tokens
            bd["input_cost_usd"] += input_cost
            bd["output_cost_usd"] += output_cost
            bd["total_cost_usd"] += cost
            bd["call_count"] += 1

        model_breakdowns = {
            model: CostBreakdown(model=model, **data) for model, data in breakdowns.items()
        }

        total_llm = sum(bd.total_cost_usd for bd in model_breakdowns.values())
        total_input = sum(bd.input_tokens for bd in model_breakdowns.values())
        total_output = sum(bd.output_tokens for bd in model_breakdowns.values())

        summary = CostSummary(
            total_llm_cost_usd=total_llm,
            total_tool_cost_usd=0.0,
            total_cost_usd=total_llm,
            breakdown_by_model=model_breakdowns,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
        )

        if self._budget_limit is not None and total_llm > self._budget_limit:
            raise BudgetExceededError(total_llm, self._budget_limit)

        return summary
