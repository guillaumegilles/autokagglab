"""T020 — US1 unit tests for config validation and preflight."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kaggle_agent.domain.config import Budgets, CompetitionConfig, CVConfig
from kaggle_agent.domain.leakage import preflight


def _config(**overrides: object) -> CompetitionConfig:
    base: dict[str, object] = {
        "name": "demo",
        "task": "binary-classification",
        "target": "target",
        "id_columns": ["id"],
        "metric": "roc_auc",
        "cv": CVConfig(strategy="stratified-kfold", n_folds=5),
        "seed": 42,
        "budgets": Budgets(),
    }
    base.update(overrides)
    return CompetitionConfig.model_validate(base)


def test_unsupported_metric_lists_supported() -> None:
    with pytest.raises(ValueError, match="unsupported metric 'f1'.*roc_auc"):
        _config(metric="f1")


def test_metric_task_mismatch_rejected() -> None:
    with pytest.raises(ValueError, match="not supported for regression"):
        _config(task="regression", metric="roc_auc", cv=CVConfig(strategy="kfold"))


def test_duplicate_id_columns_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        _config(id_columns=["id", "id"])


def test_preflight_ok() -> None:
    rng = np.random.default_rng(0)
    train = pd.DataFrame({"id": range(100), "f": rng.normal(size=100).round(1)})
    train["target"] = (rng.random(100) > 0.5).astype(int)
    test = pd.DataFrame({"id": range(100, 150), "f": rng.normal(size=50).round(1)})
    result = preflight(train, test, _config())
    assert result.ok
    assert result.warnings == []


def test_preflight_constant_column_warns_not_blocks() -> None:
    rng = np.random.default_rng(0)
    train = pd.DataFrame({"id": range(100), "const": 1.0, "f": rng.normal(size=100)})
    train["target"] = (rng.random(100) > 0.5).astype(int)
    test = pd.DataFrame({"id": range(100, 150), "const": 1.0, "f": rng.normal(size=50)})
    result = preflight(train, test, _config())
    assert result.ok
    assert any("constant column 'const'" in w for w in result.warnings)


def test_preflight_id_like_column_warns() -> None:
    rng = np.random.default_rng(0)
    train = pd.DataFrame({"id": range(100), "rowkey": [f"k{i}" for i in range(100)]})
    train["target"] = (rng.random(100) > 0.5).astype(int)
    test = pd.DataFrame({"id": range(100, 150), "rowkey": [f"k{i}" for i in range(100, 150)]})
    result = preflight(train, test, _config())
    assert result.ok
    assert any("rowkey" in w and "leakage risk" in w for w in result.warnings)


def test_preflight_imbalanced_target_warns() -> None:
    train = pd.DataFrame({"id": range(1000), "f": np.zeros(1000)})
    train["target"] = [0] * 990 + [1] * 10
    test = pd.DataFrame({"id": range(1000, 1100), "f": np.zeros(100)})
    result = preflight(train, test, _config())
    assert result.ok
    assert any("imbalanced" in w for w in result.warnings)
