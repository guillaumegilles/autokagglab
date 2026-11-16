"""Domain entities and state machines (see specs/001-competition-baseline/data-model.md)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExperimentStatus(StrEnum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    REJECTED_DUPLICATE = "REJECTED_DUPLICATE"
    REJECTED_POLICY = "REJECTED_POLICY"


@dataclass
class Competition:
    slug: str
    config_json: str
    config_fingerprint: str
    created_at: str


@dataclass
class DatasetProfile:
    competition_slug: str
    n_rows_train: int
    n_rows_test: int
    columns: list[dict[str, Any]]
    target_distribution: dict[str, Any]
    id_unique: bool
    leakage_warnings: list[str]
    fingerprints: dict[str, str]
    schema_diff: dict[str, Any] | None
    created_at: str


@dataclass
class ResearchRun:
    run_id: str
    competition_slug: str
    kind: str
    status: RunStatus
    budgets_json: str
    started_at: str
    finished_at: str | None = None
    exit_code: int | None = None
    error: str | None = None


@dataclass
class Experiment:
    experiment_id: str
    run_id: str
    parent_id: str | None
    hypothesis: str
    change_json: str
    model_family: str
    params_json: str
    feature_set_version: str
    experiment_fingerprint: str
    cv_strategy: str
    seed: int
    status: ExperimentStatus
    git_commit: str | None


@dataclass
class Result:
    experiment_id: str
    metric_name: str
    direction: str
    fold_metrics: list[dict[str, Any]]
    mean: float
    std: float
    runtime_seconds: float
    environment_json: str
    mlflow_run_id: str | None
    conclusion: str | None = None


@dataclass
class ResearchLogEntry:
    entry_id: str
    timestamp: str
    run_id: str
    type: str
    status: str
    experiment_id: str | None = None
    hypothesis: dict[str, Any] | None = None
    observed: dict[str, Any] | None = None
    conclusion: str | None = None
    parent_entry_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)
