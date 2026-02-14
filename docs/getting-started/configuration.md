# Configuration

AgentProbe is configured via `agentprobe.yaml` in your project root. Run `agentprobe init` to generate a starter config file.

## Config File Discovery

AgentProbe searches for configuration in this order:

1. Path passed via `--config` / `-c` CLI flag
2. `agentprobe.yaml` in the current directory
3. `agentprobe.yml` in the current directory
4. If no file is found, default values are used

## Environment Variable Interpolation

Use `${VAR_NAME}` syntax to reference environment variables:

```yaml
trace:
  database_path: ${AGENTPROBE_DB_PATH}
```

If the variable is not set, a warning is logged and the literal `${VAR_NAME}` string is kept.

## Full Configuration Reference

### Top-Level

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `project_name` | `string` | `"agentprobe"` | Name of the project being tested |
| `test_dir` | `string` | `"tests"` | Directory containing test files |

### `runner`

Controls test execution behavior.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `parallel` | `bool` | `false` | Run tests in parallel |
| `max_workers` | `int` | `4` | Maximum concurrent tests (min: 1) |
| `default_timeout` | `float` | `30.0` | Default test timeout in seconds |

### `eval`

Evaluator configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_evaluators` | `list[str]` | `[]` | Evaluator names applied to all tests |

### `judge`

Settings for the judge evaluator.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model` | `string` | `"claude-sonnet-4-5-20250929"` | Model to use for judging |
| `provider` | `string` | `"anthropic"` | API provider name |
| `temperature` | `float` | `0.0` | Sampling temperature (0.0--2.0) |
| `max_tokens` | `int` | `1024` | Maximum response tokens |

### `trace`

Trace recording and storage.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Whether to record traces |
| `storage_backend` | `string` | `"sqlite"` | Storage backend (`sqlite` or `postgresql`) |
| `database_path` | `string` | `".agentprobe/traces.db"` | Path to database file or DSN |

### `cost`

Cost tracking settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Whether to track costs |
| `budget_limit_usd` | `float\|null` | `null` | Maximum cost per run |
| `pricing_dir` | `string\|null` | `null` | Custom pricing YAML directory |

### `safety`

Safety testing configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `false` | Whether to run safety tests |
| `suites` | `list[str]` | `[]` | Safety suite names to run |

### `chaos`

Chaos fault injection configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `false` | Whether chaos testing is enabled |
| `seed` | `int` | `42` | Random seed for reproducibility |
| `default_probability` | `float` | `0.5` | Probability of injecting a fault (0.0--1.0) |

### `snapshot`

Snapshot (golden file) testing.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `false` | Whether snapshot testing is enabled |
| `snapshot_dir` | `string` | `".agentprobe/snapshots"` | Directory for snapshot files |
| `update_on_first_run` | `bool` | `true` | Create snapshots on first run |
| `threshold` | `float` | `0.8` | Similarity threshold (0.0--1.0) |

### `budget`

Per-test and per-suite cost budgets.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `test_budget_usd` | `float\|null` | `null` | Maximum cost per individual test |
| `suite_budget_usd` | `float\|null` | `null` | Maximum cost per test suite run |

### `regression`

Regression detection settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `false` | Whether regression detection is enabled |
| `baseline_dir` | `string` | `".agentprobe/baselines"` | Baseline file directory |
| `threshold` | `float` | `0.05` | Score delta threshold for flagging (0.0--1.0) |

### `metrics`

Metric collection and trending.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Whether metric collection is enabled |
| `builtin_metrics` | `bool` | `true` | Collect built-in metrics automatically |
| `trend_window` | `int` | `10` | Number of recent runs for trend analysis (min: 2) |

### `plugins`

Plugin system configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Whether the plugin system is enabled |
| `directories` | `list[str]` | `[]` | Additional plugin scan directories |
| `entry_point_group` | `string` | `"agentprobe.plugins"` | Entry point group name |

### `reporting`

Result reporting configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `formats` | `list[str]` | `["terminal"]` | Output format names |
| `output_dir` | `string` | `"agentprobe-report"` | Directory for report files |

Available formats: `terminal`, `json`, `junit`, `html`, `markdown`, `csv`

## Example Configuration

```yaml
project_name: my-agent-project
test_dir: tests/agent_tests

runner:
  parallel: true
  max_workers: 8
  default_timeout: 60.0

eval:
  default_evaluators:
    - rules

trace:
  enabled: true
  storage_backend: sqlite
  database_path: .agentprobe/traces.db

cost:
  enabled: true
  budget_limit_usd: 5.00

safety:
  enabled: true
  suites:
    - prompt-injection
    - data-exfiltration
    - jailbreak

regression:
  enabled: true
  threshold: 0.10

metrics:
  enabled: true
  trend_window: 20

reporting:
  formats:
    - terminal
    - junit
  output_dir: test-reports
```
