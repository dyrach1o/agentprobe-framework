"""Pytest plugin for AgentProbe: provides fixtures and markers.

Auto-registered via the ``pytest11`` entry point. Provides:

- ``agentprobe`` fixture (function-scoped): returns an ``AgentProbeContext``
  with ``invoke()``, ``evaluate()``, and ``calculate_cost()`` methods.
- ``agentprobe_config`` fixture (session-scoped): loads ``AgentProbeConfig``.
- ``agentprobe_storage`` fixture (session-scoped): manages ``SQLiteStorage``.
- ``--agentprobe-config``, ``--agentprobe-trace-dir``, ``--agentprobe-store-traces``
  command-line options.
- ``@pytest.mark.agentprobe`` marker for tagging tests.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest

from agentprobe.adapters.base import BaseAdapter
from agentprobe.core.config import AgentProbeConfig, load_config
from agentprobe.core.models import CostSummary, EvalResult, Trace
from agentprobe.cost.calculator import CostCalculator
from agentprobe.eval.base import BaseEvaluator
from agentprobe.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add AgentProbe-specific command-line options.

    Args:
        parser: The pytest argument parser.
    """
    group = parser.getgroup("agentprobe", "AgentProbe agent testing")
    group.addoption(
        "--agentprobe-config",
        default=None,
        help="Path to agentprobe.yaml config file.",
    )
    group.addoption(
        "--agentprobe-trace-dir",
        default=None,
        help="Directory to store trace database.",
    )
    group.addoption(
        "--agentprobe-store-traces",
        action="store_true",
        default=False,
        help="Persist traces to storage after each test.",
    )
    group.addoption(
        "--agentprobe-parallel",
        action="store_true",
        default=False,
        help="Enable parallel-safe mode (per-worker DB files). Enabled automatically under xdist.",
    )


def _is_xdist_worker(config: pytest.Config) -> bool:
    """Return True if running as a pytest-xdist worker process.

    Args:
        config: The pytest configuration object.
    """
    return hasattr(config, "workerinput")


def _get_xdist_worker_id(config: pytest.Config) -> str | None:
    """Return the xdist worker ID (e.g. 'gw0') or None if not a worker.

    Args:
        config: The pytest configuration object.
    """
    if _is_xdist_worker(config):
        return str(config.workerinput["workerid"])  # type: ignore[attr-defined]
    return None


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``agentprobe`` marker and detect xdist.

    Args:
        config: The pytest configuration object.
    """
    config.addinivalue_line(
        "markers",
        "agentprobe: marks tests using the AgentProbe framework",
    )

    # Detect xdist worker mode and stash the worker ID for fixture use.
    worker_id = _get_xdist_worker_id(config)
    if worker_id is not None:
        config._agentprobe_worker_id = worker_id  # type: ignore[attr-defined]
        logger.debug("AgentProbe: running as xdist worker %s", worker_id)


class AgentProbeContext:
    """Per-test context for invoking agents and running evaluations.

    Created fresh for each test function by the ``agentprobe`` fixture.

    Attributes:
        traces: All traces collected during this test.
        config: The AgentProbe configuration.
    """

    def __init__(
        self,
        config: AgentProbeConfig,
        storage: SQLiteStorage | None = None,
        store_traces: bool = False,
    ) -> None:
        """Initialize the context.

        Args:
            config: The AgentProbe configuration.
            storage: Optional storage backend for persisting traces.
            store_traces: Whether to persist traces after invocation.
        """
        self._config = config
        self._storage = storage
        self._store_traces = store_traces
        self._traces: list[Trace] = []
        self._calculator: CostCalculator | None = None

    @property
    def config(self) -> AgentProbeConfig:
        """Return the AgentProbe configuration."""
        return self._config

    @property
    def traces(self) -> list[Trace]:
        """Return all traces collected during this test."""
        return list(self._traces)

    @property
    def last_trace(self) -> Trace:
        """Return the most recent trace.

        Returns:
            The last collected trace.

        Raises:
            ValueError: If no traces have been collected.
        """
        if not self._traces:
            msg = "No traces collected yet — call invoke() first"
            raise ValueError(msg)
        return self._traces[-1]

    async def invoke(
        self,
        input_text: str,
        adapter: BaseAdapter,
        **kwargs: Any,
    ) -> Trace:
        """Invoke an adapter and collect the trace.

        Args:
            input_text: The input prompt to send.
            adapter: The agent adapter to invoke.
            **kwargs: Additional arguments passed to the adapter.

        Returns:
            The execution trace from the adapter.
        """
        trace = await adapter.invoke(input_text, **kwargs)
        self._traces.append(trace)

        if self._store_traces and self._storage is not None:
            await self._storage.save_trace(trace)

        return trace

    async def evaluate(
        self,
        trace: Trace,
        evaluator: BaseEvaluator,
        input_text: str = "",
        test_name: str = "agentprobe_eval",
    ) -> EvalResult:
        """Run an evaluator against a trace.

        Args:
            trace: The execution trace to evaluate.
            evaluator: The evaluator to run.
            input_text: Input text for the synthetic test case.
            test_name: Name for the synthetic test case.

        Returns:
            The evaluation result.
        """
        from agentprobe.core.models import TestCase

        test_case = TestCase(name=test_name, input_text=input_text)
        return await evaluator.evaluate(test_case, trace)

    def calculate_cost(self, trace: Trace) -> CostSummary:
        """Calculate the cost of a trace.

        Args:
            trace: The execution trace to price.

        Returns:
            A cost summary with per-model breakdown.
        """
        if self._calculator is None:
            self._calculator = CostCalculator()
        return self._calculator.calculate_trace_cost(trace)


@pytest.fixture(scope="session")
def agentprobe_config(request: pytest.FixtureRequest) -> AgentProbeConfig:
    """Load AgentProbe configuration (session-scoped).

    Reads from ``--agentprobe-config`` if provided, otherwise searches
    for ``agentprobe.yaml`` / ``agentprobe.yml`` or uses defaults.

    Args:
        request: The pytest fixture request.

    Returns:
        A validated AgentProbeConfig.
    """
    config_path = request.config.getoption("--agentprobe-config", default=None)
    return load_config(config_path)


def _resolve_db_path(config: pytest.Config, default_path: str) -> str:
    """Resolve the database path, appending worker ID for parallel safety.

    When running under pytest-xdist or with ``--agentprobe-parallel``,
    each worker gets its own database file to avoid SQLite write contention.

    Args:
        config: The pytest configuration object.
        default_path: The default database path from configuration.

    Returns:
        The resolved database path (potentially worker-specific).
    """
    trace_dir = config.getoption("--agentprobe-trace-dir", default=None)
    base_path = trace_dir + "/traces.db" if trace_dir else default_path

    # Determine if we need per-worker isolation.
    worker_id: str | None = getattr(config, "_agentprobe_worker_id", None)
    parallel_flag: bool = config.getoption("--agentprobe-parallel", default=False)

    if worker_id is not None or parallel_flag:
        suffix = worker_id or "main"
        p = Path(base_path)
        return str(p.with_stem(f"{p.stem}_{suffix}"))

    return base_path


@pytest.fixture(scope="session")
async def agentprobe_storage(
    agentprobe_config: AgentProbeConfig,
    request: pytest.FixtureRequest,
) -> AsyncGenerator[SQLiteStorage]:
    """Create and manage a SQLite storage instance (session-scoped).

    When running under pytest-xdist, each worker gets its own database
    file (e.g. ``traces_gw0.db``) to avoid SQLite write contention.

    Args:
        agentprobe_config: The loaded configuration.
        request: The pytest fixture request.

    Yields:
        An initialized SQLiteStorage instance.
    """
    db_path = _resolve_db_path(request.config, agentprobe_config.trace.database_path)

    storage = SQLiteStorage(db_path=db_path)
    await storage.setup()

    yield storage

    await storage.close()


@pytest.fixture
def agentprobe(
    agentprobe_config: AgentProbeConfig,
    request: pytest.FixtureRequest,
) -> AgentProbeContext:
    """Provide a fresh AgentProbeContext for each test (function-scoped).

    Args:
        agentprobe_config: The session-scoped configuration.
        request: The pytest fixture request.

    Returns:
        An AgentProbeContext for invoking agents and running evaluations.
    """
    store_traces = request.config.getoption("--agentprobe-store-traces", default=False)

    storage: SQLiteStorage | None = None
    if store_traces:
        storage = request.getfixturevalue("agentprobe_storage")

    return AgentProbeContext(
        config=agentprobe_config,
        storage=storage,
        store_traces=bool(store_traces),
    )
