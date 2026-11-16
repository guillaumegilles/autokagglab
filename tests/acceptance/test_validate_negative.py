"""T019 — US1 acceptance tests: AT-003, AT-004, and the spec's edge cases.

Every invalid workspace must be rejected before training with a specific
error message, exit code 2, and no recorded run.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from typer.testing import CliRunner

from kaggle_agent.cli.app import app

runner = CliRunner()


def _write_workspace(
    root: Path,
    train: pd.DataFrame | None,
    test: pd.DataFrame | None,
    config: dict | None = None,
    sample: pd.DataFrame | None = None,
) -> Path:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    if train is not None:
        train.to_csv(data / "train.csv", index=False)
    if test is not None:
        test.to_csv(data / "test.csv", index=False)
    if sample is None and test is not None:
        sample = pd.DataFrame({"id": test["id"], "prediction": 0.0})
    if sample is not None:
        sample.to_csv(data / "sample_submission.csv", index=False)
    base = {
        "name": root.name,
        "task": "binary-classification",
        "target": "target",
        "id_columns": ["id"],
        "metric": "roc_auc",
        "cv": {"strategy": "stratified-kfold", "n_folds": 5},
        "seed": 42,
        "budgets": {
            "max_experiments": 10,
            "experiment_timeout_seconds": 1200,
            "run_timeout_seconds": 10800,
            "max_consecutive_failures": 3,
        },
    }
    if config:
        base.update(config)
    (root / "competition.yaml").write_text(yaml.safe_dump(base), encoding="utf-8")
    return root


def _classification_df(n: int = 200, seed: int = 0, with_target: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(
        {
            "id": np.arange(1000, 1000 + n),
            "f1": rng.normal(size=n),
            "f2": rng.normal(size=n),
        }
    )
    if with_target:
        df["target"] = (rng.random(n) > 0.5).astype(int)
    return df


def _assert_no_run_recorded(root: Path) -> None:
    log = root / "research_log.jsonl"
    assert not log.exists() or log.read_text().strip() == "", "no log entries on failed validation"
    registry = root / "registry.sqlite"
    if registry.exists():
        with sqlite3.connect(registry) as conn:
            count = conn.execute("SELECT COUNT(*) FROM research_runs").fetchone()[0]
        assert count == 0, "no run rows on failed validation"


def test_missing_files_rejected(tmp_path: Path) -> None:
    ws = _write_workspace(tmp_path / "ws", train=None, test=None)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "missing required files" in result.output
    _assert_no_run_recorded(ws)


def test_at003_missing_target_rejected(tmp_path: Path) -> None:
    train = _classification_df(with_target=False)
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "missing target column 'target'" in result.output
    _assert_no_run_recorded(ws)


def test_duplicate_identifiers_rejected(tmp_path: Path) -> None:
    train = _classification_df()
    train.loc[1, "id"] = train.loc[0, "id"]
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "duplicate identifiers" in result.output
    _assert_no_run_recorded(ws)


def test_at004_schema_mismatch_rejected(tmp_path: Path) -> None:
    train = _classification_df()
    train["extra_feature"] = 1.0
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "schema mismatch" in result.output
    assert "extra_feature" in result.output
    _assert_no_run_recorded(ws)


def test_unsupported_metric_rejected(tmp_path: Path) -> None:
    train = _classification_df()
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test, config={"metric": "f1"})
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "unsupported metric" in result.output
    assert "roc_auc" in result.output  # lists supported values
    _assert_no_run_recorded(ws)


def test_too_small_dataset_rejected(tmp_path: Path) -> None:
    train = _classification_df(n=8)  # minority class < 5 folds
    test = _classification_df(n=5, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "too small" in result.output
    _assert_no_run_recorded(ws)


def test_sample_submission_with_target_rejected(tmp_path: Path) -> None:
    train = _classification_df()
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test)
    sample = pd.DataFrame({"id": test["id"], "target": 0, "prediction": 0.0})
    sample.to_csv(ws / "data" / "sample_submission.csv", index=False)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "must not contain the target column" in result.output
    _assert_no_run_recorded(ws)


def test_sample_submission_missing_id_column_rejected(tmp_path: Path) -> None:
    train = _classification_df()
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test)
    pd.DataFrame({"prediction": [0.0]}).to_csv(ws / "data" / "sample_submission.csv", index=False)
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "missing identifier columns" in result.output
    _assert_no_run_recorded(ws)


def test_target_listed_as_id_column_rejected(tmp_path: Path) -> None:
    train = _classification_df()
    test = _classification_df(n=50, seed=1, with_target=False)
    ws = _write_workspace(tmp_path / "ws", train, test, config={"id_columns": ["id", "target"]})
    result = runner.invoke(app, ["validate", str(ws)])
    assert result.exit_code == 2
    assert "target leakage" in result.output
    _assert_no_run_recorded(ws)


def test_config_override_option_rejects_broken_config(
    classification_workspace: Path, tmp_path: Path
) -> None:
    """Quickstart: validate <ws> --config broken.yaml -> exit 2, specific error,
    no run recorded."""
    broken = tmp_path / "broken.yaml"
    config = yaml.safe_load((classification_workspace / "competition.yaml").read_text())
    config["target"] = "nonexistent"
    broken.write_text(yaml.safe_dump(config))
    result = runner.invoke(
        app, ["validate", str(classification_workspace), "--config", str(broken)]
    )
    assert result.exit_code == 2
    assert "missing target column 'nonexistent'" in result.output
    _assert_no_run_recorded(classification_workspace)


def test_valid_workspace_passes(classification_workspace: Path) -> None:
    result = runner.invoke(app, ["validate", str(classification_workspace)])
    assert result.exit_code == 0, result.output
