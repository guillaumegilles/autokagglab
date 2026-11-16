"""Competition configuration contract (Pydantic v2).

Mirrors specs/001-competition-baseline/contracts/competition-config.schema.json.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(StrEnum):
    BINARY_CLASSIFICATION = "binary-classification"
    REGRESSION = "regression"


class CVStrategy(StrEnum):
    STRATIFIED_KFOLD = "stratified-kfold"
    KFOLD = "kfold"


BINARY_METRICS = {"roc_auc", "log_loss"}
REGRESSION_METRICS = {"rmse", "mae", "r2"}
ALL_METRICS = BINARY_METRICS | REGRESSION_METRICS


class CVConfig(BaseModel):
    strategy: CVStrategy
    n_folds: int = Field(default=5, ge=2, le=10)


class Budgets(BaseModel):
    max_experiments: int = Field(default=10, ge=1)
    experiment_timeout_seconds: int = Field(default=1200, ge=60)
    run_timeout_seconds: int = Field(default=10800, ge=300)
    max_consecutive_failures: int = Field(default=3, ge=1)
    min_improvement: float = Field(default=0.001, ge=0)


class CompetitionConfig(BaseModel):
    name: str = Field(min_length=1)
    task: TaskType
    target: str = Field(min_length=1)
    id_columns: list[str] = Field(min_length=1)
    metric: str
    cv: CVConfig
    seed: int = 42
    budgets: Budgets

    @field_validator("id_columns")
    @classmethod
    def _unique_id_columns(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("id_columns must be unique")
        return value

    @field_validator("metric")
    @classmethod
    def _known_metric(cls, value: str) -> str:
        if value not in ALL_METRICS:
            raise ValueError(
                f"unsupported metric '{value}'; supported: {', '.join(sorted(ALL_METRICS))}"
            )
        return value

    @model_validator(mode="after")
    def _check_task_metric_cv(self) -> CompetitionConfig:
        if self.task == TaskType.BINARY_CLASSIFICATION:
            if self.metric not in BINARY_METRICS:
                raise ValueError(
                    f"metric '{self.metric}' is not supported for binary-classification; "
                    f"supported: {', '.join(sorted(BINARY_METRICS))}"
                )
            if self.cv.strategy != CVStrategy.STRATIFIED_KFOLD:
                raise ValueError(
                    "binary-classification requires cv.strategy 'stratified-kfold' "
                    "(supported: stratified-kfold)"
                )
        else:
            if self.metric not in REGRESSION_METRICS:
                raise ValueError(
                    f"metric '{self.metric}' is not supported for regression; "
                    f"supported: {', '.join(sorted(REGRESSION_METRICS))}"
                )
            if self.cv.strategy != CVStrategy.KFOLD:
                raise ValueError("regression requires cv.strategy 'kfold' (supported: kfold)")
        return self

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    @classmethod
    def load(cls, path: Path) -> CompetitionConfig:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"invalid competition config in {path}: expected a mapping")
        return cls.model_validate(data)
