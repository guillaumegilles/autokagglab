"""T027 — US3 acceptance test AT-002: rerunning a baseline with unchanged
inputs reproduces the aggregate metric within 0.000001 on identical folds.
Also covers regression KFold and the NaN-metric failure path (exit 3)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from kaggle_agent.cli.app import app

runner = CliRunner()


def _results(root: Path) -> list[dict]:
    with sqlite3.connect(root / "registry.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT r.mean, r.std, r.fold_metrics_json FROM results r "
            "JOIN experiments e ON r.experiment_id = e.experiment_id "
            "JOIN research_runs u ON e.run_id = u.run_id WHERE u.kind = 'baseline'"
        ).fetchall()
    return [dict(r) for r in rows]


def test_at002_deterministic_rerun(classification_workspace: Path) -> None:
    first = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert first.exit_code == 0, first.output
    second = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert second.exit_code == 0, second.output

    results = _results(classification_workspace)
    assert len(results) == 2
    assert abs(results[0]["mean"] - results[1]["mean"]) <= 0.000001
    assert json.loads(results[0]["fold_metrics_json"]) == json.loads(
        results[1]["fold_metrics_json"]
    )


def test_regression_baseline_uses_kfold(
    classification_workspace: Path, regression_workspace: Path
) -> None:
    result = runner.invoke(app, ["baseline", str(regression_workspace)])
    assert result.exit_code == 0, result.output
    results = _results(regression_workspace)
    assert len(results) == 1
    assert results[0]["mean"] >= 0  # rmse is non-negative
    folds = json.loads(results[0]["fold_metrics_json"])
    assert len(folds) == 5


def test_nan_metric_fails_run_with_exit_3(
    classification_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import kaggle_agent.infrastructure.trainers as trainers_mod

    class BrokenTrainer(trainers_mod.LightGBMTrainer):
        def predict(self, X: object) -> np.ndarray:
            return np.full(len(X), np.nan)  # type: ignore[arg-type]

    monkeypatch.setitem(trainers_mod.TRAINERS, "lightgbm", BrokenTrainer)
    result = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert result.exit_code == 3
    with sqlite3.connect(classification_workspace / "registry.sqlite") as conn:
        row = conn.execute(
            "SELECT status, exit_code FROM research_runs WHERE kind = 'baseline'"
        ).fetchone()
    assert row == ("FAILED", 3)


def test_nonfinite_aggregate_metric_fails_run_with_exit_3(
    classification_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec edge case: NaN/non-finite aggregate metric -> run FAILED, exit 3,
    and a FAILED research-log entry that still validates against the contract."""
    import jsonschema
    from referencing import Registry, Resource

    import kaggle_agent.application.baseline_service as baseline_mod
    from kaggle_agent.domain.metrics import Direction, MetricSpec
    from kaggle_agent.infrastructure.research_log import read_entries

    contracts = (
        Path(__file__).resolve().parents[2] / "specs" / "001-competition-baseline" / "contracts"
    )

    def nan_scorer(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float("nan")

    monkeypatch.setattr(
        baseline_mod,
        "get_metric",
        lambda name: MetricSpec(name, Direction.MAX, nan_scorer),
    )
    result = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert result.exit_code == 3
    with sqlite3.connect(classification_workspace / "registry.sqlite") as conn:
        row = conn.execute(
            "SELECT status, exit_code FROM research_runs WHERE kind = 'baseline'"
        ).fetchone()
    assert row == ("FAILED", 3)
    entries = read_entries(classification_workspace / "research_log.jsonl")
    assert len(entries) == 1
    assert entries[0]["status"] == "FAILED"
    assert entries[0]["conclusion"]
    registry = Registry()
    for path in contracts.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(contents["$id"], Resource.from_contents(contents))
    schema = json.loads((contracts / "research-entry.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(entries[0], schema, registry=registry)
