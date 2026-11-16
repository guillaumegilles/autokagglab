"""T035 — produced artifacts must validate against the JSON Schema contracts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import jsonschema
from referencing import Registry, Resource
from typer.testing import CliRunner

from kaggle_agent.cli.app import app
from kaggle_agent.infrastructure.research_log import read_entries

CONTRACTS = Path(__file__).resolve().parents[2] / "specs" / "001-competition-baseline" / "contracts"

runner = CliRunner()


def _registry() -> Registry:
    registry = Registry()
    for path in CONTRACTS.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(contents["$id"], Resource.from_contents(contents))
    return registry


def _schema(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def test_baseline_artifacts_match_contracts(classification_workspace: Path) -> None:
    result = runner.invoke(app, ["baseline", str(classification_workspace)])
    assert result.exit_code == 0, result.output

    with sqlite3.connect(classification_workspace / "registry.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        exp = dict(
            conn.execute("SELECT * FROM experiments LIMIT 1").fetchone()  # type: ignore[arg-type]
        )
        res = dict(
            conn.execute("SELECT * FROM results LIMIT 1").fetchone()  # type: ignore[arg-type]
        )

    experiment_payload = {
        "experiment_id": exp["experiment_id"],
        "run_id": exp["run_id"],
        "parent_id": exp["parent_id"],
        "hypothesis": {
            "statement": exp["hypothesis"],
            "expected_effect": {
                "metric": res["metric_name"],
                "direction": "increase" if res["direction"] == "max" else "decrease",
                "minimum_change": 0.0,
            },
        },
        "change": json.loads(exp["change_json"]),
        "model_family": exp["model_family"],
        "params": json.loads(exp["params_json"]),
        "status": exp["status"],
    }
    jsonschema.validate(experiment_payload, _schema("experiment.schema.json"), registry=_registry())

    result_payload = {
        "experiment_id": res["experiment_id"],
        "metric_name": res["metric_name"],
        "direction": res["direction"],
        "fold_metrics": json.loads(res["fold_metrics_json"]),
        "mean": res["mean"],
        "std": res["std"],
        "runtime_seconds": res["runtime_seconds"],
        "environment": json.loads(res["environment_json"]),
        "mlflow_run_id": res["mlflow_run_id"],
        "conclusion": res["conclusion"],
    }
    jsonschema.validate(result_payload, _schema("result.schema.json"), registry=_registry())

    entries = read_entries(classification_workspace / "research_log.jsonl")
    assert len(entries) == 1
    jsonschema.validate(entries[0], _schema("research-entry.schema.json"), registry=_registry())
