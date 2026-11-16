"""MLflow tracking adapter (local file store only; fully offline)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

import mlflow

from kaggle_agent.application.workspace import Workspace


class Tracker:
    def __init__(self, workspace: Workspace) -> None:
        self._mlruns = workspace.mlruns_dir
        self._mlruns.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(self._mlruns.as_uri())
        mlflow.set_experiment(workspace.slug)

    def start_run(self, name: str) -> str:
        run = mlflow.start_run(run_name=name)
        return str(run.info.run_id)

    def log_params(self, params: dict[str, Any]) -> None:
        mlflow.log_params({k: str(v) for k, v in params.items()})

    def log_metrics(self, metrics: dict[str, float]) -> None:
        mlflow.log_metrics(metrics)

    def log_artifact(self, local_path: Path, artifact_path: str | None = None) -> None:
        mlflow.log_artifact(str(local_path), artifact_path)

    def end_run(self, status: str = "FINISHED") -> None:
        mlflow.end_run(status)
