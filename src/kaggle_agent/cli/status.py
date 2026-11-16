"""`kaggle-agent status` — read-only run/profile summary (exit 0)."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from kaggle_agent.application.run_service import EXIT_OK, EXIT_VALIDATION_ERROR, configure_logging
from kaggle_agent.application.workspace import Workspace, WorkspaceError
from kaggle_agent.infrastructure.registry import Registry


def run_status(path: Path) -> int:
    configure_logging()
    try:
        ws = Workspace(path)
        ws.load_config()
    except WorkspaceError as exc:
        typer.echo(f"error: {exc}", err=True)
        return EXIT_VALIDATION_ERROR
    if not ws.registry_path.exists():
        typer.echo(f"no runs recorded yet for {ws.slug}")
        return EXIT_OK
    registry = Registry(ws.registry_path)
    runs = registry.list_runs(ws.slug)
    typer.echo(f"workspace: {ws.slug}")
    typer.echo(f"runs: {len(runs)}")
    for run in runs:
        typer.echo(
            f"  {run['kind']}: {run['status']} (started {run['started_at']}, "
            f"exit {run['exit_code']})"
        )
        if run["error"]:
            typer.echo(f"    error: {run['error']}")
    profile = registry.latest_profile(ws.slug)
    if profile is not None:
        n_cols = len(json.loads(profile["columns_json"]))
        typer.echo(
            f"profile: {profile['n_rows_train']} train rows, {profile['n_rows_test']} test rows, "
            f"{n_cols} columns, id_unique={bool(profile['id_unique'])}"
        )
        typer.echo(f"target_distribution: {profile['target_distribution_json']}")
        warnings = json.loads(profile["leakage_warnings_json"])
        typer.echo(f"leakage_warnings: {len(warnings)}")
        for warning in warnings:
            typer.echo(f"  warning: {warning}")
        budgets = json.loads(runs[-1]["budgets_json"]) if runs else None
        if budgets:
            typer.echo(f"budgets: {budgets}")
    latest = registry.latest_result(ws.slug)
    if latest is not None:
        typer.echo(
            f"incumbent: {latest['experiment_id']} {latest['metric_name']}="
            f"{latest['mean']:.6f} ± {latest['std']:.6f}"
        )
    else:
        typer.echo("incumbent: none (no completed experiment yet)")
    return EXIT_OK


def register(app: typer.Typer) -> None:
    @app.command()
    def status(
        path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    ) -> None:
        """Show runs and incumbent for a workspace (read-only)."""
        raise typer.Exit(run_status(path))
