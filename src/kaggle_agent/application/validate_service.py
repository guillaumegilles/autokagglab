"""T021 — CompetitionValidator: input contract checks (FR-001..FR-005).

Fails fast before any training; never modifies the input datasets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from pydantic import ValidationError

from kaggle_agent.application.workspace import REQUIRED_DATA_FILES, Workspace, WorkspaceError
from kaggle_agent.domain.config import CompetitionConfig
from kaggle_agent.domain.fingerprints import dataset_fingerprints
from kaggle_agent.domain.leakage import PreflightResult, preflight


@dataclass
class ValidationOutcome:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    config: CompetitionConfig | None = None
    fingerprints: dict[str, str] = field(default_factory=dict)
    train: pd.DataFrame | None = None
    test: pd.DataFrame | None = None
    sample: pd.DataFrame | None = None


class CompetitionValidator:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def validate(self) -> ValidationOutcome:
        outcome = ValidationOutcome(ok=False)

        try:
            config = self.workspace.load_config()
        except WorkspaceError as exc:
            outcome.errors.append(str(exc))
            return outcome
        except ValidationError as exc:
            outcome.errors.append(f"invalid competition config: {exc.errors(include_url=False)}")
            return outcome
        except Exception as exc:  # malformed YAML
            outcome.errors.append(f"invalid competition config: {exc}")
            return outcome
        outcome.config = config

        missing = [f for f in REQUIRED_DATA_FILES if not (self.workspace.data_dir / f).exists()]
        if missing:
            outcome.errors.append(
                f"missing required files in {self.workspace.data_dir}: {', '.join(missing)}"
            )
            return outcome
        try:
            train = pd.read_csv(self.workspace.data_dir / "train.csv")
            test = pd.read_csv(self.workspace.data_dir / "test.csv")
            sample = pd.read_csv(self.workspace.data_dir / "sample_submission.csv")
        except Exception as exc:
            outcome.errors.append(f"unreadable dataset file: {exc}")
            return outcome

        outcome.fingerprints = dataset_fingerprints(self.workspace.data_dir)
        pre: PreflightResult = preflight(train, test, config)
        outcome.errors.extend(pre.errors)
        outcome.warnings.extend(pre.warnings)

        if config.target in sample.columns:
            outcome.errors.append(
                "sample_submission.csv must not contain the target column (target leakage)"
            )
        missing_ids = [c for c in config.id_columns if c not in sample.columns]
        if missing_ids:
            outcome.errors.append(
                "sample_submission.csv schema mismatch: missing identifier columns: "
                + ", ".join(missing_ids)
            )
        for id_col in config.id_columns:
            if id_col in sample.columns and sample[id_col].duplicated().any():
                outcome.errors.append(
                    f"duplicate identifiers in sample_submission.csv column '{id_col}'"
                )
        if outcome.errors:
            return outcome

        outcome.train = train
        outcome.test = test
        outcome.sample = sample
        outcome.ok = True
        return outcome
