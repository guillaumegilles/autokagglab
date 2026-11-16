"""T037 — unit edge cases for fingerprints, metrics, and splits."""

from __future__ import annotations

import numpy as np
import pytest

from kaggle_agent.domain.config import CVStrategy
from kaggle_agent.domain.fingerprints import canonical_json_hash, experiment_fingerprint
from kaggle_agent.domain.metrics import UnsupportedMetricError, get_metric, supported_metrics
from kaggle_agent.domain.splits import make_folds


def test_canonical_json_hash_is_order_independent() -> None:
    assert canonical_json_hash({"a": 1, "b": 2}) == canonical_json_hash({"b": 2, "a": 1})


def test_experiment_fingerprint_changes_with_spec() -> None:
    base = {"model_family": "lightgbm", "params": {"n_estimators": 200}}
    assert experiment_fingerprint(base) != experiment_fingerprint(
        {**base, "params": {"n_estimators": 300}}
    )


def test_get_metric_directions() -> None:
    assert get_metric("roc_auc").direction == "max"
    assert get_metric("rmse").direction == "min"
    assert get_metric("log_loss").direction == "min"
    assert get_metric("r2").direction == "max"


def test_get_metric_unknown_lists_supported() -> None:
    with pytest.raises(UnsupportedMetricError, match="supported:.*roc_auc"):
        get_metric("f1")
    assert "roc_auc" in supported_metrics()


def test_folds_cover_all_rows_exactly_once() -> None:
    y = (np.random.default_rng(0).random(100) > 0.5).astype(int)
    folds = make_folds(100, y, CVStrategy.STRATIFIED_KFOLD, n_folds=5, seed=42)
    val = sorted(v for f in folds for v in f["val_idx"])  # type: ignore[arg-type]
    assert val == list(range(100))
    for f in folds:
        assert not set(f["train_idx"]) & set(f["val_idx"])  # type: ignore[arg-type]


def test_folds_deterministic() -> None:
    y = (np.random.default_rng(1).random(50) > 0.5).astype(int)
    a = make_folds(50, y, CVStrategy.KFOLD, 5, 42)
    b = make_folds(50, y, CVStrategy.KFOLD, 5, 42)
    assert a == b
    c = make_folds(50, y, CVStrategy.KFOLD, 5, 7)
    assert a != c
