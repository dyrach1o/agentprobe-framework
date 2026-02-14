"""Snapshot (golden file) management for output comparison testing.

Saves, loads, compares, and updates agent output snapshots stored
as JSON files. Supports multi-dimension comparison including tool
calls, response structure, key facts, cost, and latency.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agentprobe.core.exceptions import SnapshotError
from agentprobe.core.models import DiffItem, SnapshotDiff, Trace

logger = logging.getLogger(__name__)


def _sequence_similarity(a: list[str], b: list[str]) -> float:
    """Compute normalized similarity between two string sequences."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    matches = sum(1 for x, y in zip(a, b, strict=False) if x == y)
    return matches / max(len(a), len(b))


def _keyword_overlap(a: str, b: str) -> float:
    """Compute keyword overlap between two strings."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


class SnapshotManager:
    """Manages snapshot files for golden-file testing.

    Saves traces as JSON snapshots and compares current traces against
    saved snapshots across multiple dimensions.

    Attributes:
        snapshot_dir: Directory where snapshot files are stored.
        threshold: Similarity threshold for matching.
    """

    def __init__(
        self,
        snapshot_dir: str | Path = ".agentprobe/snapshots",
        *,
        threshold: float = 0.8,
    ) -> None:
        """Initialize the snapshot manager.

        Args:
            snapshot_dir: Directory for snapshot storage.
            threshold: Similarity threshold for a match.
        """
        self._dir = Path(snapshot_dir)
        self._threshold = threshold

    def _snapshot_path(self, name: str) -> Path:
        """Get the file path for a named snapshot."""
        return self._dir / f"{name}.json"

    def save(self, name: str, trace: Trace) -> Path:
        """Save a trace as a named snapshot.

        Args:
            name: Snapshot name.
            trace: Trace to save.

        Returns:
            Path to the saved snapshot file.
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._snapshot_path(name)
        path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Snapshot saved: %s", path)
        return path

    def load(self, name: str) -> Trace:
        """Load a named snapshot.

        Args:
            name: Snapshot name.

        Returns:
            The saved Trace.

        Raises:
            SnapshotError: If the snapshot does not exist.
        """
        path = self._snapshot_path(name)
        if not path.exists():
            raise SnapshotError(f"Snapshot not found: {name}")
        return Trace.model_validate_json(path.read_text(encoding="utf-8"))

    def exists(self, name: str) -> bool:
        """Check if a named snapshot exists."""
        return self._snapshot_path(name).exists()

    def list_snapshots(self) -> list[str]:
        """List all snapshot names."""
        if not self._dir.is_dir():
            return []
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def delete(self, name: str) -> bool:
        """Delete a named snapshot.

        Args:
            name: Snapshot name.

        Returns:
            True if deleted, False if not found.
        """
        path = self._snapshot_path(name)
        if path.exists():
            path.unlink()
            logger.info("Snapshot deleted: %s", name)
            return True
        return False

    def compare(self, name: str, current: Trace) -> SnapshotDiff:
        """Compare a current trace against a saved snapshot.

        Compares across dimensions: tool_calls, output, token_usage,
        latency, and metadata.

        Args:
            name: Snapshot name.
            current: Current trace to compare.

        Returns:
            A SnapshotDiff with per-dimension similarity scores.

        Raises:
            SnapshotError: If the snapshot does not exist.
        """
        baseline = self.load(name)
        diffs: list[DiffItem] = []

        # Tool call sequence similarity
        baseline_tools = [tc.tool_name for tc in baseline.tool_calls]
        current_tools = [tc.tool_name for tc in current.tool_calls]
        tool_sim = _sequence_similarity(baseline_tools, current_tools)
        diffs.append(
            DiffItem(
                dimension="tool_calls",
                expected=baseline_tools,
                actual=current_tools,
                similarity=round(tool_sim, 4),
            )
        )

        # Output text similarity
        output_sim = _keyword_overlap(baseline.output_text, current.output_text)
        diffs.append(
            DiffItem(
                dimension="output",
                expected=baseline.output_text[:200],
                actual=current.output_text[:200],
                similarity=round(output_sim, 4),
            )
        )

        # Token usage similarity
        baseline_tokens = baseline.total_input_tokens + baseline.total_output_tokens
        current_tokens = current.total_input_tokens + current.total_output_tokens
        if baseline_tokens > 0:
            token_ratio = min(current_tokens, baseline_tokens) / max(
                current_tokens, baseline_tokens
            )
        elif current_tokens == 0:
            token_ratio = 1.0
        else:
            token_ratio = 0.0
        diffs.append(
            DiffItem(
                dimension="token_usage",
                expected=baseline_tokens,
                actual=current_tokens,
                similarity=round(token_ratio, 4),
            )
        )

        # Latency similarity
        if baseline.total_latency_ms > 0:
            latency_ratio = min(current.total_latency_ms, baseline.total_latency_ms) / max(
                current.total_latency_ms, baseline.total_latency_ms
            )
        elif current.total_latency_ms == 0:
            latency_ratio = 1.0
        else:
            latency_ratio = 0.0
        diffs.append(
            DiffItem(
                dimension="latency",
                expected=baseline.total_latency_ms,
                actual=current.total_latency_ms,
                similarity=round(latency_ratio, 4),
            )
        )

        # Overall weighted average
        weights = {"tool_calls": 0.35, "output": 0.35, "token_usage": 0.15, "latency": 0.15}
        overall = sum(d.similarity * weights.get(d.dimension, 0.0) for d in diffs)

        is_match = overall >= self._threshold

        return SnapshotDiff(
            snapshot_name=name,
            overall_similarity=round(overall, 4),
            diffs=tuple(diffs),
            is_match=is_match,
            threshold=self._threshold,
        )

    def update_all(self, snapshots: dict[str, Trace]) -> int:
        """Update multiple snapshots at once.

        Args:
            snapshots: Mapping of snapshot names to traces.

        Returns:
            Number of snapshots updated.
        """
        count = 0
        for name, trace in snapshots.items():
            self.save(name, trace)
            count += 1
        return count
