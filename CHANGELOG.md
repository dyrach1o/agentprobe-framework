# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-14

### Fixed
- CI: install dashboard and eval dependencies in test/type-check jobs
- CLI: resolve `version_option` package name to `agentprobe-framework`
- CI: separate local vs CI coverage thresholds (90% local, 70% CI without API keys)
- Adapters: add mypy type ignores for LangChain callback handler

### Changed
- Reformatted 8 source files to match latest ruff style

## [1.0.0] - 2026-02-14

### Added
- **pytest plugin** — `agentprobe` fixture auto-discovered via entry point
- **Assert helpers** — `assert_trace()`, `assert_score()`, `assert_cost()` for fluent test assertions
- **Core test runner** with scenario discovery, parallel execution, and timeout support
- **Trace recording** — structured capture of LLM calls, tool invocations, token usage, and timing
- **Trace replay and diff** — replay recorded traces with mock overrides, structural comparison
- **Evaluators** — rule-based, embedding similarity, statistical, and trace comparison evaluators
- **Cost tracking** — built-in pricing for Anthropic, OpenAI, Google, Mistral, and Cohere models
- **Budget enforcement** — per-test and per-suite cost limits with utilization reporting
- **Safety scanning** — 6 built-in suites: prompt injection, data leakage, jailbreak, role confusion, hallucination, tool abuse
- **Regression detection** — save baselines, detect score degradation with configurable thresholds
- **Framework adapters** — LangChain, CrewAI, AutoGen, MCP
- **Storage backends** — SQLite (default) and PostgreSQL with asyncpg
- **Reporting** — terminal, HTML, JUnit XML, JSON, Markdown, CSV output formats
- **Plugin system** — loader, registry, lifecycle hooks for extensibility
- **Security** — PII redaction, field encryption, structured audit logging
- **Dashboard** — FastAPI REST API for trace and result inspection
- **CLI** — `agentprobe init`, `test`, `trace`, `safety`, `cost`, `baseline`, `snapshot`, `metrics`, `dashboard`
- **Metrics** — collection, aggregation, and trending for latency, tokens, cost, and scores
- **Documentation** — MkDocs Material site with guides and API reference

[1.0.1]: https://github.com/dyrach1o/agentprobe-framework/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/dyrach1o/agentprobe-framework/releases/tag/v1.0.0
