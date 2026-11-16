"""Deterministic fingerprints for datasets, configs, and experiment specs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def schema_hash(df: pd.DataFrame) -> str:
    schema = {col: str(df[col].dtype) for col in df.columns}
    return canonical_json_hash(schema)


def dataset_fingerprints(data_dir: Path) -> dict[str, str]:
    return {
        name: sha256_file(data_dir / name)
        for name in ("train.csv", "test.csv", "sample_submission.csv")
        if (data_dir / name).exists()
    }


def experiment_fingerprint(spec: dict[str, Any]) -> str:
    return canonical_json_hash(spec)
