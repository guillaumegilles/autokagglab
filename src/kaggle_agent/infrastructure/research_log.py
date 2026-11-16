"""Append-only JSONL research log. Entries are never rewritten; corrections are
new entries linked via parent_entry_id (constitution VI)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_KEYS = ("entry_id", "timestamp", "run_id", "type", "status")


class ResearchLogError(ValueError):
    pass


def append_entry(log_path: Path, entry: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in entry]
    if missing:
        raise ResearchLogError(f"research log entry missing keys: {', '.join(missing)}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, default=str) + "\n")


def read_entries(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries
