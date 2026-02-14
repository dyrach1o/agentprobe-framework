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

## Complete GitHub Actions Example

Use this drop-in workflow to run AgentProbe tests in your CI environment. This example includes caching, secret management, coverage reporting, and cost budget enforcement.

```yaml
# .github/workflows/agent-tests.yml
name: Agent Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip' # Enable pip caching

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install agentprobe-framework pytest pytest-cov

      - name: Run AgentProbe tests
        env:
          # API Keys stored as repository secrets
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          # Path for traces database
          AGENTPROBE_DB_PATH: traces.db
        run: |
          pytest tests/ \
            --agentprobe-store-traces \
            --cov=src \
            --cov-report=xml \
            --junitxml=test-results.xml

      - name: Verify budget
        run: agentprobe cost budget --max-cost 5.00

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agentprobe-results
          path: |
            test-results.xml
            coverage.xml
            traces.db
```

## Secret Management

Store your model provider API keys (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) as **Repository Secrets** in GitHub:

1. Go to your repository **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**.
3. Add your keys and reference them in the workflow using `${{ secrets.YOUR_SECRET_NAME }}`.

## Environment Variables

AgentProbe can read configuration from environment variables, which is ideal for CI:

```yaml
      - name: Run tests
        env:
          # Required for model providers
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          # Customize AgentProbe behavior
          AGENTPROBE_LOG_LEVEL: DEBUG
          AGENTPROBE_DB_PATH: ${AGENTPROBE_DB_PATH}
        run: agentprobe test -d tests/
```

```yaml
# agentprobe.yaml
trace:
  database_path: ${AGENTPROBE_DB_PATH}
```
