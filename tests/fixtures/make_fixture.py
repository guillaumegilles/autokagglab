"""Synthetic competition fixture generator.

Usage:
    python -m tests.fixtures.make_fixture --out competitions/demo-classification \
        --task binary-classification
    python -m tests.fixtures.make_fixture --out competitions/demo-regression --task regression
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.datasets import make_classification, make_regression


def build_classification(out: Path, seed: int = 42) -> None:
    X, y = make_classification(
        n_samples=400,
        n_features=8,
        n_informative=5,
        n_redundant=1,
        n_classes=2,
        weights=[0.7, 0.3],
        flip_y=0.02,
        random_state=seed,
    )
    cols = [f"num_{i}" for i in range(6)] + ["cat_a", "cat_b"]
    df = pd.DataFrame(X[:, :6], columns=cols[:6])
    df["cat_a"] = np.array(["x", "y", "z"])[np.random.default_rng(seed).integers(0, 3, len(df))]
    df["cat_b"] = np.array(["p", "q"])[np.random.default_rng(seed + 1).integers(0, 2, len(df))]
    df["id"] = np.arange(1000, 1000 + len(df))
    df["target"] = y

    n_test = 120
    Xt, _ = make_classification(
        n_samples=n_test,
        n_features=8,
        n_informative=5,
        n_redundant=1,
        n_classes=2,
        random_state=seed + 2,
    )
    test = pd.DataFrame(Xt[:, :6], columns=cols[:6])
    test["cat_a"] = np.array(["x", "y", "z"])[
        np.random.default_rng(seed + 3).integers(0, 3, n_test)
    ]
    test["cat_b"] = np.array(["p", "q"])[np.random.default_rng(seed + 4).integers(0, 2, n_test)]
    test["id"] = np.arange(2000, 2000 + n_test)

    write_workspace(out, df, test, task="binary-classification", target="target", metric="roc_auc")


def build_regression(out: Path, seed: int = 42) -> None:
    X, y = make_regression(
        n_samples=400, n_features=6, n_informative=4, noise=5.0, random_state=seed
    )
    df = pd.DataFrame(X, columns=[f"num_{i}" for i in range(6)])
    df["id"] = np.arange(1000, 1000 + len(df))
    df["target"] = y

    Xt, _ = make_regression(
        n_samples=120, n_features=6, n_informative=4, noise=5.0, random_state=seed + 2
    )
    test = pd.DataFrame(Xt, columns=[f"num_{i}" for i in range(6)])
    test["id"] = np.arange(2000, 2000 + len(test))

    write_workspace(out, df, test, task="regression", target="target", metric="rmse")


def write_workspace(
    out: Path, train: pd.DataFrame, test: pd.DataFrame, task: str, target: str, metric: str
) -> None:
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    train.to_csv(data / "train.csv", index=False)
    test.to_csv(data / "test.csv", index=False)
    pd.DataFrame({"id": test["id"], "prediction": 0.0}).to_csv(
        data / "sample_submission.csv", index=False
    )
    config = {
        "name": out.name,
        "task": task,
        "target": target,
        "id_columns": ["id"],
        "metric": metric,
        "cv": {
            "strategy": "stratified-kfold" if task == "binary-classification" else "kfold",
            "n_folds": 5,
        },
        "seed": 42,
        "budgets": {
            "max_experiments": 10,
            "experiment_timeout_seconds": 1200,
            "run_timeout_seconds": 10800,
            "max_consecutive_failures": 3,
            "min_improvement": 0.001,
        },
    }
    (out / "competition.yaml").write_text(yaml.safe_dump(config, sort_keys=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--task", choices=["binary-classification", "regression"], required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.task == "binary-classification":
        build_classification(args.out, args.seed)
    else:
        build_regression(args.out, args.seed)
    print(f"fixture written to {args.out}")


if __name__ == "__main__":
    main()
