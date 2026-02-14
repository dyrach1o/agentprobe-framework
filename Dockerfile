# ── Stage 1: Builder ──
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /build/dist

# ── Stage 2: Runtime ──
FROM python:3.11-slim AS runtime

# Create non-root user
RUN groupadd --gid 1000 agentprobe \
    && useradd --uid 1000 --gid 1000 --create-home agentprobe

WORKDIR /app

# Install the wheel from builder stage
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm -rf /tmp/*.whl

# Switch to non-root user
USER agentprobe

# Default working directory for user projects
WORKDIR /project

ENTRYPOINT ["agentprobe"]
CMD ["--help"]
