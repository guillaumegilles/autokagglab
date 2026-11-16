# Quickstart: Competition Baseline

End-to-end validation that the harness works standalone, offline, with no LLM
or agent runtime.

## Prerequisites

- Python 3.12
- From a clean checkout: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e '.[dev]'`
  (or with pip: `pip install -e '.[dev]'`)
- No network access, credentials, or GPU required at runtime

## 1. Generate a synthetic competition fixture

```bash
python -m tests.fixtures.make_fixture --out competitions/demo-classification --task binary-classification
python -m tests.fixtures.make_fixture --out competitions/demo-regression --task regression
```

Each fixture creates `competition.yaml`, `data/train.csv`, `data/test.csv`,
`data/sample_submission.csv` (see `contracts/competition-config.schema.json`).

## 2. Validate the competition

```bash
kaggle-agent validate competitions/demo-classification
```

Expected: exit code 0; a dataset profile is printed (shape, dtypes, missing
values, target distribution, leakage warnings) and stored; fingerprints of
`train.csv`/`test.csv`/`sample_submission.csv` are recorded.

Negative check:

```bash
kaggle-agent validate competitions/demo-classification --config broken.yaml
```

Expected: exit code 2, a specific error (e.g., missing target column), and no
run recorded.

## 3. Run the baseline

```bash
kaggle-agent baseline competitions/demo-classification
```

Expected: exit code 0; 5 stratified folds executed; per-fold and aggregate ROC
AUC printed; a structured run record, an MLflow run under `mlruns/`, and one
appended entry in `competitions/demo-classification/research_log.jsonl`
(conforming to `contracts/research-entry.schema.json`).

## 4. Check status

```bash
kaggle-agent status competitions/demo-classification
```

Expected: exit code 0; lists runs, incumbent experiment, metric, and budgets.

## 5. Verify determinism

```bash
kaggle-agent baseline competitions/demo-classification --run-id rerun-1
```

Expected: same fold assignments and aggregate metric within 0.000001 of the
first baseline (SC-002).

## 6. Run the acceptance tests

```bash
pytest tests/acceptance -k baseline -v
pytest tests/contract -v
```

Expected: all AT-001..AT-005 scenarios pass; all artifacts validate against
`contracts/*.schema.json`.
