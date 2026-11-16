"""T032 — US4 acceptance test AT-005: a target-dependent transformation must
be fitted only on each fold's training rows; no validation target value may be
accessible during fitting."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from typer.testing import CliRunner

from kaggle_agent.cli.app import app
from kaggle_agent.domain.config import CVStrategy
from kaggle_agent.domain.splits import make_folds
from kaggle_agent.domain.transforms import FoldIsolatedPipeline, TargetEncoder

runner = CliRunner()


def _unique_target_frame(n: int = 200, seed: int = 0) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(
        {
            "id": np.arange(n),
            "cat": rng.choice(list("abcd"), size=n),
            "num": rng.normal(size=n),
        }
    )
    # unique target per row so fitted values identify exactly which rows were seen
    y = rng.random(n) + np.arange(n) / 1000.0
    return X, y


def test_at005_target_encoding_fitted_on_train_fold_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    X, y = _unique_target_frame()
    folds = make_folds(len(X), y, CVStrategy.KFOLD, n_folds=5, seed=42)

    seen: list[np.ndarray] = []
    original_fit = TargetEncoder.fit

    def spy_fit(self: TargetEncoder, X_fit: pd.DataFrame, y_fit: np.ndarray) -> TargetEncoder:
        seen.append(np.asarray(y_fit, dtype=float).copy())
        return original_fit(self, X_fit, y_fit)

    monkeypatch.setattr(TargetEncoder, "fit", spy_fit)

    for fold in folds:
        train_idx = np.asarray(fold["train_idx"], dtype=int)
        val_idx = np.asarray(fold["val_idx"], dtype=int)
        pipeline = FoldIsolatedPipeline(strategy="target_encoding", columns=["cat"])
        Xt = pipeline.fit_transform(X.iloc[train_idx], y[train_idx])
        assert not Xt.isna().any().any()
        pipeline.transform(X.iloc[val_idx])

    assert len(seen) == 5, "one fit per fold"
    all_val = np.concatenate([np.asarray(f["val_idx"], dtype=int) for f in folds])
    for fold, y_seen in zip(folds, seen):
        train_idx = np.asarray(fold["train_idx"], dtype=int)
        assert len(y_seen) == len(train_idx)
        # fitted targets are exactly the training fold's targets
        np.testing.assert_array_equal(np.sort(y_seen), np.sort(y[train_idx]))
        # no validation target value was ever seen during fitting
        val_targets = set(np.round(y[all_val], 6))
        assert not (set(np.round(y_seen, 6)) & val_targets - set(np.round(y[train_idx], 6)))


def test_baseline_with_target_encoding_keeps_fold_isolation(
    classification_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []
    original_fit = TargetEncoder.fit

    def spy_fit(self: TargetEncoder, X_fit: pd.DataFrame, y_fit: np.ndarray) -> TargetEncoder:
        seen.append(len(y_fit))
        return original_fit(self, X_fit, y_fit)

    monkeypatch.setattr(TargetEncoder, "fit", spy_fit)
    result = runner.invoke(app, ["baseline", str(classification_workspace), "--target-encoding"])
    assert result.exit_code == 0, result.output
    # 5 folds x 2 categorical columns (cat_a, cat_b) = 10 fold-isolated fits
    assert len(seen) == 10
    # each fit saw only a training fold (4/5 of 400 rows), never the full dataset
    assert all(size == 320 for size in seen)
