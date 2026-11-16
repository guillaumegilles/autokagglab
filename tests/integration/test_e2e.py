"""T036 — end-to-end: init → validate → baseline → status on synthetic
fixtures, for both classification and regression."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from kaggle_agent.cli.app import app

runner = CliRunner()


def test_e2e_classification(tmp_path: Path) -> None:
    ws = tmp_path / "e2e-clf"
    assert runner.invoke(app, ["init", str(ws), "--task", "binary-classification"]).exit_code == 0
    # drop fixture data into the initialized workspace
    from tests.fixtures.make_fixture import build_classification

    build_classification(ws)
    assert runner.invoke(app, ["validate", str(ws)]).exit_code == 0
    assert runner.invoke(app, ["baseline", str(ws)]).exit_code == 0
    status = runner.invoke(app, ["status", str(ws)])
    assert status.exit_code == 0
    assert "incumbent: exp-0001 roc_auc=" in status.output


def test_e2e_regression(tmp_path: Path) -> None:
    ws = tmp_path / "e2e-reg"
    assert (
        runner.invoke(app, ["init", str(ws), "--task", "regression", "--metric", "rmse"]).exit_code
        == 0
    )
    from tests.fixtures.make_fixture import build_regression

    build_regression(ws)
    assert runner.invoke(app, ["validate", str(ws)]).exit_code == 0
    assert runner.invoke(app, ["baseline", str(ws)]).exit_code == 0
    status = runner.invoke(app, ["status", str(ws)])
    assert status.exit_code == 0
    assert "incumbent: exp-0001 rmse=" in status.output
