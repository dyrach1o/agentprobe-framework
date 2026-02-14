"""PostgreSQL storage backend for traces, test results, and metrics.

Uses asyncpg for async database access. The asyncpg dependency is lazy-loaded
so users without PostgreSQL are not affected.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

from agentprobe.core.exceptions import StorageError
from agentprobe.core.models import MetricValue, TestResult, Trace
from agentprobe.storage.migrations import SchemaMigration

logger = logging.getLogger(__name__)

_SCHEMA_VERSION_QUERY = "SELECT version FROM schema_version LIMIT 1"


class PostgreSQLStorage:
    """PostgreSQL-based storage for traces, results, and metrics.

    Uses asyncpg connection pool for concurrent access. Full model data
    is stored in a TEXT ``data`` column for lossless round-tripping,
    with extracted columns for indexing and filtering.

    Attributes:
        dsn: PostgreSQL connection string.
    """

    def __init__(
        self,
        dsn: str = "postgresql://localhost/agentprobe",
        min_pool_size: int = 2,
        max_pool_size: int = 10,
    ) -> None:
        """Initialize the PostgreSQL storage.

        Args:
            dsn: PostgreSQL connection string.
            min_pool_size: Minimum pool connections.
            max_pool_size: Maximum pool connections.
        """
        self._dsn = dsn
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._pool: Any = None
        self._migration = SchemaMigration()

    async def setup(self) -> None:  # pragma: no cover
        """Create the connection pool and run pending migrations.

        Raises:
            StorageError: If connection or migration fails.
        """
        try:
            import asyncpg  # type: ignore[import-not-found]  # noqa: PLC0415

            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=self._min_pool_size,
                max_size=self._max_pool_size,
            )
            await self._run_migrations()
            logger.info("PostgreSQL storage initialized: %s", self._dsn)
        except Exception as exc:
            raise StorageError(f"Failed to initialize PostgreSQL: {exc}") from exc

    async def _run_migrations(self) -> None:  # pragma: no cover
        """Check current version and apply pending migrations."""
        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(_SCHEMA_VERSION_QUERY)
                current = row["version"] if row else 0
            except Exception:
                current = 0

            async def _execute(sql: str) -> None:
                await conn.execute(sql)

            await self._migration.apply(current, _execute)

    async def save_trace(self, trace: Trace) -> None:
        """Persist a trace to PostgreSQL.

        Args:
            trace: The trace to save.

        Raises:
            StorageError: If the save operation fails.
        """
        try:
            data = trace.model_dump_json()
            tags_json = json.dumps(list(trace.tags))
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO traces
                       (trace_id, agent_name, model, input_text, output_text,
                        total_input_tokens, total_output_tokens, total_latency_ms,
                        tags, data, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                       ON CONFLICT (trace_id) DO UPDATE SET data = $10""",
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
                    trace.created_at,
                )
        except Exception as exc:
            raise StorageError(f"Failed to save trace: {exc}") from exc

    async def load_trace(self, trace_id: str) -> Trace | None:
        """Load a trace by ID.

        Args:
            trace_id: The unique identifier.

        Returns:
            The trace if found, otherwise None.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT data FROM traces WHERE trace_id = $1", trace_id)
                if row is None:
                    return None
                return Trace.model_validate_json(row["data"])
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Failed to load trace: {exc}") from exc

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
            async with self._pool.acquire() as conn:
                if agent_name:
                    rows = await conn.fetch(
                        "SELECT data FROM traces WHERE agent_name = $1 "
                        "ORDER BY created_at DESC LIMIT $2",
                        agent_name,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT data FROM traces ORDER BY created_at DESC LIMIT $1",
                        limit,
                    )
                return [Trace.model_validate_json(row["data"]) for row in rows]
        except Exception as exc:
            raise StorageError(f"Failed to list traces: {exc}") from exc

    async def save_result(self, result: TestResult) -> None:
        """Persist a test result.

        Args:
            result: The test result to save.

        Raises:
            StorageError: If the save operation fails.
        """
        try:
            data = result.model_dump_json()
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO test_results
                       (result_id, test_name, status, score, duration_ms, data, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)
                       ON CONFLICT (result_id) DO UPDATE SET data = $6""",
                    result.result_id,
                    result.test_name,
                    result.status.value,
                    result.score,
                    result.duration_ms,
                    data,
                    result.created_at,
                )
        except Exception as exc:
            raise StorageError(f"Failed to save result: {exc}") from exc

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
            async with self._pool.acquire() as conn:
                if test_name:
                    rows = await conn.fetch(
                        "SELECT data FROM test_results WHERE test_name = $1 "
                        "ORDER BY created_at DESC LIMIT $2",
                        test_name,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT data FROM test_results ORDER BY created_at DESC LIMIT $1",
                        limit,
                    )
                return [TestResult.model_validate_json(row["data"]) for row in rows]
        except Exception as exc:
            raise StorageError(f"Failed to load results: {exc}") from exc

    async def load_result(self, result_id: str) -> TestResult | None:
        """Load a single test result by ID.

        Args:
            result_id: The unique identifier.

        Returns:
            The test result if found, otherwise None.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT data FROM test_results WHERE result_id = $1", result_id
                )
                if row is None:
                    return None
                return TestResult.model_validate_json(row["data"])
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Failed to load result: {exc}") from exc

    async def save_metrics(self, metrics: Sequence[MetricValue]) -> None:
        """Persist a batch of metric values.

        Args:
            metrics: The metric values to save.

        Raises:
            StorageError: If the save operation fails.
        """
        if not metrics:
            return
        try:
            async with self._pool.acquire() as conn:
                for mv in metrics:
                    tags_json = json.dumps(list(mv.tags))
                    meta_json = json.dumps(mv.metadata)
                    await conn.execute(
                        """INSERT INTO metrics (metric_name, value, tags, metadata, timestamp)
                           VALUES ($1, $2, $3, $4, $5)""",
                        mv.metric_name,
                        mv.value,
                        tags_json,
                        meta_json,
                        mv.timestamp,
                    )
        except Exception as exc:
            raise StorageError(f"Failed to save metrics: {exc}") from exc

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
            A sequence of matching metric values.
        """
        try:
            async with self._pool.acquire() as conn:
                if metric_name:
                    rows = await conn.fetch(
                        "SELECT metric_name, value, tags, metadata, timestamp "
                        "FROM metrics WHERE metric_name = $1 "
                        "ORDER BY timestamp DESC LIMIT $2",
                        metric_name,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT metric_name, value, tags, metadata, timestamp "
                        "FROM metrics ORDER BY timestamp DESC LIMIT $1",
                        limit,
                    )
                return [
                    MetricValue(
                        metric_name=row["metric_name"],
                        value=row["value"],
                        tags=tuple(json.loads(row["tags"])) if row["tags"] else (),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        timestamp=row["timestamp"],
                    )
                    for row in rows
                ]
        except Exception as exc:
            raise StorageError(f"Failed to load metrics: {exc}") from exc

    async def close(self) -> None:  # pragma: no cover
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
