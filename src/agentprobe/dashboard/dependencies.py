"""Dependency injection helpers for the dashboard API."""

from __future__ import annotations

from agentprobe.storage.sqlite import SQLiteStorage


def get_storage(db_path: str = ".agentprobe/traces.db") -> SQLiteStorage:
    """Create a SQLiteStorage instance for the given database path.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A configured SQLiteStorage instance.
    """
    return SQLiteStorage(db_path=db_path)
