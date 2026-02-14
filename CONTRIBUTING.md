# Contributing to AgentProbe

Thank you for your interest in contributing to AgentProbe! This document covers how to set up your development environment, our coding standards, and the contribution workflow.

## Development Setup

### Prerequisites

- Python 3.11 or later
- Git

### Getting Started

```bash
# Clone the repository
git clone https://github.com/dyrach1o/agentprobe-framework.git
cd agentprobe-framework

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
make dev
# or manually: pip install -e ".[dev,test,docs]"

# Verify setup
make check
```

## Coding Standards

### Python

- **Python 3.11+** required
- **ruff** for linting and formatting --- run `make lint` and `make format`
- **mypy strict mode** for type checking --- run `make type-check`
- **100% type annotations** on all public and private functions
- **Google-style docstrings** on all public classes, methods, and functions
- Line length: 100 characters

### Naming Conventions

| Scope | Convention | Example |
|-------|-----------|---------|
| Modules | `snake_case` | `trace_compare.py` |
| Classes | `PascalCase` | `TraceRecorder` |
| Functions | `snake_case` | `calculate_cost()` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_TIMEOUT_SECONDS` |
| Variables | `snake_case` | `total_cost` |

### Import Order

Enforced by ruff (isort):

1. Standard library
2. Third-party packages
3. First-party (`agentprobe`)

## Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Fast tests (skip slow and API tests)
make test-fast

# Specific test file
pytest tests/unit/core/test_runner.py -v
```

### Writing Tests

- Test files go in `tests/unit/` mirroring the `src/` structure
- Use pytest fixtures from `tests/fixtures/` for test data
- Use factory functions (`make_trace`, `make_eval_result`, etc.) for model instances
- Follow the pattern: `test_{method}_{scenario}_{expected_outcome}`
- Async tests use `@pytest.mark.asyncio`
- Minimum **90% coverage** for new code

### Test Structure

```python
class TestMyClass:
    """Tests for MyClass."""

    def test_method_with_valid_input_returns_expected(self) -> None:
        # Arrange
        obj = MyClass()

        # Act
        result = obj.method(valid_input)

        # Assert
        assert result == expected

    def test_method_with_invalid_input_raises_error(self) -> None:
        obj = MyClass()

        with pytest.raises(ValueError, match="specific message"):
            obj.method(invalid_input)
```

## Git Workflow

### Branches

- `main` --- production-ready, protected
- `develop` --- integration branch
- `feature/TEAM-X.YY.ZZ-description` --- feature branches from `develop`
- `bugfix/TEAM-X.YY.ZZ-description` --- bug fixes
- `hotfix/description` --- urgent fixes from `main`

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**Scopes:** `core`, `eval`, `safety`, `adapters`, `cli`, `trace`, `cost`, `storage`, `reporting`, `plugins`, `docs`, `infra`

**Examples:**

```
feat(core): implement test runner with parallel execution
fix(eval): correct cosine similarity for zero vectors
docs(cli): add usage examples for trace commands
test(safety): add prompt injection detection tests
```

### Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes following the coding standards
3. Ensure all checks pass: `make check`
4. Push and open a PR against `develop`
5. Fill out the PR template
6. Address review feedback

### PR Checklist

- [ ] Code is fully type-annotated (mypy strict passes)
- [ ] Docstrings added for all public APIs
- [ ] Tests pass with >= 90% coverage for new code
- [ ] No linting errors (`ruff check`)
- [ ] Changelog entry added (if user-facing)
- [ ] Documentation updated (if applicable)

## Project Layout

```
src/agentprobe/
├── core/       # Test runner, discovery, assertions, config
├── eval/       # Evaluators
├── trace/      # Recording and replay
├── cost/       # Cost tracking
├── safety/     # Safety scanning
├── regression/ # Regression detection
├── adapters/   # Framework adapters
├── metrics/    # Metric collection
├── storage/    # Storage backends
├── reporting/  # Output formatters
├── plugins/    # Plugin system
└── cli/        # CLI commands
```

## Getting Help

- Open a [GitHub Issue](https://github.com/dyrach1o/agentprobe-framework/issues) for bugs or feature requests
- Check existing issues before creating new ones
- Include reproduction steps for bug reports
