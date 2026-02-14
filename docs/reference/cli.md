# CLI Reference

Complete reference for all AgentProbe command-line commands.

## Global Options

```bash
agentprobe --version    # Show version
agentprobe --help       # Show help
```

---

## `agentprobe init`

Initialize a new AgentProbe configuration file.

```bash
agentprobe init [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `agentprobe.yaml` | Output file path |

**Example:**

```bash
agentprobe init
agentprobe init -o config/agentprobe.yaml
```

---

## `agentprobe test`

Discover and run agent test scenarios.

```bash
agentprobe test [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | Auto-detect | Path to config file |
| `--test-dir` | `-d` | From config | Directory containing test files |
| `--pattern` | `-p` | `test_*.py` | Glob pattern for test files |
| `--parallel` | | | Run tests in parallel |
| `--sequential` | | | Run tests sequentially |

**Examples:**

```bash
agentprobe test
agentprobe test -d tests/agent_tests/
agentprobe test -p "check_*.py"
agentprobe test --parallel
agentprobe test -c custom-config.yaml -d tests/ --parallel
```

---

## `agentprobe trace`

Inspect and manage execution traces.

### `agentprobe trace list`

List recorded traces.

```bash
agentprobe trace list [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | Auto-detect | Path to config file |
| `--agent` | `-a` | All agents | Filter by agent name |
| `--limit` | `-n` | `20` | Maximum traces to show |

**Examples:**

```bash
agentprobe trace list
agentprobe trace list -a my-agent -n 50
```

### `agentprobe trace show`

Show details for a specific trace.

```bash
agentprobe trace show TRACE_ID [OPTIONS]
```

| Argument | Description |
|----------|-------------|
| `TRACE_ID` | The trace identifier |

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | Auto-detect | Path to config file |

**Example:**

```bash
agentprobe trace show abc12345
```

**Output includes:** trace ID, agent name, model, input/output text, token counts, latency, tags, timestamps, and tool call details.

---

## `agentprobe safety`

Run safety scans against agents.

### `agentprobe safety scan`

Run safety test suites.

```bash
agentprobe safety scan [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--suite` | `-s` | All configured | Suite names (repeatable) |
| `--severity` | | All | Filter by severity level |

**Examples:**

```bash
agentprobe safety scan
agentprobe safety scan -s prompt-injection -s data-leakage
```

### `agentprobe safety list`

List available safety test suites.

```bash
agentprobe safety list
```

---

## `agentprobe cost`

Track and manage execution costs.

### `agentprobe cost report`

Generate a cost report.

```bash
agentprobe cost report [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--agent` | `-a` | All | Filter by agent name |
| `--format` | `-f` | `terminal` | Output format |

### `agentprobe cost budget`

Check budget status.

```bash
agentprobe cost budget [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--max-cost` | | From config | Maximum cost in USD |
| `--max-tokens` | | None | Maximum token count |

---

## `agentprobe baseline`

Manage regression testing baselines.

### `agentprobe baseline list`

List all saved baselines.

```bash
agentprobe baseline list [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dir` | `-d` | `.agentprobe/baselines` | Baselines directory |

### `agentprobe baseline save`

Create a new baseline from the latest test run.

```bash
agentprobe baseline save NAME [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dir` | `-d` | `.agentprobe/baselines` | Baselines directory |

### `agentprobe baseline delete`

Delete a saved baseline.

```bash
agentprobe baseline delete NAME [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dir` | `-d` | `.agentprobe/baselines` | Baselines directory |

---

## `agentprobe snapshot`

Manage trace snapshots for golden-file testing.

### `agentprobe snapshot list`

List all saved snapshots.

```bash
agentprobe snapshot list [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dir` | `-d` | `.agentprobe/snapshots` | Snapshots directory |

### `agentprobe snapshot delete`

Delete a saved snapshot.

```bash
agentprobe snapshot delete NAME [OPTIONS]
```

### `agentprobe snapshot diff`

Show diff information for a snapshot.

```bash
agentprobe snapshot diff NAME [OPTIONS]
```

---

## `agentprobe metrics`

View metric data and summaries.

### `agentprobe metrics list`

List available metrics.

```bash
agentprobe metrics list
```

### `agentprobe metrics summary`

Show metric summary statistics.

```bash
agentprobe metrics summary [OPTIONS]
```
