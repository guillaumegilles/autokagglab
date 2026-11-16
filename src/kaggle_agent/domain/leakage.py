"""Leakage and validation preflight.

Blocking errors fail validation before any training; warnings are reported in
the dataset profile without blocking the run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from kaggle_agent.domain.config import CompetitionConfig, TaskType


@dataclass
class PreflightResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def id_like_feature_columns(train: pd.DataFrame, config: CompetitionConfig) -> list[str]:
    """Feature columns that look like row identifiers (unique per row and
    string-typed or id-named): likely leakage risks."""
    protected = {config.target, *config.id_columns}
    flagged: list[str] = []
    for col in train.columns:
        if col in protected:
            continue
        is_string = not pd.api.types.is_numeric_dtype(train[col])
        if train[col].nunique(dropna=True) == len(train) and (is_string or "id" in col.lower()):
            flagged.append(col)
    return flagged


def preflight(
    train: pd.DataFrame,
    test: pd.DataFrame,
    config: CompetitionConfig,
) -> PreflightResult:
    result = PreflightResult()
    protected = {config.target, *config.id_columns}

    if config.target in config.id_columns:
        result.errors.append("target column must not be listed in id_columns (target leakage)")
    if config.target not in train.columns:
        result.errors.append(f"missing target column '{config.target}' in train.csv")
    for id_col in config.id_columns:
        if id_col not in train.columns or id_col not in test.columns:
            result.errors.append(f"identifier column '{id_col}' missing from train.csv or test.csv")
            continue
        if train[id_col].duplicated().any():
            result.errors.append(f"duplicate identifiers in train.csv column '{id_col}'")
        if test[id_col].duplicated().any():
            result.errors.append(f"duplicate identifiers in test.csv column '{id_col}'")

    feature_cols = [c for c in train.columns if c not in protected]
    missing_in_test = [c for c in feature_cols if c not in test.columns]
    if missing_in_test:
        result.errors.append(
            "train/test schema mismatch: features missing from test.csv: "
            + ", ".join(missing_in_test)
        )
    extra_in_test = [c for c in test.columns if c not in protected and c not in feature_cols]
    if extra_in_test:
        result.warnings.append(
            "columns present only in test.csv (ignored as features): " + ", ".join(extra_in_test)
        )

    n_folds = config.cv.n_folds
    if config.target in train.columns:
        if config.task == TaskType.BINARY_CLASSIFICATION:
            counts = train[config.target].value_counts()
            if len(counts) < 2:
                result.errors.append("binary target has a single class in train.csv")
            elif int(counts.min()) < n_folds:
                result.errors.append(
                    f"dataset too small for {n_folds} folds: minority class has "
                    f"{int(counts.min())} rows"
                )
            elif counts.min() / counts.max() < 0.1:
                result.warnings.append("imbalanced binary target detected")
        elif len(train) < n_folds * 2:
            result.errors.append(f"dataset too small for {n_folds} folds: {len(train)} rows")

    for col in feature_cols:
        if train[col].nunique(dropna=True) <= 1:
            result.warnings.append(f"constant column '{col}'")
    for col in id_like_feature_columns(train, config):
        if col in feature_cols:
            result.warnings.append(
                f"column '{col}' looks like a row identifier (unique per row); leakage risk"
            )
    return result
