# Regression Testing

AgentProbe's regression testing system helps you detect behavioral changes between agent versions by comparing test results against saved baselines.

## Overview

The regression testing workflow:

1. Run your test suite and save results as a **baseline**
2. Make changes to your agent
3. Run the test suite again and **compare** against the baseline
4. Review detected regressions and improvements

## Managing Baselines

### Save a Baseline

```bash
agentprobe baseline save my-baseline
```

### List Baselines

```bash
agentprobe baseline list
```

### Delete a Baseline

```bash
agentprobe baseline delete my-baseline
```

### Using the Python API

```python
from agentprobe import BaselineManager

manager = BaselineManager(baseline_dir=".agentprobe/baselines")

# Save results as a baseline
path = manager.save("v1.0", test_results)

# Load a baseline
baseline_results = manager.load("v1.0")

# Check if a baseline exists
if manager.exists("v1.0"):
    print("Baseline found")

# List all baselines
baselines = manager.list_baselines()
```

## Detecting Regressions

The `RegressionDetector` compares current test results against a baseline and flags significant score changes:

```python
from agentprobe import RegressionDetector

detector = RegressionDetector(threshold=0.05)

report = detector.compare(
    baseline_name="v1.0",
    baseline_results=baseline_results,
    current_results=current_results,
)
```

The `threshold` parameter controls sensitivity --- a score delta must exceed this value to be flagged. Default is `0.05` (5%).

## Configuration

```yaml
regression:
  enabled: true
  baseline_dir: .agentprobe/baselines
  threshold: 0.05
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `false` | Enable regression detection |
| `baseline_dir` | `string` | `.agentprobe/baselines` | Directory for baseline files |
| `threshold` | `float` | `0.05` | Score delta threshold (0.0--1.0) |

## Best Practices

1. **Save baselines at release points** --- name them after versions
2. **Set appropriate thresholds** --- too low causes noise, too high misses real regressions
3. **Integrate into CI/CD** --- compare against the latest stable baseline on every PR
4. **Review improvements too** --- unexpected score increases can indicate test issues
