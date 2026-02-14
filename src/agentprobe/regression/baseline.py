"""Baseline management for regression testing.

Provides CRUD operations for named baselines stored as JSON files
containing serialized TestResult lists.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path

from agentprobe.core.exceptions import RegressionError
from agentprobe.core.models import TestResult

logger = logging.getLogger(__name__)


class BaselineManager:
    """Manages baseline files for regression testing.

    Stores sets of TestResult objects as JSON files, enabling
    comparison between historical and current test runs.

    Attributes:
        baseline_dir: Directory where baseline files are stored.
    """

    def __init__(self, baseline_dir: str | Path = ".agentprobe/baselines") -> None:
        """Initialize the baseline manager.

        Args:
            baseline_dir: Directory for baseline storage.
        """
        self._dir = Path(baseline_dir)

    def _baseline_path(self, name: str) -> Path:
        """Get the file path for a named baseline."""
        return self._dir / f"{name}.json"

    def save(self, name: str, results: Sequence[TestResult]) -> Path:
        """Save test results as a named baseline.

        Args:
            name: Baseline name.
            results: Test results to save.

        Returns:
            Path to the saved baseline file.
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._baseline_path(name)

        data = [json.loads(r.model_dump_json()) for r in results]
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Baseline saved: %s (%d results)", name, len(data))
        return path

    def load(self, name: str) -> list[TestResult]:
        """Load a named baseline.

        Args:
            name: Baseline name.

        Returns:
            List of saved TestResult objects.

        Raises:
            RegressionError: If the baseline does not exist.
        """
        path = self._baseline_path(name)
        if not path.exists():
            raise RegressionError(f"Baseline not found: {name}")

        raw = json.loads(path.read_text(encoding="utf-8"))
        return [TestResult.model_validate_json(json.dumps(item)) for item in raw]

    def exists(self, name: str) -> bool:
        """Check if a named baseline exists."""
        return self._baseline_path(name).exists()

    def list_baselines(self) -> list[str]:
        """List all baseline names."""
        if not self._dir.is_dir():
            return []
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def delete(self, name: str) -> bool:
        """Delete a named baseline.

        Args:
            name: Baseline name.

        Returns:
            True if deleted, False if not found.
        """
        path = self._baseline_path(name)
        if path.exists():
            path.unlink()
            logger.info("Baseline deleted: %s", name)
            return True
        return False
