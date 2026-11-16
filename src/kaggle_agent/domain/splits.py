"""Deterministic cross-validation split generation.

Default: 5 folds; StratifiedKFold for binary classification, KFold for
regression; seed from config. Fold assignments are plain index lists so they
can be persisted per run and reused identically by later experiments.
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import KFold, StratifiedKFold

from kaggle_agent.domain.config import CVStrategy


def make_folds(
    n_rows: int,
    y: np.ndarray,
    strategy: CVStrategy,
    n_folds: int,
    seed: int,
) -> list[dict[str, object]]:
    """Return one entry per fold: {fold, train_idx, val_idx}."""
    folds: list[dict[str, object]] = []
    if strategy == CVStrategy.STRATIFIED_KFOLD:
        splitter = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
        splits = splitter.split(np.zeros(n_rows), y)
    else:
        splitter = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
        splits = splitter.split(np.zeros(n_rows))
    for i, (train_idx, val_idx) in enumerate(splits):
        folds.append(
            {
                "fold": i,
                "train_idx": [int(v) for v in train_idx],
                "val_idx": [int(v) for v in val_idx],
            }
        )
    return folds
