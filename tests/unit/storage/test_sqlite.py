"""Tests for the SQLite storage backend."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from agentprobe.core.exceptions import StorageError
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.results import make_test_result
from tests.fixtures.traces import make_metric_value, make_trace


class TestSQLiteStorage:
    """Tests for SQLiteStorage operations."""

    @pytest.fixture
    async def storage(self, tmp_path: Path) -> SQLiteStorage:
        db_path = tmp_path / "test.db"
        s = SQLiteStorage(db_path)
        await s.setup()
        return s

    @pytest.mark.asyncio
    async def test_setup_creates_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "new.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()
        assert db_path.exists()
        await storage.close()

    @pytest.mark.asyncio
    async def test_save_and_load_trace(self, storage: SQLiteStorage) -> None:
        trace = make_trace(agent_name="test-agent", trace_id="trace-123")
        await storage.save_trace(trace)
        loaded = await storage.load_trace("trace-123")
        assert loaded is not None
        assert loaded.trace_id == "trace-123"
        assert loaded.agent_name == "test-agent"
        await storage.close()

    @pytest.mark.asyncio
    async def test_load_nonexistent_trace(self, storage: SQLiteStorage) -> None:
        loaded = await storage.load_trace("nonexistent")
        assert loaded is None
        await storage.close()

    @pytest.mark.asyncio
    async def test_list_traces(self, storage: SQLiteStorage) -> None:
        await storage.save_trace(make_trace(agent_name="agent1", trace_id="t1"))
        await storage.save_trace(make_trace(agent_name="agent2", trace_id="t2"))
        await storage.save_trace(make_trace(agent_name="agent1", trace_id="t3"))

        all_traces = await storage.list_traces()
        assert len(all_traces) == 3

        agent1_traces = await storage.list_traces(agent_name="agent1")
        assert len(agent1_traces) == 2

        limited = await storage.list_traces(limit=1)
        assert len(limited) == 1
        await storage.close()

    @pytest.mark.asyncio
    async def test_save_and_load_result(self, storage: SQLiteStorage) -> None:
        result = make_test_result(test_name="test_one")
        await storage.save_result(result)
        results = await storage.load_results(test_name="test_one")
        assert len(results) == 1
        assert results[0].test_name == "test_one"
        await storage.close()

    @pytest.mark.asyncio
    async def test_load_results_filtered(self, storage: SQLiteStorage) -> None:
        await storage.save_result(make_test_result(test_name="test_a"))
        await storage.save_result(make_test_result(test_name="test_b"))

        a_results = await storage.load_results(test_name="test_a")
        assert len(a_results) == 1

        all_results = await storage.load_results()
        assert len(all_results) == 2
        await storage.close()

    @pytest.mark.asyncio
    async def test_upsert_trace(self, storage: SQLiteStorage) -> None:
        trace1 = make_trace(trace_id="t1", output_text="first")
        await storage.save_trace(trace1)

        trace2 = make_trace(trace_id="t1", output_text="second")
        await storage.save_trace(trace2)

        loaded = await storage.load_trace("t1")
        assert loaded is not None
        assert loaded.output_text == "second"
        await storage.close()

    @pytest.mark.asyncio
    async def test_trace_with_calls_roundtrip(self, storage: SQLiteStorage) -> None:
        from tests.fixtures.traces import make_llm_call, make_tool_call

        trace = make_trace(
            trace_id="complex-1",
            llm_calls=[make_llm_call(model="gpt-4o", input_tokens=100)],
            tool_calls=[make_tool_call(tool_name="search")],
        )
        await storage.save_trace(trace)
        loaded = await storage.load_trace("complex-1")
        assert loaded is not None
        assert len(loaded.llm_calls) == 1
        assert loaded.llm_calls[0].model == "gpt-4o"
        assert len(loaded.tool_calls) == 1
        assert loaded.tool_calls[0].tool_name == "search"
        await storage.close()


class TestSQLiteSetup:
    """Tests for SQLiteStorage.setup() behavior."""

    @pytest.mark.asyncio
    async def test_setup_creates_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "tables.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        table_names = sorted(row[0] for row in cursor.fetchall())
        conn.close()

        assert "traces" in table_names
        assert "test_results" in table_names
        await storage.close()

    @pytest.mark.asyncio
    async def test_setup_creates_parent_directories(self, tmp_path: Path) -> None:
        db_path = tmp_path / "nested" / "deep" / "test.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()
        assert db_path.exists()
        await storage.close()

    @pytest.mark.asyncio
    async def test_setup_idempotent(self, tmp_path: Path) -> None:
        db_path = tmp_path / "idem.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()
        await storage.setup()  # Should not raise
        assert db_path.exists()
        await storage.close()

    @pytest.mark.asyncio
    async def test_setup_raises_storage_error_on_failure(self, tmp_path: Path) -> None:
        db_path = tmp_path / "fail.db"
        storage = SQLiteStorage(db_path)

        with (
            patch.object(
                storage, "_setup_sync", side_effect=sqlite3.OperationalError("disk I/O error")
            ),
            pytest.raises(StorageError, match="Failed to initialize SQLite"),
        ):
            await storage.setup()


class TestSQLiteErrorPaths:
    """Tests for error handling when database operations fail."""

    @pytest.mark.asyncio
    async def test_save_trace_raises_storage_error_on_closed_connection(
        self, tmp_path: Path
    ) -> None:
        db_path = tmp_path / "err_trace.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()
        await storage.close()

        # Manually set _conn to a closed connection to simulate corruption
        closed_conn = sqlite3.connect(str(db_path))
        closed_conn.close()
        storage._conn = closed_conn

        trace = make_trace(trace_id="will-fail")
        with pytest.raises(StorageError, match="Failed to save trace"):
            await storage.save_trace(trace)

    @pytest.mark.asyncio
    async def test_save_result_raises_storage_error_on_closed_connection(
        self, tmp_path: Path
    ) -> None:
        db_path = tmp_path / "err_result.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()
        await storage.close()

        # Manually set _conn to a closed connection to simulate corruption
        closed_conn = sqlite3.connect(str(db_path))
        closed_conn.close()
        storage._conn = closed_conn

        result = make_test_result(test_name="will-fail")
        with pytest.raises(StorageError, match="Failed to save result"):
            await storage.save_result(result)

    @pytest.mark.asyncio
    async def test_save_trace_raises_storage_error_on_sync_exception(self, tmp_path: Path) -> None:
        db_path = tmp_path / "err_sync.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        trace = make_trace(trace_id="sync-fail")
        with (
            patch.object(
                storage,
                "_save_trace_sync",
                side_effect=sqlite3.OperationalError("database is locked"),
            ),
            pytest.raises(StorageError, match="Failed to save trace"),
        ):
            await storage.save_trace(trace)
        await storage.close()

    @pytest.mark.asyncio
    async def test_save_result_raises_storage_error_on_sync_exception(self, tmp_path: Path) -> None:
        db_path = tmp_path / "err_sync_r.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        result = make_test_result(test_name="sync-fail")
        with (
            patch.object(
                storage,
                "_save_result_sync",
                side_effect=sqlite3.OperationalError("database is locked"),
            ),
            pytest.raises(StorageError, match="Failed to save result"),
        ):
            await storage.save_result(result)
        await storage.close()

    @pytest.mark.asyncio
    async def test_load_trace_raises_storage_error_on_failure(self, tmp_path: Path) -> None:
        db_path = tmp_path / "err_load.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        with (
            patch.object(
                storage,
                "_load_trace_sync",
                side_effect=RuntimeError("unexpected failure"),
            ),
            pytest.raises(StorageError, match="Failed to load trace"),
        ):
            await storage.load_trace("any-id")
        await storage.close()

    @pytest.mark.asyncio
    async def test_list_traces_raises_storage_error_on_failure(self, tmp_path: Path) -> None:
        db_path = tmp_path / "err_list.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        with (
            patch.object(
                storage,
                "_list_traces_sync",
                side_effect=RuntimeError("unexpected failure"),
            ),
            pytest.raises(StorageError, match="Failed to list traces"),
        ):
            await storage.list_traces()
        await storage.close()

    @pytest.mark.asyncio
    async def test_load_results_raises_storage_error_on_failure(self, tmp_path: Path) -> None:
        db_path = tmp_path / "err_results.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        with (
            patch.object(
                storage,
                "_load_results_sync",
                side_effect=RuntimeError("unexpected failure"),
            ),
            pytest.raises(StorageError, match="Failed to load results"),
        ):
            await storage.load_results()
        await storage.close()


class TestSQLiteMetrics:
    """Tests for SQLite metric storage operations."""

    @pytest.fixture
    async def storage(self, tmp_path: Path) -> SQLiteStorage:
        db_path = tmp_path / "metrics_test.db"
        s = SQLiteStorage(db_path)
        await s.setup()
        return s

    @pytest.mark.asyncio
    async def test_save_and_load_metrics(self, storage: SQLiteStorage) -> None:
        metrics = [
            make_metric_value(metric_name="latency_ms", value=150.0),
            make_metric_value(metric_name="cost_usd", value=0.05),
        ]
        await storage.save_metrics(metrics)

        loaded = await storage.load_metrics()
        assert len(loaded) == 2
        await storage.close()

    @pytest.mark.asyncio
    async def test_load_metrics_by_name(self, storage: SQLiteStorage) -> None:
        metrics = [
            make_metric_value(metric_name="latency_ms", value=100.0),
            make_metric_value(metric_name="latency_ms", value=200.0),
            make_metric_value(metric_name="cost_usd", value=0.01),
        ]
        await storage.save_metrics(metrics)

        latency = await storage.load_metrics(metric_name="latency_ms")
        assert len(latency) == 2
        assert all(m.metric_name == "latency_ms" for m in latency)

        cost = await storage.load_metrics(metric_name="cost_usd")
        assert len(cost) == 1
        await storage.close()

    @pytest.mark.asyncio
    async def test_save_empty_metrics(self, storage: SQLiteStorage) -> None:
        await storage.save_metrics([])
        loaded = await storage.load_metrics()
        assert len(loaded) == 0
        await storage.close()

    @pytest.mark.asyncio
    async def test_metrics_with_tags(self, storage: SQLiteStorage) -> None:
        mv = make_metric_value(tags=["prod", "fast"])
        await storage.save_metrics([mv])

        loaded = await storage.load_metrics()
        assert len(loaded) == 1
        assert "prod" in loaded[0].tags
        assert "fast" in loaded[0].tags
        await storage.close()

    @pytest.mark.asyncio
    async def test_metrics_limit(self, storage: SQLiteStorage) -> None:
        metrics = [make_metric_value(value=float(i)) for i in range(10)]
        await storage.save_metrics(metrics)

        limited = await storage.load_metrics(limit=3)
        assert len(limited) == 3
        await storage.close()

    @pytest.mark.asyncio
    async def test_metrics_table_created(self, tmp_path: Path) -> None:
        db_path = tmp_path / "schema_check.db"
        storage = SQLiteStorage(db_path)
        await storage.setup()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "metrics" in tables
        await storage.close()
