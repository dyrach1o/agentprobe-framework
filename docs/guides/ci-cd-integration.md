# CI/CD Integration

AgentProbe integrates into CI/CD pipelines with JUnit XML output, configurable exit codes, and cost controls.

## GitHub Actions

### Basic Setup

```yaml
# .github/workflows/agent-tests.yml
name: Agent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install agentprobe-framework

      - name: Run agent tests
        run: agentprobe test -d tests/
```

### With JUnit Output

Generate JUnit XML reports for CI integration:

```yaml
reporting:
  formats:
    - terminal
    - junit
  output_dir: test-reports
```

### Upload Test Results

```yaml
      - name: Run tests
        run: agentprobe test -d tests/

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-reports/
```

## Cost Controls in CI

Set budget limits to prevent expensive tests from running unchecked:

```yaml
cost:
  enabled: true
  budget_limit_usd: 5.00

budget:
  suite_budget_usd: 5.00
```

## Regression Checks in CI

Compare test results against a baseline on every PR:

```yaml
      - name: Run tests and check regressions
        run: |
          agentprobe test -d tests/
          agentprobe baseline compare latest
```

## Safety Scans in CI

Run safety suites as a required check:

```yaml
      - name: Safety scan
        run: agentprobe safety scan -s prompt-injection -s data-leakage
```

## Multiple Output Formats

Generate several report formats in a single run:

```yaml
reporting:
  formats:
    - terminal
    - junit
    - json
    - html
  output_dir: test-reports
```

## Environment Variables

Store API keys as CI secrets and reference them in config:

```yaml
      - name: Run tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: agentprobe test -d tests/
```

```yaml
# agentprobe.yaml
trace:
  database_path: ${AGENTPROBE_DB_PATH}
```
