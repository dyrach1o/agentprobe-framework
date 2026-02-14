# Configuration Reference

Full reference for `agentprobe.yaml` configuration options.

For a quick overview, see [Getting Started > Configuration](../getting-started/configuration.md).

## File Format

AgentProbe configuration is a YAML file with the following top-level keys:

```yaml
project_name: my-project
test_dir: tests
runner: { ... }
eval: { ... }
judge: { ... }
trace: { ... }
cost: { ... }
safety: { ... }
chaos: { ... }
snapshot: { ... }
budget: { ... }
regression: { ... }
metrics: { ... }
plugins: { ... }
reporting: { ... }
```

All sections are optional. Unknown keys cause validation errors (`extra="forbid"`).

## Environment Variable Interpolation

Use `${VAR_NAME}` to reference environment variables anywhere in the config:

```yaml
trace:
  database_path: ${AGENTPROBE_DB_PATH}
```

## Section Reference

### `project_name`
- **Type:** `str`
- **Default:** `"agentprobe"`
- Name of the project being tested.

### `test_dir`
- **Type:** `str`
- **Default:** `"tests"`
- Root directory containing test files.

### `runner`

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `parallel` | `bool` | `false` | | Run tests concurrently |
| `max_workers` | `int` | `4` | >= 1 | Max concurrent tests |
| `default_timeout` | `float` | `30.0` | > 0 | Timeout per test (seconds) |

### `eval`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_evaluators` | `list[str]` | `[]` | Evaluator names for all tests |

### `judge`

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `model` | `str` | `"claude-sonnet-4-5-20250929"` | | Judge model ID |
| `provider` | `str` | `"anthropic"` | | API provider |
| `temperature` | `float` | `0.0` | 0.0--2.0 | Sampling temperature |
| `max_tokens` | `int` | `1024` | >= 1 | Max response tokens |

### `trace`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable trace recording |
| `storage_backend` | `str` | `"sqlite"` | `sqlite` or `postgresql` |
| `database_path` | `str` | `".agentprobe/traces.db"` | DB path or DSN |

### `cost`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable cost tracking |
| `budget_limit_usd` | `float \| null` | `null` | Max cost per run |
| `pricing_dir` | `str \| null` | `null` | Custom pricing YAML dir |

### `safety`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `false` | Enable safety testing |
| `suites` | `list[str]` | `[]` | Suite names to run |

### `chaos`

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `enabled` | `bool` | `false` | | Enable chaos testing |
| `seed` | `int` | `42` | | Random seed |
| `default_probability` | `float` | `0.5` | 0.0--1.0 | Fault probability |

### `snapshot`

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `enabled` | `bool` | `false` | | Enable snapshots |
| `snapshot_dir` | `str` | `".agentprobe/snapshots"` | | Snapshot directory |
| `update_on_first_run` | `bool` | `true` | | Auto-create on first run |
| `threshold` | `float` | `0.8` | 0.0--1.0 | Similarity threshold |

### `budget`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `test_budget_usd` | `float \| null` | `null` | Max cost per test |
| `suite_budget_usd` | `float \| null` | `null` | Max cost per suite |

### `regression`

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `enabled` | `bool` | `false` | | Enable regression detection |
| `baseline_dir` | `str` | `".agentprobe/baselines"` | | Baseline directory |
| `threshold` | `float` | `0.05` | 0.0--1.0 | Score delta threshold |

### `metrics`

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `enabled` | `bool` | `true` | | Enable metric collection |
| `builtin_metrics` | `bool` | `true` | | Collect built-in metrics |
| `trend_window` | `int` | `10` | >= 2 | Runs for trend analysis |

### `plugins`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable plugin system |
| `directories` | `list[str]` | `[]` | Additional plugin dirs |
| `entry_point_group` | `str` | `"agentprobe.plugins"` | Entry point group |

### `reporting`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `formats` | `list[str]` | `["terminal"]` | Output format names |
| `output_dir` | `str` | `"agentprobe-report"` | Report output directory |

**Available formats:** `terminal`, `json`, `junit`, `html`, `markdown`, `csv`
