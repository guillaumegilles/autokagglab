"""T026 — US3 acceptance test AT-001: a valid baseline run on a binary
classification fixture produces folds, per-fold + aggregate metrics, a
registry record, an MLflow run, one JSONL entry, and exit code 0."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kaggle_agent.cli.app import app
from kaggle_agent.infrastructure.research_log import read_entries

runner = CliRunner()


def test_at001_baseline_classification(classification_workspace: Path) -> None:
    result = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert result.exit_code == 0, result.output

    with sqlite3.connect(classification_workspace / "registry.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        runs = conn.execute("SELECT * FROM research_runs WHERE kind = 'baseline'").fetchall()
        assert len(runs) == 1
        run = dict(runs[0])
        assert run["status"] == "COMPLETED"
        assert run["exit_code"] == 0

        experiments = conn.execute(
            "SELECT * FROM experiments WHERE run_id = ?", (run["run_id"],)
        ).fetchall()
        assert len(experiments) == 1
        exp = dict(experiments[0])
        assert exp["experiment_id"] == "exp-0001"
        assert exp["parent_id"] is None
        assert exp["status"] == "COMPLETED"
        assert exp["model_family"] == "lightgbm"
        assert "baseline" in exp["hypothesis"].lower()

        results = conn.execute(
            "SELECT * FROM results WHERE experiment_id = ?", (exp["experiment_id"],)
        ).fetchall()
        assert len(results) == 1
        res = dict(results[0])
        assert res["metric_name"] == "roc_auc"
        assert res["direction"] == "max"
        folds = json.loads(res["fold_metrics_json"])
        assert len(folds) == 5
        assert all(0.0 <= f["value"] <= 1.0 for f in folds)
        assert res["mean"] == json.loads(json.dumps(res["mean"]))  # finite float
        assert res["runtime_seconds"] > 0
        assert res["conclusion"]

    entries = read_entries(classification_workspace / "research_log.jsonl")
    assert len(entries) == 1
    entry = entries[0]
    assert entry["type"] == "experiment"
    assert entry["status"] == "COMPLETED"
    assert entry["experiment_id"] == "exp-0001"
    assert entry["hypothesis"]["statement"]
    assert entry["conclusion"]

    mlruns = classification_workspace / "mlruns"
    assert mlruns.exists() and any(mlruns.rglob("meta.yaml")), "MLflow run recorded"

    run_dir = classification_workspace / "runs" / run["run_id"]
    folds_artifact = run_dir / "artifacts" / "folds.json"
    assert folds_artifact.exists()
    persisted = json.loads(folds_artifact.read_text())
    assert len(persisted) == 5


def test_baseline_works_with_relative_path(
    classification_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Quickstart invokes the CLI with a relative workspace path; the run must
    still succeed (exit 0), not crash on URI conversion."""
    monkeypatch.chdir(classification_workspace.parent)
    result = runner.invoke(app, ["baseline", classification_workspace.name])
    assert result.exit_code == 0, result.output


def test_constant_and_id_like_columns_excluded_from_features(
    classification_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec edge cases: constant columns and leakage-risk ID-like columns are
    reported in the profile and excluded from the baseline feature set."""
    import numpy as np
    import pandas as pd

    import kaggle_agent.infrastructure.trainers as trainers_mod

    train_path = classification_workspace / "data" / "train.csv"
    test_path = classification_workspace / "data" / "test.csv"
    df = pd.read_csv(train_path)
    df["const_col"] = 1.0
    df["rowkey"] = [f"k{i}" for i in range(len(df))]
    df.to_csv(train_path, index=False)
    dt = pd.read_csv(test_path)
    dt["const_col"] = 1.0
    dt["rowkey"] = [f"t{i}" for i in range(len(dt))]
    dt.to_csv(test_path, index=False)

    seen_columns: list[set] = []
    original_fit = trainers_mod.LightGBMTrainer.fit

    def spy_fit(
        self: trainers_mod.LightGBMTrainer, X: pd.DataFrame, y: np.ndarray, cat: list
    ) -> None:
        seen_columns.append(set(X.columns))
        return original_fit(self, X, y, cat)

    monkeypatch.setattr(trainers_mod.LightGBMTrainer, "fit", spy_fit)
    result = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert result.exit_code == 0, result.output
    assert seen_columns, "trainer must have been fitted"
    for cols in seen_columns:
        assert "const_col" not in cols
        assert "rowkey" not in cols
        assert "id" not in cols and "target" not in cols
