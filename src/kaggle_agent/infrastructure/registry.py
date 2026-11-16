"""SQLite structured registry (SQLAlchemy 2) for competitions, profiles, runs,
experiments, and results. See specs/001-competition-baseline/data-model.md."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from kaggle_agent.domain.entities import (
    Competition,
    DatasetProfile,
    Experiment,
    ResearchRun,
    Result,
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS competitions (
    slug TEXT PRIMARY KEY,
    config_json TEXT NOT NULL,
    config_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dataset_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_slug TEXT NOT NULL REFERENCES competitions(slug),
    n_rows_train INTEGER NOT NULL,
    n_rows_test INTEGER NOT NULL,
    columns_json TEXT NOT NULL,
    target_distribution_json TEXT NOT NULL,
    id_unique INTEGER NOT NULL,
    leakage_warnings_json TEXT NOT NULL,
    fingerprints_json TEXT NOT NULL,
    schema_diff_json TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_runs (
    run_id TEXT PRIMARY KEY,
    competition_slug TEXT NOT NULL REFERENCES competitions(slug),
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    budgets_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    exit_code INTEGER,
    error TEXT
);
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES research_runs(run_id),
    parent_id TEXT,
    hypothesis TEXT NOT NULL,
    change_json TEXT NOT NULL,
    model_family TEXT NOT NULL,
    params_json TEXT NOT NULL,
    feature_set_version TEXT NOT NULL,
    experiment_fingerprint TEXT NOT NULL,
    cv_strategy TEXT NOT NULL,
    seed INTEGER NOT NULL,
    status TEXT NOT NULL,
    git_commit TEXT
);
CREATE TABLE IF NOT EXISTS results (
    experiment_id TEXT PRIMARY KEY REFERENCES experiments(experiment_id),
    metric_name TEXT NOT NULL,
    direction TEXT NOT NULL,
    fold_metrics_json TEXT NOT NULL,
    mean REAL NOT NULL,
    std REAL NOT NULL,
    runtime_seconds REAL NOT NULL,
    environment_json TEXT NOT NULL,
    mlflow_run_id TEXT,
    conclusion TEXT
);
"""


class Registry:
    def __init__(self, path: Path) -> None:
        self.engine: Engine = create_engine(f"sqlite:///{path}")
        with self.engine.begin() as conn:
            for statement in SCHEMA_SQL.split(";"):
                if statement.strip():
                    conn.execute(text(statement))

    def save_competition(self, competition: Competition) -> None:
        with Session(self.engine) as session:
            session.execute(
                text(
                    "INSERT OR REPLACE INTO competitions (slug, config_json, "
                    "config_fingerprint, created_at) VALUES (:slug, :cj, :cf, :ca)"
                ),
                {
                    "slug": competition.slug,
                    "cj": competition.config_json,
                    "cf": competition.config_fingerprint,
                    "ca": competition.created_at,
                },
            )
            session.commit()

    def save_profile(self, profile: DatasetProfile) -> None:
        with Session(self.engine) as session:
            session.execute(
                text(
                    "INSERT INTO dataset_profiles (competition_slug, n_rows_train, "
                    "n_rows_test, columns_json, target_distribution_json, id_unique, "
                    "leakage_warnings_json, fingerprints_json, schema_diff_json, created_at) "
                    "VALUES (:slug, :nrt, :nrtest, :cols, :td, :idu, :lw, :fp, :sd, :ca)"
                ),
                {
                    "slug": profile.competition_slug,
                    "nrt": profile.n_rows_train,
                    "nrtest": profile.n_rows_test,
                    "cols": json.dumps(profile.columns),
                    "td": json.dumps(profile.target_distribution),
                    "idu": int(profile.id_unique),
                    "lw": json.dumps(profile.leakage_warnings),
                    "fp": json.dumps(profile.fingerprints),
                    "sd": json.dumps(profile.schema_diff),
                    "ca": profile.created_at,
                },
            )
            session.commit()

    def create_run(self, run: ResearchRun) -> None:
        self._save_run(run)

    def update_run(self, run: ResearchRun) -> None:
        self._save_run(run)

    def _save_run(self, run: ResearchRun) -> None:
        with Session(self.engine) as session:
            session.execute(
                text(
                    "INSERT OR REPLACE INTO research_runs (run_id, competition_slug, kind, "
                    "status, budgets_json, started_at, finished_at, exit_code, error) "
                    "VALUES (:rid, :slug, :kind, :status, :b, :sa, :fa, :ec, :err)"
                ),
                {
                    "rid": run.run_id,
                    "slug": run.competition_slug,
                    "kind": run.kind,
                    "status": str(run.status),
                    "b": run.budgets_json,
                    "sa": run.started_at,
                    "fa": run.finished_at,
                    "ec": run.exit_code,
                    "err": run.error,
                },
            )
            session.commit()

    def save_experiment(self, experiment: Experiment) -> None:
        with Session(self.engine) as session:
            session.execute(
                text(
                    "INSERT OR REPLACE INTO experiments (experiment_id, run_id, parent_id, "
                    "hypothesis, change_json, model_family, params_json, feature_set_version, "
                    "experiment_fingerprint, cv_strategy, seed, status, git_commit) "
                    "VALUES (:eid, :rid, :pid, :h, :ch, :mf, :p, :fsv, :fp, :cv, :seed, :st, :gc)"
                ),
                {
                    "eid": experiment.experiment_id,
                    "rid": experiment.run_id,
                    "pid": experiment.parent_id,
                    "h": experiment.hypothesis,
                    "ch": experiment.change_json,
                    "mf": experiment.model_family,
                    "p": experiment.params_json,
                    "fsv": experiment.feature_set_version,
                    "fp": experiment.experiment_fingerprint,
                    "cv": experiment.cv_strategy,
                    "seed": experiment.seed,
                    "st": str(experiment.status),
                    "gc": experiment.git_commit,
                },
            )
            session.commit()

    def save_result(self, result: Result) -> None:
        with Session(self.engine) as session:
            session.execute(
                text(
                    "INSERT OR REPLACE INTO results (experiment_id, metric_name, direction, "
                    "fold_metrics_json, mean, std, runtime_seconds, environment_json, "
                    "mlflow_run_id, conclusion) "
                    "VALUES (:eid, :mn, :d, :fm, :m, :s, :rt, :env, :mr, :c)"
                ),
                {
                    "eid": result.experiment_id,
                    "mn": result.metric_name,
                    "d": result.direction,
                    "fm": json.dumps(result.fold_metrics),
                    "m": result.mean,
                    "s": result.std,
                    "rt": result.runtime_seconds,
                    "env": result.environment_json,
                    "mr": result.mlflow_run_id,
                    "c": result.conclusion,
                },
            )
            session.commit()

    def list_runs(self, slug: str) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.execute(
                text(
                    "SELECT run_id, kind, status, budgets_json, started_at, finished_at, "
                    "exit_code, error "
                    "FROM research_runs WHERE competition_slug = :slug ORDER BY started_at"
                ),
                {"slug": slug},
            ).all()
            return [dict(row._mapping) for row in rows]

    def list_experiments(self, run_id: str) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.execute(
                text("SELECT * FROM experiments WHERE run_id = :rid"),
                {"rid": run_id},
            ).all()
            return [dict(row._mapping) for row in rows]

    def latest_profile(self, slug: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.execute(
                text(
                    "SELECT * FROM dataset_profiles WHERE competition_slug = :slug "
                    "ORDER BY id DESC LIMIT 1"
                ),
                {"slug": slug},
            ).first()
            return dict(row._mapping) if row else None

    def latest_result(self, slug: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.execute(
                text(
                    "SELECT r.* FROM results r JOIN experiments e ON r.experiment_id = "
                    "e.experiment_id JOIN research_runs u ON e.run_id = u.run_id "
                    "WHERE u.competition_slug = :slug AND e.status = 'COMPLETED' "
                    "ORDER BY r.mean DESC LIMIT 1"
                ),
                {"slug": slug},
            ).first()
            return dict(row._mapping) if row else None
