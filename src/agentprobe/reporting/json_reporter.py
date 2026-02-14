"""JSON file reporter for test results.

Writes the complete AgentRun as a JSON file for consumption by
CI/CD pipelines and other tools.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from agentprobe.core.models import AgentRun

logger = logging.getLogger(__name__)


class JSONReporter:
    """Reporter that writes results to a JSON file.

    Attributes:
        output_dir: Directory to write report files to.
    """

    def __init__(self, output_dir: str | Path = "agentprobe-report") -> None:
        """Initialize the JSON reporter.

        Args:
            output_dir: Directory for report output.
        """
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        """Return the reporter name."""
        return "json"

    async def report(self, run: AgentRun) -> None:
        """Write the agent run as a JSON file.

        Args:
            run: The completed agent run.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"report-{run.run_id}.json"

        data = json.loads(run.model_dump_json())
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("JSON report written to %s", output_path)
