"""T024 — DatasetProfiler: machine-readable profile (FR-006/FR-007)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from kaggle_agent.application.run_service import utc_now
from kaggle_agent.application.validate_service import ValidationOutcome
from kaggle_agent.application.workspace import Workspace
from kaggle_agent.domain.config import TaskType
from kaggle_agent.domain.entities import DatasetProfile
from kaggle_agent.domain.fingerprints import schema_hash

MAX_CATEGORICAL_CARDINALITY = 50


def _column_profile(series: pd.Series) -> dict[str, Any]:
    n_unique = int(series.nunique(dropna=True))
    is_likely_categorical = (
        series.dtype == object or n_unique <= MAX_CATEGORICAL_CARDINALITY and series.dtype != float
    )
    return {
        "name": str(series.name),
        "dtype": str(series.dtype),
        "missing": int(series.isna().sum()),
        "n_unique": n_unique,
        "is_constant": n_unique <= 1,
        "is_likely_categorical": bool(is_likely_categorical),
    }


class DatasetProfiler:
    def __init__(self, workspace: Workspace, outcome: ValidationOutcome) -> None:
        self.workspace = workspace
        self.outcome = outcome

    def profile(self) -> DatasetProfile:
        config = self.outcome.config
        train = self.outcome.train
        test = self.outcome.test
        assert config is not None and train is not None and test is not None

        columns = [_column_profile(train[col]) for col in train.columns]

        if config.task == TaskType.BINARY_CLASSIFICATION:
            counts = train[config.target].value_counts()
            target_distribution: dict[str, Any] = {
                "type": "classification",
                "counts": {str(k): int(v) for k, v in counts.items()},
            }
        else:
            target_distribution = {
                "type": "regression",
                "mean": float(train[config.target].mean()),
                "std": float(train[config.target].std()),
                "min": float(train[config.target].min()),
                "max": float(train[config.target].max()),
            }

        id_unique = all(
            not train[col].duplicated().any() and not test[col].duplicated().any()
            for col in config.id_columns
        )

        fingerprints = dict(self.outcome.fingerprints)
        fingerprints["train_schema"] = schema_hash(train)
        fingerprints["test_schema"] = schema_hash(test)

        schema_diff = None if not self.outcome.errors else {"errors": self.outcome.errors}

        return DatasetProfile(
            competition_slug=self.workspace.slug,
            n_rows_train=int(len(train)),
            n_rows_test=int(len(test)),
            columns=columns,
            target_distribution=target_distribution,
            id_unique=id_unique,
            leakage_warnings=list(self.outcome.warnings),
            fingerprints=fingerprints,
            schema_diff=schema_diff,
            created_at=utc_now(),
        )
