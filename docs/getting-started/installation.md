# Installation

## Requirements

- Python 3.11 or later
- pip (included with Python)

## Install from PyPI

```bash
pip install agentprobe-framework
```

## Optional Dependencies

AgentProbe has several optional dependency groups for extended functionality:

### PostgreSQL Storage

For team environments that need concurrent access and JSONB queries:

```bash
pip install agentprobe-framework[postgres]
```

Requires a running PostgreSQL 16+ instance. Configure via `agentprobe.yaml`:

```yaml
trace:
  storage_backend: postgresql
  database_path: ${AGENTPROBE_PG_DSN}
```

### Embedding-Based Evaluation

For semantic similarity scoring using embedding vectors:

```bash
pip install agentprobe-framework[eval]
```

Installs numpy for vector math operations.

### Dashboard

For the web-based dashboard with real-time results:

```bash
pip install agentprobe-framework[dashboard]
```

Installs FastAPI and Uvicorn.

### All Optional Dependencies

```bash
pip install agentprobe-framework[postgres,eval,dashboard]
```

## Install from Source

For development or to get the latest changes:

```bash
git clone https://github.com/dyrach1o/agentprobe-framework.git
cd agentprobe-framework

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install with all development dependencies
pip install -e ".[dev,test,docs]"
```

## Verify Installation

```bash
# Check version
agentprobe --version

# View help
agentprobe --help

# Initialize a project
agentprobe init
```

## Development Setup

If you plan to contribute, install the full development environment:

```bash
pip install -e ".[dev,test,docs]"

# Run all checks
make check

# This runs:
#   ruff check src/ tests/    (linting)
#   mypy src/agentprobe/      (type checking)
#   pytest tests/unit/        (unit tests)
```

See [CONTRIBUTING.md](https://github.com/dyrach1o/agentprobe-framework/blob/main/CONTRIBUTING.md) for the full development guide.
