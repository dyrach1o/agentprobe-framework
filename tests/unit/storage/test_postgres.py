"""Tests for PostgreSQL storage backend (all asyncpg mocked)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from agentprobe.core.exceptions import StorageError
from agentprobe.storage.postgres import PostgreSQLStorage
from tests.fixtures.results import make_test_result
from tests.fixtures.traces import make_metric_value, make_trace


class _MockConnection:
    """Mock asyncpg connection."""

    def __init__(self) -> None:
        self.execute = AsyncMock()
        self.fetchrow = AsyncMock(return_value=None)
        self.fetch = AsyncMock(return_value=[])

    async def __aenter__(self) -> _MockConnection:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


class _MockPool:
    """Mock asyncpg connection pool."""

    def __init__(self) -> None:
        self.conn = _MockConnection()
        self.close = AsyncMock()

    def acquire(self) -> _MockConnection:
        return self.conn


def _make_storage_with_pool() -> tuple[PostgreSQLStorage, _MockPool]:
    """Create a PostgreSQLStorage with a mock pool."""
    storage = PostgreSQLStorage(dsn="postgresql://test/db")
    pool = _MockPool()
    storage._pool = pool
    return storage, pool


class TestPostgreSQLStorageTraces:
    """Test trace operations."""

    @pytest.mark.asyncio
    async def test_save_trace(self) -> None:
        storage, pool = _make_storage_with_pool()
        trace = make_trace()
        await storage.save_trace(trace)
        pool.conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_trace_found(self) -> None:
        storage, pool = _make_storage_with_pool()
        trace = make_trace(trace_id="abc-123")
        pool.conn.fetchrow.return_value = {"data": trace.model_dump_json()}

        loaded = await storage.load_trace("abc-123")
        assert loaded is not None
        assert loaded.trace_id == "abc-123"

    @pytest.mark.asyncio
    async def test_load_trace_not_found(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.fetchrow.return_value = None

        loaded = await storage.load_trace("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_traces_all(self) -> None:
        storage, pool = _make_storage_with_pool()
        trace = make_trace()
        pool.conn.fetch.return_value = [{"data": trace.model_dump_json()}]

        traces = await storage.list_traces()
        assert len(traces) == 1

    @pytest.mark.asyncio
    async def test_list_traces_by_agent(self) -> None:
        storage, pool = _make_storage_with_pool()
        trace = make_trace(agent_name="support")
        pool.conn.fetch.return_value = [{"data": trace.model_dump_json()}]

        traces = await storage.list_traces(agent_name="support")
        assert len(traces) == 1
        assert traces[0].agent_name == "support"

    @pytest.mark.asyncio
    async def test_save_trace_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.execute.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to save trace"):
            await storage.save_trace(make_trace())

    @pytest.mark.asyncio
    async def test_load_trace_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.fetchrow.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to load trace"):
            await storage.load_trace("abc")


class TestPostgreSQLStorageResults:
    """Test result operations."""

    @pytest.mark.asyncio
    async def test_save_result(self) -> None:
        storage, pool = _make_storage_with_pool()
        result = make_test_result()
        await storage.save_result(result)
        pool.conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_results_all(self) -> None:
        storage, pool = _make_storage_with_pool()
        result = make_test_result()
        pool.conn.fetch.return_value = [{"data": result.model_dump_json()}]

        results = await storage.load_results()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_load_results_by_name(self) -> None:
        storage, pool = _make_storage_with_pool()
        result = make_test_result(test_name="test_greeting")
        pool.conn.fetch.return_value = [{"data": result.model_dump_json()}]

        results = await storage.load_results(test_name="test_greeting")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_load_result_found(self) -> None:
        storage, pool = _make_storage_with_pool()
        result = make_test_result(result_id="res-123")
        pool.conn.fetchrow.return_value = {"data": result.model_dump_json()}

        loaded = await storage.load_result("res-123")
        assert loaded is not None
        assert loaded.result_id == "res-123"

    @pytest.mark.asyncio
    async def test_load_result_not_found(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.fetchrow.return_value = None

        loaded = await storage.load_result("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_load_result_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.fetchrow.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to load result"):
            await storage.load_result("res-123")

    @pytest.mark.asyncio
    async def test_save_result_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.execute.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to save result"):
            await storage.save_result(make_test_result())

    @pytest.mark.asyncio
    async def test_load_results_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.fetch.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to load results"):
            await storage.load_results()


class TestPostgreSQLStorageMetrics:
    """Test metric operations."""

    @pytest.mark.asyncio
    async def test_save_metrics(self) -> None:
        storage, pool = _make_storage_with_pool()
        metrics = [make_metric_value(), make_metric_value(metric_name="cost_usd")]
        await storage.save_metrics(metrics)
        assert pool.conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_save_metrics_empty(self) -> None:
        storage, pool = _make_storage_with_pool()
        await storage.save_metrics([])
        pool.conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_metrics_all(self) -> None:
        storage, pool = _make_storage_with_pool()
        now = datetime.now(UTC)
        pool.conn.fetch.return_value = [
            {
                "metric_name": "latency_ms",
                "value": 150.0,
                "tags": '["prod"]',
                "metadata": '{"key": "val"}',
                "timestamp": now,
            }
        ]

        metrics = await storage.load_metrics()
        assert len(metrics) == 1
        assert metrics[0].metric_name == "latency_ms"
        assert "prod" in metrics[0].tags

    @pytest.mark.asyncio
    async def test_load_metrics_by_name(self) -> None:
        storage, pool = _make_storage_with_pool()
        now = datetime.now(UTC)
        pool.conn.fetch.return_value = [
            {
                "metric_name": "cost_usd",
                "value": 0.05,
                "tags": None,
                "metadata": None,
                "timestamp": now,
            }
        ]

        metrics = await storage.load_metrics(metric_name="cost_usd")
        assert len(metrics) == 1
        assert metrics[0].tags == ()
        assert metrics[0].metadata == {}

    @pytest.mark.asyncio
    async def test_save_metrics_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.execute.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to save metrics"):
            await storage.save_metrics([make_metric_value()])

    @pytest.mark.asyncio
    async def test_load_metrics_error_raises(self) -> None:
        storage, pool = _make_storage_with_pool()
        pool.conn.fetch.side_effect = RuntimeError("db error")

        with pytest.raises(StorageError, match="Failed to load metrics"):
            await storage.load_metrics()


class TestSchemaMigration:
    """Test migration logic."""

    def test_latest_version(self) -> None:
        from agentprobe.storage.migrations import SchemaMigration

        migration = SchemaMigration()
        assert migration.latest_version >= 2

    def test_pending_migrations(self) -> None:
        from agentprobe.storage.migrations import SchemaMigration

        migration = SchemaMigration()
        pending = migration.get_pending(0)
        assert len(pending) == 2

        pending = migration.get_pending(1)
        assert len(pending) == 1
        assert pending[0][0] == 2

        pending = migration.get_pending(2)
        assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_apply_migrations(self) -> None:
        from agentprobe.storage.migrations import SchemaMigration

        migration = SchemaMigration()
        execute_fn = AsyncMock()

        new_version = await migration.apply(0, execute_fn)
        assert new_version == 2
        assert execute_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_apply_no_pending(self) -> None:
        from agentprobe.storage.migrations import SchemaMigration

        migration = SchemaMigration()
        execute_fn = AsyncMock()

        new_version = await migration.apply(2, execute_fn)
        assert new_version == 2
        execute_fn.assert_not_called()
