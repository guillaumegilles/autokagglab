"""`kaggle-agent init` — scaffold a competition workspace (FR-012)."""

from __future__ import annotations

from pathlib import Path

import typer

from kaggle_agent.application.run_service import EXIT_OK, configure_logging
from kaggle_agent.application.workspace import init_workspace
from kaggle_agent.domain.config import (
    ALL_METRICS,
    Budgets,
    CompetitionConfig,
    CVConfig,
    CVStrategy,
    TaskType,
)


def register(app: typer.Typer) -> None:
    @app.command()
    def init(
        path: Path = typer.Argument(..., file_okay=False),
        task: TaskType = typer.Option(TaskType.BINARY_CLASSIFICATION, "--task"),
        target: str = typer.Option("target", "--target"),
        id_column: str = typer.Option("id", "--id"),
        metric: str = typer.Option("roc_auc", "--metric"),
    ) -> None:
        """Create a competition workspace with a default competition.yaml."""
        configure_logging()
        if metric not in ALL_METRICS:
            supported = ", ".join(sorted(ALL_METRICS))
            typer.echo(
                f"error: unsupported metric '{metric}'; supported: {supported}",
                err=True,
            )
            raise typer.Exit(2)
        strategy = (
            CVStrategy.STRATIFIED_KFOLD
            if task == TaskType.BINARY_CLASSIFICATION
            else CVStrategy.KFOLD
        )
        config = CompetitionConfig(
            name=path.name,
            task=task,
            target=target,
            id_columns=[id_column],
            metric=metric,
            cv=CVConfig(strategy=strategy, n_folds=5),
            seed=42,
            budgets=Budgets(),
        )
        init_workspace(path, config)
        typer.echo(
            f"initialized workspace at {path} (add data/train.csv, data/test.csv, "
            f"data/sample_submission.csv)"
        )
        raise typer.Exit(EXIT_OK)
