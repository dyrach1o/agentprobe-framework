#!/usr/bin/env python3
"""Example: Querying the AgentProbe dashboard REST API.

Demonstrates how to interact with the dashboard API endpoints
using httpx. Start the server first with:

    agentprobe dashboard --db .agentprobe/traces.db

Then run this script to query traces, results, and metrics.
"""

from __future__ import annotations

import asyncio
import sys


async def main() -> None:
    """Query the dashboard API endpoints."""
    try:
        import httpx  # type: ignore[import-untyped]
    except ImportError:
        print("httpx is required: pip install httpx")
        sys.exit(1)

    base_url = "http://127.0.0.1:8000"

    async with httpx.AsyncClient(base_url=base_url) as client:
        # Health check
        print("=== Health Check ===")
        resp = await client.get("/api/health")
        if resp.status_code != 200:
            print(f"Dashboard not reachable at {base_url}. Is it running?")
            print("Start with: agentprobe dashboard")
            sys.exit(1)
        health = resp.json()
        print(f"  Status: {health['status']}")
        print(f"  Version: {health['version']}")

        # List traces
        print("\n=== Recent Traces ===")
        resp = await client.get("/api/traces", params={"limit": 5})
        traces = resp.json()
        if not traces:
            print("  No traces found. Run some tests first.")
        for trace in traces:
            print(
                f"  {trace['trace_id'][:12]}... "
                f"agent={trace['agent_name']} "
                f"tokens={trace['total_input_tokens']}+{trace['total_output_tokens']}"
            )

        # List results
        print("\n=== Recent Results ===")
        resp = await client.get("/api/results", params={"limit": 5})
        results = resp.json()
        if not results:
            print("  No results found. Run some tests first.")
        for result in results:
            print(f"  {result['test_name']}: status={result['status']} score={result['score']:.2f}")

        # Metrics summary
        print("\n=== Metrics Summary ===")
        resp = await client.get("/api/metrics/summary")
        summary = resp.json()
        if not summary:
            print("  No metrics collected yet.")
        for name, agg in summary.items():
            print(f"  {name}: mean={agg['mean']:.2f}, count={agg['count']}")


if __name__ == "__main__":
    asyncio.run(main())
