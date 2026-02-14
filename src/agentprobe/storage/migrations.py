"""Schema migrations for storage backends.

Provides a linear version-based migration system for database schemas.
Each migration is a pair of (version, SQL statements) applied in order.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
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
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_traces_agent_name ON traces(agent_name);
        CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at);

        CREATE TABLE IF NOT EXISTS test_results (
            result_id TEXT PRIMARY KEY,
            test_name TEXT NOT NULL,
            status TEXT NOT NULL,
            score DOUBLE PRECISION DEFAULT 0.0,
            duration_ms INTEGER DEFAULT 0,
            data TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_results_test_name ON test_results(test_name);
        CREATE INDEX IF NOT EXISTS idx_results_created_at ON test_results(created_at);

        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        );

        INSERT INTO schema_version (version) VALUES (1);
        """,
    ),
    (
        2,
        """
        CREATE TABLE IF NOT EXISTS metrics (
            id SERIAL PRIMARY KEY,
            metric_name TEXT NOT NULL,
            value DOUBLE PRECISION NOT NULL,
            tags TEXT,
            metadata TEXT,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);

        UPDATE schema_version SET version = 2;
        """,
    ),
]


class SchemaMigration:
    """Manages linear schema migrations for PostgreSQL.

    Tracks the current schema version and applies any pending
    migrations in order.
    """

    def __init__(self) -> None:
        self._migrations = list(_MIGRATIONS)

    @property
    def latest_version(self) -> int:
        """Return the latest available schema version."""
        if not self._migrations:
            return 0
        return self._migrations[-1][0]

    def get_pending(self, current_version: int) -> list[tuple[int, str]]:
        """Get migrations that haven't been applied yet.

        Args:
            current_version: The currently applied schema version.

        Returns:
            List of (version, sql) tuples to apply.
        """
        return [(v, sql) for v, sql in self._migrations if v > current_version]

    async def apply(
        self,
        current_version: int,
        execute_fn: Any,
    ) -> int:
        """Apply pending migrations using the provided execution function.

        Args:
            current_version: The currently applied schema version.
            execute_fn: Async callable that executes SQL strings.

        Returns:
            The new schema version after applying migrations.
        """
        pending = self.get_pending(current_version)
        if not pending:
            logger.info("Schema is up to date at version %d", current_version)
            return current_version

        for version, sql in pending:
            logger.info("Applying migration V%d", version)
            await execute_fn(sql)

        new_version = pending[-1][0]
        logger.info("Schema migrated to version %d", new_version)
        return new_version
