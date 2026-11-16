"""T030 — Baseline service: deterministic CV baseline with full recording
(FR-008..FR-011, FR-013; constitution I/II/VI)."""

from __future__ import annotations

import json
import math
import platform
import subprocess
import sys
import time
from importlib import metadata
from typing import Any

import numpy as np
import pandas as pd

from kaggle_agent.application.run_service import (
    EXIT_OK,
    EXIT_RUN_FAILURE,
    EXIT_VALIDATION_ERROR,
    new_entry_id,
    new_run_id,
    utc_now,
)
from kaggle_agent.application.validate_service import CompetitionValidator
from kaggle_agent.application.workspace import Workspace
from kaggle_agent.domain.config import TaskType
from kaggle_agent.domain.entities import (
    Experiment,
    ExperimentStatus,
    ResearchRun,
    Result,
    RunStatus,
)
from kaggle_agent.domain.fingerprints import experiment_fingerprint
from kaggle_agent.domain.leakage import id_like_feature_columns
from kaggle_agent.domain.metrics import get_metric
from kaggle_agent.domain.splits import make_folds
from kaggle_agent.domain.transforms import FoldIsolatedPipeline
from kaggle_agent.infrastructure.registry import Registry
from kaggle_agent.infrastructure.research_log import append_entry
from kaggle_agent.infrastructure.tracking import Tracker
from kaggle_agent.infrastructure.trainers import make_trainer

BASELINE_HYPOTHESIS = (
    "Baseline: default LightGBM under frozen 5-fold stratified CV establishes the reference score"
)


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return None


def _environment() -> dict[str, Any]:
    packages = {}
    for dist in ("pandas", "scikit-learn", "lightgbm", "catboost", "mlflow"):
        try:
            packages[dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            packages[dist] = "not-installed"
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
    }


def _prepare_features(
    train: pd.DataFrame, config: Any
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    protected = {config.target, *config.id_columns}
    # Constant columns and flagged leakage-risk columns are reported in the
    # profile and excluded from the baseline feature set (spec edge cases,
    # US4: never silently used as features).
    excluded = {c for c in train.columns if train[c].nunique(dropna=True) <= 1}
    excluded.update(id_like_feature_columns(train, config))
    X = train.drop(columns=[c for c in protected | excluded if c in train.columns]).copy()
    cat_features = [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]
    for col in cat_features:
        X[col] = X[col].astype("category")
    y = train[config.target].to_numpy()
    return X, y, cat_features


class BaselineService:
    def __init__(self, workspace: Workspace) -> None:
        self.ws = workspace

    def run(self, transform_strategy: str | None = None) -> int:
        outcome = CompetitionValidator(self.ws).validate()
        if not outcome.ok or outcome.config is None:
            return EXIT_VALIDATION_ERROR
        config = outcome.config
        registry = Registry(self.ws.registry_path)
        tracker = Tracker(self.ws)

        run = ResearchRun(
            run_id=new_run_id(),
            competition_slug=self.ws.slug,
            kind="baseline",
            status=RunStatus.RUNNING,
            budgets_json=json.dumps(config.budgets.model_dump(mode="json")),
            started_at=utc_now(),
        )
        registry.create_run(run)

        train = outcome.train
        assert train is not None
        X, y, cat_features = _prepare_features(train, config)
        folds = make_folds(len(train), y, config.cv.strategy, config.cv.n_folds, config.seed)
        run_dir = self.ws.run_dir(run.run_id)
        (run_dir / "artifacts" / "folds.json").write_text(json.dumps(folds))

        exp_id = self._next_experiment_id(registry)
        spec = {
            "change": {"type": "baseline"},
            "model_family": "lightgbm",
            "params": {},
            "cv_strategy": str(config.cv.strategy),
            "seed": config.seed,
            "feature_set_version": "v0",
        }
        experiment = Experiment(
            experiment_id=exp_id,
            run_id=run.run_id,
            parent_id=None,
            hypothesis=BASELINE_HYPOTHESIS,
            change_json=json.dumps(spec["change"]),
            model_family="lightgbm",
            params_json=json.dumps(spec["params"]),
            feature_set_version="v0",
            experiment_fingerprint=experiment_fingerprint(spec),
            cv_strategy=str(config.cv.strategy),
            seed=config.seed,
            status=ExperimentStatus.RUNNING,
            git_commit=_git_commit(),
        )
        registry.save_experiment(experiment)

        binary = config.task == TaskType.BINARY_CLASSIFICATION
        metric = get_metric(config.metric)
        hypothesis = {
            "statement": BASELINE_HYPOTHESIS,
            "expected_effect": {
                "metric": metric.name,
                "direction": "increase" if str(metric.direction) == "max" else "decrease",
                "minimum_change": 0.0,
            },
        }
        fold_metrics: list[dict[str, Any]] = []
        started = time.monotonic()
        try:
            for fold in folds:
                train_idx = np.asarray(fold["train_idx"], dtype=int)
                val_idx = np.asarray(fold["val_idx"], dtype=int)
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                if transform_strategy == "target_encoding" and cat_features:
                    # fold-isolated: encoder fitted on training rows only
                    pipeline = FoldIsolatedPipeline(
                        strategy="target_encoding", columns=cat_features
                    )
                    X_train = pipeline.fit_transform(X_train, y[train_idx])
                    X_val = pipeline.transform(X_val)
                    fold_cat_features: list[str] = []
                else:
                    fold_cat_features = cat_features
                trainer = make_trainer("lightgbm", {}, binary)
                trainer.fit(X_train, y[train_idx], fold_cat_features)
                preds = trainer.predict(X_val)
                if not np.all(np.isfinite(preds)):
                    raise ValueError("model produced NaN or infinite predictions")
                fold_metrics.append(
                    {"fold": fold["fold"], "value": metric.scorer(y[val_idx], preds)}
                )
            values = np.array([f["value"] for f in fold_metrics], dtype=float)
            mean = float(values.mean())
            std = float(values.std())
            if not math.isfinite(mean):
                raise ValueError("aggregate metric is not finite")
        except Exception as exc:
            runtime = time.monotonic() - started
            experiment.status = ExperimentStatus.FAILED
            registry.save_experiment(experiment)
            run.status = RunStatus.FAILED
            run.finished_at = utc_now()
            run.exit_code = EXIT_RUN_FAILURE
            run.error = f"{type(exc).__name__}: {exc}"
            registry.update_run(run)
            append_entry(
                self.ws.research_log_path,
                {
                    "entry_id": new_entry_id(),
                    "timestamp": utc_now(),
                    "run_id": run.run_id,
                    "type": "experiment",
                    "status": "FAILED",
                    "experiment_id": exp_id,
                    "hypothesis": hypothesis,
                    "observed": {"error": run.error, "runtime_seconds": runtime},
                    "conclusion": f"Baseline failed: {run.error}",
                },
            )
            return EXIT_RUN_FAILURE

        runtime = time.monotonic() - started

        conclusion = (
            f"Baseline completed: {config.metric} mean {mean:.6f} ± {std:.6f} "
            f"over {len(fold_metrics)} folds in {runtime:.1f}s"
        )
        result = Result(
            experiment_id=exp_id,
            metric_name=metric.name,
            direction=str(metric.direction),
            fold_metrics=fold_metrics,
            mean=mean,
            std=std,
            runtime_seconds=runtime,
            environment_json=json.dumps(_environment()),
            mlflow_run_id=None,
            conclusion=conclusion,
        )
        experiment.status = ExperimentStatus.COMPLETED
        registry.save_experiment(experiment)
        result.mlflow_run_id = tracker.start_run(f"{self.ws.slug}-{exp_id}")
        tracker.log_params(
            {"model_family": "lightgbm", "seed": config.seed, "n_folds": config.cv.n_folds}
        )
        tracker.log_metrics(
            {"mean": mean, "std": std, **{f"fold_{f['fold']}": f["value"] for f in fold_metrics}}
        )
        tracker.log_artifact(run_dir / "artifacts" / "folds.json")
        tracker.end_run("FINISHED")
        registry.save_result(result)

        run.status = RunStatus.COMPLETED
        run.finished_at = utc_now()
        run.exit_code = EXIT_OK
        registry.update_run(run)
        append_entry(
            self.ws.research_log_path,
            {
                "entry_id": new_entry_id(),
                "timestamp": utc_now(),
                "run_id": run.run_id,
                "type": "experiment",
                "status": "COMPLETED",
                "experiment_id": exp_id,
                "hypothesis": hypothesis,
                "observed": {
                    "metric": metric.name,
                    "mean": mean,
                    "std": std,
                    "fold_metrics": fold_metrics,
                    "runtime_seconds": runtime,
                },
                "conclusion": conclusion,
            },
        )
        return EXIT_OK

    def _next_experiment_id(self, registry: Registry) -> str:
        with registry.engine.connect() as conn:
            row = conn.execute(
                __import__("sqlalchemy").text(
                    "SELECT COUNT(*) FROM experiments WHERE run_id IN "
                    "(SELECT run_id FROM research_runs WHERE competition_slug = :slug)"
                ),
                {"slug": self.ws.slug},
            ).first()
        count = int(row[0]) if row else 0
        return f"exp-{count + 1:04d}"
