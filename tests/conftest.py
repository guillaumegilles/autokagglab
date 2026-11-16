"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.make_fixture import build_classification, build_regression


@pytest.fixture()
def classification_workspace(tmp_path: Path) -> Path:
    out = tmp_path / "demo-classification"
    build_classification(out)
    return out


@pytest.fixture()
def regression_workspace(tmp_path: Path) -> Path:
    out = tmp_path / "demo-regression"
    build_regression(out)
    return out
