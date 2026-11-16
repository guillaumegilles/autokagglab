"""`kaggle-agent baseline` — deterministic CV baseline (exit 0/2/3)."""

from __future__ import annotations

from pathlib import Path

import typer

from kaggle_agent.application.baseline_service import BaselineService
from kaggle_agent.application.run_service import configure_logging
from kaggle_agent.application.workspace import Workspace, WorkspaceError


def register(app: typer.Typer) -> None:
    @app.command()
    def baseline(
        path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
        target_encoding: bool = typer.Option(
            False, "--target-encoding", help="Enable fold-isolated target encoding"
        ),
    ) -> None:
        """Run the deterministic baseline for a validated workspace."""
        configure_logging()
        try:
            ws = Workspace(path)
        except WorkspaceError as exc:
            typer.echo(f"error: {exc}", err=True)
            raise typer.Exit(2) from None
        raise typer.Exit(
            BaselineService(ws).run(
                transform_strategy="target_encoding" if target_encoding else None
            )
        )
