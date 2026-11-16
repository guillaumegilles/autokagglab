"""T018: validate example payloads against the JSON Schema contracts."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

CONTRACTS = Path(__file__).resolve().parents[2] / "specs" / "001-competition-baseline" / "contracts"


def load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def _registry() -> Registry:
    registry = Registry()
    for path in CONTRACTS.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(contents["$id"], Resource.from_contents(contents))
    return registry


def validate(instance: dict, schema_name: str) -> None:
    jsonschema.validate(instance, load(schema_name), registry=_registry())


def test_competition_config_schema_accepts_valid_payload() -> None:
    payload = {
        "name": "demo",
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
            "min_improvement": 0.001,
        },
    }
    validate(payload, "competition-config.schema.json")


def test_competition_config_schema_rejects_missing_budgets() -> None:
    payload = {
        "name": "demo",
        "task": "regression",
        "target": "target",
        "id_columns": ["id"],
        "metric": "rmse",
        "cv": {"strategy": "kfold", "n_folds": 5},
        "seed": 42,
        "budgets": {"max_experiments": 10},
    }
    try:
        validate(payload, "competition-config.schema.json")
    except jsonschema.ValidationError:
        return
    raise AssertionError("schema should reject incomplete budgets")


def test_experiment_schema_requires_hypothesis_and_change() -> None:
    validate(
        {
            "experiment_id": "exp-0001",
            "run_id": "123e4567-e89b-42d3-a456-426614174000",
            "hypothesis": {
                "statement": "Default baseline establishes reference score",
                "expected_effect": {
                    "metric": "roc_auc",
                    "direction": "increase",
                    "minimum_change": 0.0,
                },
            },
            "change": {"type": "baseline"},
            "model_family": "lightgbm",
            "params": {"n_estimators": 200},
        },
        "experiment.schema.json",
    )


def test_result_schema() -> None:
    validate(
        {
            "experiment_id": "exp-0001",
            "metric_name": "roc_auc",
            "direction": "max",
            "fold_metrics": [{"fold": 0, "value": 0.8}, {"fold": 1, "value": 0.81}],
            "mean": 0.805,
            "std": 0.005,
            "runtime_seconds": 12.5,
        },
        "result.schema.json",
    )


def test_research_entry_schema() -> None:
    validate(
        {
            "entry_id": "123e4567-e89b-42d3-a456-426614174000",
            "timestamp": "2026-11-16T12:00:00+00:00",
            "run_id": "123e4567-e89b-42d3-a456-426614174001",
            "type": "experiment",
            "status": "COMPLETED",
        },
        "research-entry.schema.json",
    )
