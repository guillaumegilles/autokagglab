"""Competition workspace layout and loading.

Layout: competitions/<slug>/{competition.yaml, data/, runs/<run-id>/artifacts/,
mlruns/, research_log.jsonl, registry.sqlite}. Dataset files are read-only
during runs: nothing in this module ever writes under data/.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from kaggle_agent.domain.config import CompetitionConfig

REQUIRED_DATA_FILES = ("train.csv", "test.csv", "sample_submission.csv")


class WorkspaceError(Exception):
    pass


class Workspace:
    def __init__(self, root: Path, config_override: Path | None = None) -> None:
        self.root = root.expanduser().resolve()
        self.slug = self.root.name
        self._config_override = (
            config_override.expanduser().resolve() if config_override is not None else None
        )

    @property
    def config_path(self) -> Path:
        if self._config_override is not None:
            return self._config_override
        return self.root / "competition.yaml"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def runs_dir(self) -> Path:
        return self.root / "runs"

    @property
    def registry_path(self) -> Path:
        return self.root / "registry.sqlite"

    @property
    def research_log_path(self) -> Path:
        return self.root / "research_log.jsonl"

    @property
    def mlruns_dir(self) -> Path:
        return self.root / "mlruns"

    def run_dir(self, run_id: str) -> Path:
        path = self.runs_dir / run_id
        path.mkdir(parents=True, exist_ok=True)
        (path / "artifacts").mkdir(exist_ok=True)
        return path

    def load_config(self) -> CompetitionConfig:
        if not self.config_path.exists():
            raise WorkspaceError(f"missing competition config: {self.config_path}")
        return CompetitionConfig.load(self.config_path)

    def load_datasets(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        missing = [f for f in REQUIRED_DATA_FILES if not (self.data_dir / f).exists()]
        if missing:
            raise WorkspaceError(f"missing required files in {self.data_dir}: {', '.join(missing)}")
        train = pd.read_csv(self.data_dir / "train.csv")
        test = pd.read_csv(self.data_dir / "test.csv")
        sample = pd.read_csv(self.data_dir / "sample_submission.csv")
        return train, test, sample


def init_workspace(root: Path, config: CompetitionConfig) -> Workspace:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(exist_ok=True)
    (root / "runs").mkdir(exist_ok=True)
    if not (root / "competition.yaml").exists():
        (root / "competition.yaml").write_text(
            yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
        )
    return Workspace(root)


def load_workspace(root: Path) -> Workspace:
    if not root.is_dir():
        raise WorkspaceError(f"workspace not found: {root}")
    ws = Workspace(root)
    ws.load_config()  # raises if missing/invalid
    return ws
