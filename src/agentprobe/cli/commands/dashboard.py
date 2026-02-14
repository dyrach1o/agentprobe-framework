"""Dashboard CLI command for starting the REST API server."""

from __future__ import annotations

import click


@click.command("dashboard")
@click.option("--host", default="127.0.0.1", help="Host to bind the server to.")
@click.option("--port", default=8000, type=int, help="Port to bind the server to.")
@click.option(
    "--db",
    default=".agentprobe/traces.db",
    help="Path to the SQLite database file.",
)
def dashboard_cmd(host: str, port: int, db: str) -> None:
    """Start the AgentProbe dashboard API server."""
    try:
        import uvicorn

        from agentprobe.dashboard.app import create_app
    except ImportError:
        click.echo(
            "Dashboard dependencies not installed. Install with: pip install agentprobe-framework[dashboard]",
            err=True,
        )
        raise SystemExit(1)  # noqa: B904

    app = create_app(db_path=db)
    uvicorn.run(app, host=host, port=port)  # pragma: no cover
