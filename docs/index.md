# AgentProbe

**A testing and evaluation framework for software agents.**

AgentProbe provides a comprehensive toolkit for testing autonomous software agents. Record execution traces, evaluate agent behavior, detect regressions, run safety scans, and track costs --- all from a single CLI or Python API.

## Key Features

### Trace Recording
Capture every decision, tool call, and output during agent execution into structured, replayable traces. Replay traces for debugging or comparison.

### Behavioral Evaluation
Evaluate agent outputs using rules-based checks, embedding similarity, judge-based scoring, or statistical analysis with pluggable evaluators.

### Regression Detection
Establish baselines and automatically flag behavioral regressions between agent versions. Set custom thresholds for score deltas.

### Safety Scanning
Run built-in test suites for prompt injection, data leakage, jailbreaking, role confusion, hallucination, and tool abuse.

### Cost Management
Track token usage and costs per model, enforce per-test and per-suite budgets, and generate cost reports with breakdowns by model.

### Plugin System
Extend AgentProbe with custom evaluators, adapters, reporters, and storage backends using the plugin API.

## Quick Links

- [Installation](getting-started/installation.md) --- Get AgentProbe installed
- [Quickstart](getting-started/quickstart.md) --- Write and run your first tests
- [Configuration](getting-started/configuration.md) --- Full YAML config reference
- [Writing Tests](guides/writing-tests.md) --- Test patterns and best practices
- [CLI Reference](reference/cli.md) --- All CLI commands and options
- [Evaluators](guides/evaluators.md) --- Built-in and custom evaluators
- [Plugin System](plugins/overview.md) --- Extend AgentProbe with plugins

## Architecture Overview

```
agentprobe/
├── core/       # Test runner, discovery, assertions, config
├── eval/       # Evaluators: rules, embedding, judge, statistical
├── trace/      # Recorder, replay, diff, time travel
├── cost/       # Calculator, pricing data, budgets
├── safety/     # Scanner, test suites, payloads
├── regression/ # Detector, baselines, behavioral diff
├── adapters/   # LangChain, CrewAI, AutoGen, MCP
├── metrics/    # Collection, aggregation, trending
├── storage/    # SQLite, PostgreSQL backends
├── reporting/  # Terminal, HTML, JUnit, JSON, Markdown, CSV
├── plugins/    # Plugin loader, registry, base classes
└── cli/        # Click-based CLI commands
```
