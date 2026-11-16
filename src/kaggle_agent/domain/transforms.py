"""T033 — Fold-isolated transform pipeline.

Target-derived transformations MUST be fitted inside each training fold only
(constitution III, AT-005). The pipeline is fit on the training split and
applied to the validation split; validation targets are never seen during
fitting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class TargetEncoder:
    """Per-category target mean with global-mean fallback."""

    def __init__(self) -> None:
        self.mapping_: dict[str, float] = {}
        self.global_mean_: float = 0.0

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> TargetEncoder:
        self.global_mean_ = float(np.mean(y))
        df = pd.DataFrame({"cat": X.iloc[:, 0], "y": np.asarray(y, dtype=float)})
        self.mapping_ = {str(k): float(v) for k, v in df.groupby("cat")["y"].mean().items()}
        return self

    def transform(self, X: pd.DataFrame) -> pd.Series:
        col = X.iloc[:, 0]
        return col.map(self.mapping_).fillna(self.global_mean_).astype(float)


class FoldIsolatedPipeline:
    """Applies the configured strategy, fitted only on the rows it is given."""

    def __init__(self, strategy: str, columns: list[str]) -> None:
        if strategy != "target_encoding":
            raise ValueError(f"unknown transform strategy '{strategy}'")
        self.strategy = strategy
        self.columns = columns
        self._encoders: dict[str, TargetEncoder] = {}

    def fit_transform(self, X_train: pd.DataFrame, y_train: np.ndarray) -> pd.DataFrame:
        X = X_train.copy()
        for col in self.columns:
            encoder = TargetEncoder()
            encoder.fit(X[[col]], y_train)
            self._encoders[col] = encoder
            X[col] = encoder.transform(X[[col]])
        return X

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col in self.columns:
            X[col] = self._encoders[col].transform(X[[col]])
        return X
