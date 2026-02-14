"""Chaos fault injection proxy for testing agent resilience.

Wraps an adapter and modifies tool call results in the resulting
trace to simulate failures, timeouts, malformed data, rate limits,
slow responses, and empty responses.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from agentprobe.core.models import (
    ChaosOverride,
    ChaosType,
    ToolCall,
    Trace,
)
from agentprobe.core.protocols import AdapterProtocol

logger = logging.getLogger(__name__)


class ChaosProxy:
    """Wraps an adapter and injects chaos faults into tool call results.

    After the real adapter produces a trace, ChaosProxy scans tool calls
    and probabilistically replaces their outputs with fault-injected
    variants. The modified trace is returned as a frozen copy.

    Attributes:
        overrides: Configured fault injection rules.
    """

    def __init__(
        self,
        adapter: AdapterProtocol,
        overrides: list[ChaosOverride],
        *,
        seed: int = 42,
    ) -> None:
        """Initialize the chaos proxy.

        Args:
            adapter: The real adapter to wrap.
            overrides: Fault injection rules to apply.
            seed: Random seed for deterministic fault injection.
        """
        self._adapter = adapter
        self._overrides = overrides
        self._rng = random.Random(seed)

    @property
    def name(self) -> str:
        """Return the adapter name with chaos prefix."""
        return f"chaos-{self._adapter.name}"

    async def invoke(self, input_text: str, **kwargs: Any) -> Trace:
        """Invoke the wrapped adapter and inject faults.

        Args:
            input_text: Input text to send to the adapter.
            **kwargs: Additional adapter arguments.

        Returns:
            A modified trace with chaos faults injected.
        """
        trace = await self._adapter.invoke(input_text, **kwargs)
        return self._apply_chaos(trace)

    def _apply_chaos(self, trace: Trace) -> Trace:
        """Apply chaos overrides to tool calls in the trace."""
        if not trace.tool_calls or not self._overrides:
            return trace

        modified_calls: list[ToolCall] = []
        any_modified = False

        for tc in trace.tool_calls:
            override = self._match_override(tc)
            if override is not None and self._rng.random() < override.probability:
                modified_calls.append(self._inject_fault(tc, override))
                any_modified = True
            else:
                modified_calls.append(tc)

        if not any_modified:
            return trace

        return trace.model_copy(
            update={"tool_calls": tuple(modified_calls)},
        )

    def _match_override(self, tool_call: ToolCall) -> ChaosOverride | None:
        """Find the first matching override for a tool call."""
        for override in self._overrides:
            if override.target_tool is None or override.target_tool == tool_call.tool_name:
                return override
        return None

    def _inject_fault(self, tool_call: ToolCall, override: ChaosOverride) -> ToolCall:
        """Create a fault-injected copy of a tool call."""
        logger.debug(
            "Injecting %s fault into tool '%s'",
            override.chaos_type.value,
            tool_call.tool_name,
        )
        fault_map: dict[ChaosType, dict[str, Any]] = {
            ChaosType.TIMEOUT: {
                "success": False,
                "error": "Chaos: operation timed out",
                "tool_output": None,
            },
            ChaosType.ERROR: {
                "success": False,
                "error": f"Chaos: {override.error_message}",
                "tool_output": None,
            },
            ChaosType.MALFORMED: {
                "success": True,
                "tool_output": "{malformed: data, <<invalid>>}",
            },
            ChaosType.RATE_LIMIT: {
                "success": False,
                "error": "Chaos: rate limit exceeded (429)",
                "tool_output": None,
            },
            ChaosType.SLOW: {
                "success": True,
                "tool_output": tool_call.tool_output,
                "latency_ms": tool_call.latency_ms + override.delay_ms,
            },
            ChaosType.EMPTY: {
                "success": True,
                "tool_output": "",
            },
        }
        updates = fault_map.get(
            override.chaos_type,
            {"success": False, "error": f"Chaos: unknown type {override.chaos_type}"},
        )
        return tool_call.model_copy(update=updates)
