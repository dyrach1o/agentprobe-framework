"""SQLite storage backend for traces and test results.

Uses Python's stdlib sqlite3 with ``run_in_executor`` for async
wrapping. Enables WAL mode for concurrent access.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from collections.abc import Callable, Sequence
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import TypeVar

from agentprobe.core.exceptions import StorageError
from agentprobe.core.models import MetricValue, TestResult, Trace

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    model TEXT,
    input_text TEXT,
    output_text TEXT,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_latency_ms INTEGER DEFAULT 0,
    tags TEXT,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_traces_agent_name ON traces(agent_name);
CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at);

CREATE TABLE IF NOT EXISTS test_results (
    result_id TEXT PRIMARY KEY,
    test_name TEXT NOT NULL,
    status TEXT NOT NULL,
    score REAL DEFAULT 0.0,
    duration_ms INTEGER DEFAULT 0,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_results_test_name ON test_results(test_name);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON test_results(created_at);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    tags TEXT,
    metadata TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
"""


class SQLiteStorage:
    """SQLite-based storage for traces and test results.

    Uses WAL mode for concurrent read access and stores full
    serialized models in a ``data`` TEXT column for lossless
    round-tripping.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str | Path = ".agentprobe/traces.db") -> None:
        """Initialize the SQLite storage.

        Args:
            db_path: Path to the database file. Parent directories
                will be created if they don't exist.
        """
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create the database connection."""
        if self._conn is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    async def _run(self, func: Callable[[], _T]) -> _T:
        """Run a sync function in the default executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)

    async def setup(self) -> None:
        """Create tables and indexes if they don't exist."""
        try:
            await self._run(partial(self._setup_sync))
            logger.info("SQLite storage initialized at %s", self._db_path)
        except Exception as exc:
            raise StorageError(f"Failed to initialize SQLite: {exc}") from exc

    def _setup_sync(self) -> None:
        conn = self._get_conn()
        conn.executescript(_SCHEMA)
        conn.commit()

    async def save_trace(self, trace: Trace) -> None:
        """Persist a trace to SQLite.

        Args:
            trace: The trace to save.
        """
        try:
            await self._run(partial(self._save_trace_sync, trace))
        except Exception as exc:
            raise StorageError(f"Failed to save trace: {exc}") from exc

    def _save_trace_sync(self, trace: Trace) -> None:
        conn = self._get_conn()
        data = trace.model_dump_json()
        tags_json = json.dumps(list(trace.tags))
        conn.execute(
            """INSERT OR REPLACE INTO traces
               (trace_id, agent_name, model, input_text, output_text,
                total_input_tokens, total_output_tokens, total_latency_ms,
                tags, data, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace.trace_id,
                trace.agent_name,
                trace.model,
                trace.input_text,
                trace.output_text,
                trace.total_input_tokens,
                trace.total_output_tokens,
                trace.total_latency_ms,
                tags_json,
                data,
                trace.created_at.isoformat(),
            ),
        )
        conn.commit()

    async def load_trace(self, trace_id: str) -> Trace | None:
        """Load a trace by ID.

        Args:
            trace_id: The unique identifier.

        Returns:
            The trace if found, otherwise None.
        """
        try:
            result = await self._run(partial(self._load_trace_sync, trace_id))
            return result
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Failed to load trace: {exc}") from exc

    def _load_trace_sync(self, trace_id: str) -> Trace | None:
        conn = self._get_conn()
        row = conn.execute("SELECT data FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
        if row is None:
            return None
        return Trace.model_validate_json(row["data"])

    async def list_traces(
        self,
        agent_name: str | None = None,
        limit: int = 100,
    ) -> Sequence[Trace]:
        """List traces with optional filtering.

        Args:
            agent_name: Filter by agent name.
            limit: Maximum results.

        Returns:
            A list of matching traces.
        """
        try:
            result = await self._run(partial(self._list_traces_sync, agent_name, limit))
            return result
        except Exception as exc:
            raise StorageError(f"Failed to list traces: {exc}") from exc

    def _list_traces_sync(self, agent_name: str | None, limit: int) -> list[Trace]:
        conn = self._get_conn()
        if agent_name:
            rows = conn.execute(
                "SELECT data FROM traces WHERE agent_name = ? ORDER BY created_at DESC LIMIT ?",
                (agent_name, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT data FROM traces ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Trace.model_validate_json(row["data"]) for row in rows]

    async def save_result(self, result: TestResult) -> None:
        """Persist a test result.

        Args:
            result: The test result to save.
        """
        try:
            await self._run(partial(self._save_result_sync, result))
        except Exception as exc:
            raise StorageError(f"Failed to save result: {exc}") from exc

    def _save_result_sync(self, result: TestResult) -> None:
        conn = self._get_conn()
        data = result.model_dump_json()
        conn.execute(
            """INSERT OR REPLACE INTO test_results
               (result_id, test_name, status, score, duration_ms, data, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                result.result_id,
                result.test_name,
                result.status.value,
                result.score,
                result.duration_ms,
                data,
                result.created_at.isoformat(),
            ),
        )
        conn.commit()

    async def load_results(
        self,
        test_name: str | None = None,
        limit: int = 100,
    ) -> Sequence[TestResult]:
        """Load test results with optional filtering.

        Args:
            test_name: Filter by test name.
            limit: Maximum results.

        Returns:
            A list of matching test results.
        """
        try:
            result = await self._run(partial(self._load_results_sync, test_name, limit))
            return result
        except Exception as exc:
            raise StorageError(f"Failed to load results: {exc}") from exc

    def _load_results_sync(self, test_name: str | None, limit: int) -> list[TestResult]:
        conn = self._get_conn()
        if test_name:
            rows = conn.execute(
                "SELECT data FROM test_results WHERE test_name = ? ORDER BY created_at DESC LIMIT ?",
                (test_name, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT data FROM test_results ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [TestResult.model_validate_json(row["data"]) for row in rows]

    async def load_result(self, result_id: str) -> TestResult | None:
        """Load a single test result by ID.

        Args:
            result_id: The unique identifier.

        Returns:
            The test result if found, otherwise None.
        """
        try:
            return await self._run(partial(self._load_result_sync, result_id))
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Failed to load result: {exc}") from exc

    def _load_result_sync(self, result_id: str) -> TestResult | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT data FROM test_results WHERE result_id = ?", (result_id,)
        ).fetchone()
        if row is None:
            return None
        return TestResult.model_validate_json(row["data"])

    async def save_metrics(self, metrics: Sequence[MetricValue]) -> None:
        """Persist a batch of metric values.

        Args:
            metrics: The metric values to save.
        """
        if not metrics:
            return
        try:
            await self._run(partial(self._save_metrics_sync, metrics))
        except Exception as exc:
            raise StorageError(f"Failed to save metrics: {exc}") from exc

    def _save_metrics_sync(self, metrics: Sequence[MetricValue]) -> None:
        conn = self._get_conn()
        for mv in metrics:
            tags_json = json.dumps(list(mv.tags))
            meta_json = json.dumps(mv.metadata)
            conn.execute(
                """INSERT INTO metrics (metric_name, value, tags, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (mv.metric_name, mv.value, tags_json, meta_json, mv.timestamp.isoformat()),
            )
        conn.commit()

    async def load_metrics(
        self,
        metric_name: str | None = None,
        limit: int = 1000,
    ) -> Sequence[MetricValue]:
        """Load metric values with optional filtering.

        Args:
            metric_name: Filter by metric name.
            limit: Maximum values to return.

        Returns:
            A list of matching metric values.
        """
        try:
            return await self._run(partial(self._load_metrics_sync, metric_name, limit))
        except Exception as exc:
            raise StorageError(f"Failed to load metrics: {exc}") from exc

    def _load_metrics_sync(self, metric_name: str | None, limit: int) -> list[MetricValue]:
        conn = self._get_conn()
        if metric_name:
            rows = conn.execute(
                "SELECT metric_name, value, tags, metadata, timestamp "
                "FROM metrics WHERE metric_name = ? ORDER BY timestamp DESC LIMIT ?",
                (metric_name, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT metric_name, value, tags, metadata, timestamp "
                "FROM metrics ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [
            MetricValue(
                metric_name=row["metric_name"],
                value=row["value"],
                tags=tuple(json.loads(row["tags"])) if row["tags"] else (),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
