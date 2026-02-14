# Changelog

All notable changes to AgentProbe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-05-15

### Added

- PostgreSQL `load_result(result_id)` method for API parity with SQLite
- Dedicated migration test suite (`test_migrations.py`)
- `TraceDiffer` for structural comparison between any two traces
- `TraceDiffReport` model with token/latency deltas and similarity scoring
- Dashboard CLI command tests (`test_dashboard_cmd.py`)
- Pricing data for Google (Gemini), Mistral, and Cohere models
- `FieldEncryptor` with SHA-256 hashing and partial masking
- `AuditLogger` with structured JSON event logging
- Parametrized tests across 6 test modules for edge case coverage
- PyPI release workflow with trusted publisher
- MkDocs documentation deployment to GitHub Pages
- Dependabot configuration for pip and GitHub Actions

### Changed

- Development status upgraded from Alpha to Beta
- Version bumped from 0.4.0 to 0.5.0

## [0.4.0] - 2025-04-15

### Added

- Dashboard REST API with FastAPI: health, traces, results, and metrics endpoints
- `agentprobe dashboard` CLI command with lazy FastAPI/uvicorn imports
- API reference documentation for all 12 top-level modules via mkdocstrings
- Test factories for cost, safety, regression, and trace replay models
- Example scripts for cost management, metrics trending, plugin creation, custom adapters, and dashboard usage
- Plugin system: loader, registry, base classes, and plugin manager
- Metric collection, aggregation, and trend analysis
- PostgreSQL storage backend with asyncpg
- Database migration system (V1: traces/results, V2: metrics)
- CLI commands for metrics (`metrics list`, `metrics summary`)
- Integration test suite covering all cross-module pipelines
- Full project documentation with MkDocs Material
- Docker support with multi-stage build
- CONTRIBUTING.md and LICENSE

### Changed

- Consolidated CI into single workflow with test matrix, artifact uploads, and JUnit reporting
- Expanded `agentprobe.yaml.example` and `init` template to cover all 13 config sections
- Version bumped from 0.1.0 to 0.4.0 to reflect Phases 1-4 feature completeness

## [0.3.0] - 2025-03-15

### Added

- Plugin system with `PluginBase` abstract class and four typed subclasses
- `PluginRegistry` for managing plugin lifecycle
- `PluginLoader` with entry point and file-based discovery
- `PluginManager` for dispatching lifecycle hooks with error isolation
- `MetricCollector` for stateless metric extraction from traces and results
- `MetricAggregator` using stdlib `statistics` for summary computation
- `MetricTrend` for trend analysis across multiple runs
- Six built-in metric definitions (latency, token count, cost, score, tool calls, error rate)
- PostgreSQL storage backend with connection pooling via asyncpg
- Migration system for schema versioning
- SQLite extended with metrics table
- `metrics list` and `metrics summary` CLI commands
- Integration tests for plugin, metrics, and storage pipelines

## [0.2.0] - 2025-02-15

### Added

- `ChaosProxy` for fault injection into agent tool calls
- `SnapshotManager` for golden-file comparison testing
- `BudgetEnforcer` for per-test and per-suite cost limits
- `StatisticalEvaluator` for multi-run score aggregation
- `TraceComparisonEvaluator` for structural trace diffing
- `ConversationRunner` for multi-turn dialogue testing
- `RegressionDetector` and `BaselineManager` for behavioral diff
- `ReplayEngine` and `TimeTravel` for trace replay and inspection
- Six safety test suites: prompt injection, data leakage, jailbreak, role confusion, hallucination, tool abuse
- PII redaction scanner in `security/pii.py`
- Six reporting formats: terminal, HTML, JUnit XML, JSON, Markdown, CSV
- CLI commands: `baseline`, `snapshot`, `cost`, `safety`
- Configuration sections: `chaos`, `snapshot`, `budget`, `regression`

## [0.1.0] - 2025-01-15

### Added

- Core test framework: `TestRunner`, `TestCase`, `TestResult`, `TestRun` models
- `@scenario` decorator and test discovery system
- Assertion builder with fluent API (`expect`, `expect_tool_calls`)
- `TraceRecorder` with async context manager for capturing agent execution
- `Trace`, `LLMCall`, `ToolCall` data models (frozen Pydantic)
- Configuration loading from `agentprobe.yaml` with `${ENV_VAR}` interpolation
- `CostCalculator` with YAML-based pricing data
- Rules-based, embedding, and judge evaluators
- SQLite storage backend with WAL mode
- Framework adapters: LangChain, CrewAI, AutoGen, MCP
- Click-based CLI with `init` and `test` commands
- Custom exception hierarchy
