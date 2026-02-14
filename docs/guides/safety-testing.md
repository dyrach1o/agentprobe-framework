# Safety Testing

AgentProbe includes built-in safety test suites that probe agents for common vulnerabilities.

## Overview

The safety scanner runs a series of adversarial test cases against your agent and reports which attacks succeeded. This helps identify vulnerabilities before deployment.

## Built-in Safety Suites

| Suite | Description |
|-------|-------------|
| `prompt-injection` | Tests for prompt injection attacks that attempt to override agent instructions |
| `data-leakage` | Tests for data exfiltration attempts that try to extract system prompts or internal data |
| `jailbreak` | Tests for jailbreak attempts that try to bypass safety guardrails |
| `role-confusion` | Tests for role confusion attacks that attempt to make the agent assume a different identity |
| `hallucination` | Tests for hallucination patterns where the agent fabricates information |
| `tool-abuse` | Tests for tool abuse scenarios where the agent misuses available tools |

## Using the CLI

### Run All Configured Suites

```bash
agentprobe safety scan
```

### Run Specific Suites

```bash
agentprobe safety scan -s prompt-injection -s data-leakage
```

### List Available Suites

```bash
agentprobe safety list
```

## Configuration

Enable safety scanning in `agentprobe.yaml`:

```yaml
safety:
  enabled: true
  suites:
    - prompt-injection
    - data-leakage
    - jailbreak
    - role-confusion
    - hallucination
    - tool-abuse
```

## Using the Python API

```python
from agentprobe.safety.scanner import SafetyScanner

# Create scanner from config
scanner = SafetyScanner.from_config([
    "prompt-injection",
    "data-leakage",
    "jailbreak",
])

# Run scan
result = await scanner.scan(adapter)

print(f"Total tests: {result.total_tests}")
print(f"Passed: {result.total_passed}")
print(f"Failed: {result.total_failed}")

for suite_result in result.suite_results:
    print(f"  {suite_result.suite_name}: {suite_result.passed}/{suite_result.total_tests}")
```

## Scan Results

The `SafetyScanResult` contains aggregate results:

| Field | Type | Description |
|-------|------|-------------|
| `total_suites` | `int` | Number of suites run |
| `total_tests` | `int` | Total tests across all suites |
| `total_passed` | `int` | Tests where no vulnerability was found |
| `total_failed` | `int` | Tests where a vulnerability was detected |
| `suite_results` | `tuple[SafetySuiteResult, ...]` | Per-suite breakdown |

## Custom Safety Suites

Register a custom suite by subclassing `SafetySuite`:

```python
from agentprobe.safety.scanner import SafetySuite, SafetySuiteResult, register_suite

@register_suite
class CustomSafetySuite(SafetySuite):
    @property
    def name(self) -> str:
        return "custom-safety"

    async def run(self, adapter) -> SafetySuiteResult:
        results = []
        # ... test logic ...
        return SafetySuiteResult(
            suite_name=self.name,
            total_tests=len(results),
            passed=sum(1 for r in results if r["passed"]),
            failed=sum(1 for r in results if not r["passed"]),
            results=tuple(results),
        )
```

## Best Practices

1. **Run safety scans regularly** as part of CI/CD
2. **Test all suites** --- different suites catch different vulnerability classes
3. **Review failed tests** carefully to understand attack vectors
4. **Add custom suites** for domain-specific safety concerns
5. **Track safety metrics** over time to catch regressions
