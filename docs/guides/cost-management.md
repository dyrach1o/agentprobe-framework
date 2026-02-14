# Cost Management

AgentProbe tracks token usage and costs across all agent executions, helping you manage expenses and set budgets.

## Cost Calculator

The `CostCalculator` uses YAML-based pricing data to compute costs from traces:

```python
from agentprobe.cost.calculator import CostCalculator

calculator = CostCalculator()

# Calculate cost for a trace
summary = calculator.calculate_trace_cost(trace)

print(f"Total cost: ${summary.total_cost_usd:.4f}")
print(f"Input tokens: {summary.total_input_tokens}")
print(f"Output tokens: {summary.total_output_tokens}")
```

The `CostSummary` includes a breakdown by model:

```python
for model, cost in summary.breakdown_by_model.items():
    print(f"  {model}: ${cost:.4f}")
```

## Pricing Data

AgentProbe includes built-in pricing data for common models. You can provide custom pricing via YAML files:

```yaml
# pricing/anthropic.yaml
models:
  - model: claude-sonnet-4-5-20250929
    input_cost_per_1k: 0.003
    output_cost_per_1k: 0.015
```

Point AgentProbe to your pricing directory:

```yaml
cost:
  enabled: true
  pricing_dir: pricing/
```

## Budget Enforcement

Set per-test and per-suite cost limits with `BudgetEnforcer`:

```python
from agentprobe import BudgetEnforcer

enforcer = BudgetEnforcer(
    test_budget_usd=0.50,
    suite_budget_usd=5.00,
)

# Check a single test
check = enforcer.check_test(cost_summary)

# Check entire suite
check = enforcer.check_suite(all_cost_summaries)
```

## CLI Commands

### Cost Report

```bash
agentprobe cost report
agentprobe cost report -a my-agent
agentprobe cost report -f json
```

### Budget Status

```bash
agentprobe cost budget
agentprobe cost budget --max-cost 0.50 --max-tokens 1000
```

## Configuration

```yaml
cost:
  enabled: true
  budget_limit_usd: 10.00
  pricing_dir: pricing/

budget:
  test_budget_usd: 0.50
  suite_budget_usd: 5.00
```

## Best Practices

1. **Set budget limits** to prevent runaway costs during development
2. **Track costs per model** to optimize model selection
3. **Monitor cost trends** using the metrics system
4. **Use pricing overrides** for custom or self-hosted models
5. **Include cost checks in CI** to catch expensive test changes
