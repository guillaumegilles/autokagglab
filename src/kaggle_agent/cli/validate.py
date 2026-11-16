"""`kaggle-agent validate` — validate a competition workspace (exit 0/2)."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from kaggle_agent.application.profile_service import DatasetProfiler
from kaggle_agent.application.run_service import (
    EXIT_OK,
    EXIT_VALIDATION_ERROR,
    configure_logging,
    new_run_id,
    utc_now,
)
from kaggle_agent.application.validate_service import CompetitionValidator
from kaggle_agent.application.workspace import Workspace, WorkspaceError
from kaggle_agent.domain.entities import Competition, ResearchRun, RunStatus
from kaggle_agent.domain.fingerprints import canonical_json_hash
from kaggle_agent.infrastructure.registry import Registry


def run_validate(path: Path, config_override: Path | None = None) -> int:
    configure_logging()
    try:
        ws = Workspace(path, config_override=config_override)
        outcome = CompetitionValidator(ws).validate()
    except WorkspaceError as exc:
        typer.echo(f"error: {exc}", err=True)
        return EXIT_VALIDATION_ERROR

    if not outcome.ok or outcome.config is None:
        for error in outcome.errors:
            typer.echo(f"error: {error}", err=True)
        return EXIT_VALIDATION_ERROR

    config = outcome.config
    registry = Registry(ws.registry_path)
    registry.save_competition(
        Competition(
            slug=ws.slug,
            config_json=config.canonical_json(),
            config_fingerprint=canonical_json_hash(config.model_dump(mode="json")),
            created_at=utc_now(),
        )
    )
    run = ResearchRun(
        run_id=new_run_id(),
        competition_slug=ws.slug,
        kind="validate",
        status=RunStatus.COMPLETED,
        budgets_json=json.dumps(config.budgets.model_dump(mode="json")),
        started_at=utc_now(),
        finished_at=utc_now(),
        exit_code=EXIT_OK,
    )
    registry.create_run(run)

    profile = DatasetProfiler(ws, outcome).profile()
    registry.save_profile(profile)

    for warning in outcome.warnings:
        typer.echo(f"warning: {warning}")
    typer.echo(
        f"OK: competition '{config.name}' validated ({ws.slug}): "
        f"{profile.n_rows_train} train rows, {profile.n_rows_test} test rows, "
        f"{len(profile.columns)} profiled columns"
    )
    typer.echo(
        json.dumps(
            {
                "n_rows_train": profile.n_rows_train,
                "n_rows_test": profile.n_rows_test,
                "columns": profile.columns,
                "target_distribution": profile.target_distribution,
                "id_unique": profile.id_unique,
                "leakage_warnings": profile.leakage_warnings,
                "fingerprints": profile.fingerprints,
            },
            indent=2,
            default=str,
        )
    )
    return EXIT_OK


def register(app: typer.Typer) -> None:
    @app.command()
    def validate(
        path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
        config: Path | None = typer.Option(
            None, "--config", help="Override competition.yaml with this config file"
        ),
    ) -> None:
        """Validate a competition workspace before any training."""
        raise typer.Exit(run_validate(path, config))
