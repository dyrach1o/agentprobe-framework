"""CLI commands for trace inspection and listing."""

from __future__ import annotations

import asyncio

import click

from agentprobe.core.config import load_config
from agentprobe.storage.sqlite import SQLiteStorage


@click.group("trace")
def trace_group() -> None:
    """Inspect and manage execution traces."""


@trace_group.command("list")
@click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    help="Path to agentprobe.yaml config file.",
)
@click.option("--agent", "-a", default=None, help="Filter by agent name.")
@click.option("--limit", "-n", default=20, help="Maximum traces to show.")
def trace_list(config_path: str | None, agent: str | None, limit: int) -> None:
    """List recorded traces."""
    config = load_config(config_path)
    storage = SQLiteStorage(config.trace.database_path)

    async def _list() -> None:
        await storage.setup()
        traces = await storage.list_traces(agent_name=agent, limit=limit)
        if not traces:
            click.echo("No traces found.")
            return
        for trace in traces:
            click.echo(
                f"  {trace.trace_id[:8]}  {trace.agent_name:20s}  "
                f"{trace.total_input_tokens + trace.total_output_tokens:>8d} tokens  "
                f"{trace.created_at.isoformat()}"
            )
        await storage.close()

    asyncio.run(_list())


@trace_group.command("show")
@click.argument("trace_id")
@click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    help="Path to agentprobe.yaml config file.",
)
def trace_show(trace_id: str, config_path: str | None) -> None:
    """Show details for a specific trace."""
    config = load_config(config_path)
    storage = SQLiteStorage(config.trace.database_path)

    async def _show() -> None:
        await storage.setup()
        trace = await storage.load_trace(trace_id)
        if trace is None:
            click.echo(f"Trace not found: {trace_id}")
            await storage.close()
            return

        click.echo(f"Trace ID:     {trace.trace_id}")
        click.echo(f"Agent:        {trace.agent_name}")
        click.echo(f"Model:        {trace.model or 'N/A'}")
        click.echo(f"Input:        {trace.input_text[:100]}")
        click.echo(f"Output:       {trace.output_text[:100]}")
        click.echo(f"LLM Calls:    {len(trace.llm_calls)}")
        click.echo(f"Tool Calls:   {len(trace.tool_calls)}")
        click.echo(f"Tokens:       {trace.total_input_tokens} in / {trace.total_output_tokens} out")
        click.echo(f"Latency:      {trace.total_latency_ms}ms")
        click.echo(f"Tags:         {', '.join(trace.tags) or 'none'}")
        click.echo(f"Created:      {trace.created_at.isoformat()}")

        if trace.tool_calls:
            click.echo("\nTool Calls:")
            for tc in trace.tool_calls:
                status = "OK" if tc.success else f"FAIL: {tc.error}"
                click.echo(f"  - {tc.tool_name} [{status}]")

        await storage.close()

    asyncio.run(_show())
