"""Metric registry: every supported metric has an explicit optimization direction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from sklearn.metrics import (
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)


class Direction(StrEnum):
    MAX = "max"
    MIN = "min"


class UnsupportedMetricError(ValueError):
    pass


@dataclass(frozen=True)
class MetricSpec:
    name: str
    direction: Direction
    scorer: Callable[[np.ndarray, np.ndarray], float]


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


METRICS: dict[str, MetricSpec] = {
    "roc_auc": MetricSpec("roc_auc", Direction.MAX, lambda y, p: float(roc_auc_score(y, p))),
    "log_loss": MetricSpec("log_loss", Direction.MIN, lambda y, p: float(log_loss(y, p))),
    "rmse": MetricSpec("rmse", Direction.MIN, _rmse),
    "mae": MetricSpec("mae", Direction.MIN, lambda y, p: float(mean_absolute_error(y, p))),
    "r2": MetricSpec("r2", Direction.MAX, lambda y, p: float(r2_score(y, p))),
}


def supported_metrics() -> list[str]:
    return sorted(METRICS)


def get_metric(name: str) -> MetricSpec:
    try:
        return METRICS[name]
    except KeyError:
        raise UnsupportedMetricError(
            f"unsupported metric '{name}'; supported: {', '.join(supported_metrics())}"
        ) from None
