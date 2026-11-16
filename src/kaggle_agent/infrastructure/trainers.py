"""T028/T029 — Trainer protocol + deterministic LightGBM and CatBoost adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
import pandas as pd

DEFAULT_PARAMS: dict[str, dict[str, Any]] = {
    "lightgbm": {
        "n_estimators": 200,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "random_state": 42,
        "deterministic": True,
        "force_row_wise": True,
        "num_threads": 4,
        "verbose": -1,
    },
    "catboost": {
        "iterations": 200,
        "learning_rate": 0.05,
        "depth": 6,
        "random_seed": 42,
        "thread_count": 4,
        "verbose": 0,
    },
}


class Trainer(Protocol):
    def fit(self, X: pd.DataFrame, y: np.ndarray, cat_features: list[str]) -> None: ...
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...


class LightGBMTrainer:
    def __init__(self, params: dict[str, Any], binary: bool) -> None:
        import lightgbm as lgb

        self._binary = binary
        merged = {**DEFAULT_PARAMS["lightgbm"], **params}
        if binary:
            self._model = lgb.LGBMClassifier(**merged)
        else:
            self._model = lgb.LGBMRegressor(**merged)

    def fit(self, X: pd.DataFrame, y: np.ndarray, cat_features: list[str]) -> None:
        self._model.fit(X, y, categorical_feature=cat_features if cat_features else "auto")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._binary:
            proba = np.asarray(self._model.predict_proba(X), dtype=float)
            return proba[:, 1]
        return np.asarray(self._model.predict(X), dtype=float)


class CatBoostTrainer:
    def __init__(self, params: dict[str, Any], binary: bool) -> None:
        from catboost import CatBoostClassifier, CatBoostRegressor

        self._binary = binary
        merged = {**DEFAULT_PARAMS["catboost"], **params}
        cls = CatBoostClassifier if binary else CatBoostRegressor
        self._model = cls(**merged)

    def fit(self, X: pd.DataFrame, y: np.ndarray, cat_features: list[str]) -> None:
        self._model.fit(X, y, cat_features=cat_features or None)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._binary:
            proba = np.asarray(self._model.predict_proba(X), dtype=float)
            return proba[:, 1]
        return np.asarray(self._model.predict(X), dtype=float)


TRAINERS: dict[str, Callable[[dict[str, Any], bool], Trainer]] = {
    "lightgbm": LightGBMTrainer,
    "catboost": CatBoostTrainer,
}


def make_trainer(model_family: str, params: dict[str, Any], binary: bool) -> Trainer:
    try:
        cls = TRAINERS[model_family]
    except KeyError:
        raise ValueError(
            f"unsupported model family '{model_family}'; supported: {', '.join(sorted(TRAINERS))}"
        ) from None
    return cls(params, binary)
