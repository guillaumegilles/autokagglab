"""T023 — US2 acceptance tests: profile content (FR-006/FR-007) and
fingerprint stability (FR-004)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from kaggle_agent.cli.app import app

runner = CliRunner()


def _get_profile(root: Path) -> dict:
    registry = root / "registry.sqlite"
    assert registry.exists(), "validate must create the registry"
    with sqlite3.connect(registry) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM dataset_profiles WHERE competition_slug = ?", (root.name,)
        ).fetchone()
    assert row is not None, "validate must store a dataset profile"
    return dict(row)


def test_profile_content(classification_workspace: Path) -> None:
    result = runner.invoke(app, ["validate", str(classification_workspace)])
    assert result.exit_code == 0, result.output
    profile = _get_profile(classification_workspace)
    assert profile["n_rows_train"] == 400
    assert profile["n_rows_test"] == 120
    assert profile["id_unique"] == 1

    columns = json.loads(profile["columns_json"])
    names = {c["name"] for c in columns}
    assert {"id", "target", "num_0", "cat_a"} <= names
    for col in columns:
        assert {
            "name",
            "dtype",
            "missing",
            "n_unique",
            "is_constant",
            "is_likely_categorical",
        } <= set(col)
    by_name = {c["name"]: c for c in columns}
    assert by_name["cat_a"]["is_likely_categorical"] is True
    assert by_name["num_0"]["is_likely_categorical"] is False

    target_dist = json.loads(profile["target_distribution_json"])
    assert target_dist.get("type") == "classification"
    assert sum(target_dist["counts"].values()) == 400

    fingerprints = json.loads(profile["fingerprints_json"])
    assert set(fingerprints) >= {"train.csv", "test.csv", "sample_submission.csv"}
    assert all(len(v) == 64 for v in fingerprints.values())


def test_fingerprint_stable_across_reruns(classification_workspace: Path) -> None:
    assert runner.invoke(app, ["validate", str(classification_workspace)]).exit_code == 0
    first = json.loads(_get_profile(classification_workspace)["fingerprints_json"])
    assert runner.invoke(app, ["validate", str(classification_workspace)]).exit_code == 0
    with sqlite3.connect(classification_workspace / "registry.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT fingerprints_json FROM dataset_profiles WHERE competition_slug = ? ORDER BY id",
            (classification_workspace.name,),
        ).fetchall()
    second = json.loads(rows[-1]["fingerprints_json"])
    assert first == second


def test_fingerprint_changes_when_data_changes(classification_workspace: Path) -> None:
    assert runner.invoke(app, ["validate", str(classification_workspace)]).exit_code == 0
    before = json.loads(_get_profile(classification_workspace)["fingerprints_json"])
    train_path = classification_workspace / "data" / "train.csv"
    df = pd.read_csv(train_path)
    df.loc[0, df.columns[1]] = 999.0
    df.to_csv(train_path, index=False)
    assert runner.invoke(app, ["validate", str(classification_workspace)]).exit_code == 0
    with sqlite3.connect(classification_workspace / "registry.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT fingerprints_json FROM dataset_profiles WHERE competition_slug = ? ORDER BY id",
            (classification_workspace.name,),
        ).fetchall()
    after = json.loads(rows[-1]["fingerprints_json"])
    assert before["train.csv"] != after["train.csv"]
    assert before["test.csv"] == after["test.csv"]
