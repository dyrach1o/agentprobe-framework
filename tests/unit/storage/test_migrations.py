"""Dedicated tests for the SchemaMigration system."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agentprobe.storage.migrations import SchemaMigration


class TestSchemaMigrationVersioning:
    """Tests for schema version tracking and boundaries."""

    def test_latest_version_is_two(self) -> None:
        migration = SchemaMigration()
        assert migration.latest_version == 2

    def test_get_pending_from_zero(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(0)
        assert len(pending) == 2
        assert pending[0][0] == 1
        assert pending[1][0] == 2

    def test_get_pending_from_one(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(1)
        assert len(pending) == 1
        assert pending[0][0] == 2

    def test_get_pending_at_current(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(2)
        assert len(pending) == 0

    def test_get_pending_above_latest(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(99)
        assert len(pending) == 0

    def test_migration_sql_contains_traces_table(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(0)
        v1_sql = pending[0][1]
        assert "CREATE TABLE IF NOT EXISTS traces" in v1_sql

    def test_migration_sql_contains_results_table(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(0)
        v1_sql = pending[0][1]
        assert "CREATE TABLE IF NOT EXISTS test_results" in v1_sql

    def test_migration_sql_contains_metrics_table(self) -> None:
        migration = SchemaMigration()
        pending = migration.get_pending(0)
        v2_sql = pending[1][1]
        assert "CREATE TABLE IF NOT EXISTS metrics" in v2_sql


class TestSchemaMigrationApply:
    """Tests for applying migrations."""

    @pytest.mark.asyncio
    async def test_apply_from_zero(self) -> None:
        migration = SchemaMigration()
        execute_fn = AsyncMock()

        new_version = await migration.apply(0, execute_fn)
        assert new_version == 2
        assert execute_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_apply_from_one(self) -> None:
        migration = SchemaMigration()
        execute_fn = AsyncMock()

        new_version = await migration.apply(1, execute_fn)
        assert new_version == 2
        assert execute_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_apply_no_pending(self) -> None:
        migration = SchemaMigration()
        execute_fn = AsyncMock()

        new_version = await migration.apply(2, execute_fn)
        assert new_version == 2
        execute_fn.assert_not_called()

    @pytest.mark.asyncio
    async def test_apply_empty_migrations(self) -> None:
        migration = SchemaMigration()
        migration._migrations = []
        execute_fn = AsyncMock()

        new_version = await migration.apply(0, execute_fn)
        assert new_version == 0
        execute_fn.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_migrations_latest_version(self) -> None:
        migration = SchemaMigration()
        migration._migrations = []
        assert migration.latest_version == 0
