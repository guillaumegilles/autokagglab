# 03 — Harness usage: what it can do today and how to use it

Feature `001-competition-baseline` is **implemented and tested** (all tasks in
`specs/001-competition-baseline/tasks.md` complete). The harness works fully
standalone: **no LLM, no agent runtime, no network, no credentials, no GPU.**

## Install

```bash
# Python 3.12, from a clean checkout
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e '.[dev]'
# or: pip install -e '.[dev]'
```

This provides the `kaggle-agent` CLI (`pyproject.toml` →
`kaggle_agent.cli.app:app`) and the dev tooling (pytest, ruff, mypy).

Stack: Python 3.12 · Typer · Pydantic v2 · PyYAML · pandas/pyarrow ·
scikit-learn · LightGBM + CatBoost · SQLAlchemy 2 + SQLite · MLflow (local) ·
structlog.

## Quickstart (offline, ~10 min on a dev CPU)

```bash
# 1. Generate a synthetic competition fixture
python -m tests.fixtures.make_fixture --out competitions/demo-classification --task binary-classification
python -m tests.fixtures.make_fixture --out competitions/demo-regression --task regression

# 2. Validate the workspace (exit 0; prints the dataset profile as JSON)
kaggle-agent validate competitions/demo-classification

# 3. Run the deterministic CV baseline (5 folds, prints per-fold + aggregate metric)
kaggle-agent baseline competitions/demo-classification

# 4. Inspect runs and the incumbent
kaggle-agent status competitions/demo-classification

# 5. Verify determinism: same inputs ⇒ same folds, metric within 1e-6
kaggle-agent baseline competitions/demo-classification
```

Negative check (exit code 2, specific error, no run recorded):

```bash
kaggle-agent validate competitions/demo-classification --config broken.yaml
```

## CLI reference

| Command | Purpose | Exit codes |
|---|---|---|
| `kaggle-agent init <path> --task <t> --target <col> --id <col> --metric <m>` | Scaffold a workspace with a default `competition.yaml` | 0 ok, 2 invalid args |
| `kaggle-agent validate <path> [--config <yaml>]` | Validate inputs, profile + fingerprint the dataset, record a run | 0 ok, 2 validation error |
| `kaggle-agent baseline <path> [--target-encoding]` | Deterministic CV baseline (LightGBM/CatBoost); `--target-encoding` enables fold-isolated target encoding | 0 ok, 2 workspace error, 3 run failure, 4 budget violation |
| `kaggle-agent status <path>` | Read-only summary: runs, profile, leakage warnings, budgets, incumbent | 0 ok, 2 workspace error |

Planned commands (features 002+): `research`, `report`, `resume`, `submission`.

Exit codes (from `application/run_service.py`): `0` OK · `2` validation error ·
`3` run failure · `4` budget violation.

## `competition.yaml` reference

Mirrors `specs/001-competition-baseline/contracts/competition-config.schema.json`:

| Field | Values / default |
|---|---|
| `name` | competition name (string) |
| `task` | `binary-classification` \| `regression` |
| `target` | target column name |
| `id_columns` | list of identifier columns (must be unique in train and test) |
| `metric` | binary: `roc_auc`, `log_loss` · regression: `rmse`, `mae`, `r2` |
| `cv.strategy` | `stratified-kfold` (binary) or `kfold` (regression) |
| `cv.n_folds` | 2–10, default **5** |
| `seed` | default **42** |
| `budgets.max_experiments` | default 10 |
| `budgets.experiment_timeout_seconds` | default 1200 (20 min) |
| `budgets.run_timeout_seconds` | default 10800 (3 h) |
| `budgets.max_consecutive_failures` | default 3 |
| `budgets.min_improvement` | promotion threshold, default 0.001 |

## What a run produces

Every successful `validate`/`baseline` writes, per workspace:

- a row in `registry.sqlite` (competition, profile, run, experiment, result),
- exactly one appended entry in `research_log.jsonl`
  (conforms to `contracts/research-entry.schema.json`),
- an MLflow run under `mlruns/` (params, fold metrics, artifacts),
- per-run artifacts under `runs/<run-id>/artifacts/`.

`status` shows the incumbent: `experiment_id`, metric mean ± std.

## Guarantees (acceptance-tested)

- **Determinism** — rerunning the baseline with unchanged dataset, config, seed,
  and source revision reproduces fold assignments and the aggregate metric
  within **0.000001** (SC-002 / AT-002).
- **Fail-fast validation** — missing files, missing target, duplicate ids,
  train/test schema mismatch, unsupported metric/task, too-small dataset are all
  rejected **before training** with a named error and non-zero exit (SC-003).
- **Leakage safety** — target-derived transformations are fitted inside each
  training fold only; leakage risks are reported in the profile (AT-005).
- **Append-only memory** — the research log is never rewritten; corrections are
  new linked entries.
- **Offline** — zero network access, zero credentials (SC-005).
- **Traceability** — every artifact traces to run, config, dataset fingerprint,
  and source revision (SC-006).

## Tests and CI gates

```bash
ruff check . && ruff format --check . && mypy src
pytest tests/unit && pytest tests/contract && pytest tests/integration \
  && pytest tests/acceptance
pytest --cov=src/kaggle_agent --cov-report=term-missing
```

Suites: `unit` · `contract` (artifacts validate against `contracts/*.json`) ·
`integration` (E2E synthetic classification + regression) · `acceptance`
(AT-001…AT-005 scenarios shipped in 001: baseline, determinism, missing target,
schema mismatch, fold-isolated target transforms).

CI thresholds (every PR): 100% of P1 acceptance tests pass; 100% of
safety/validation-integrity tests; ≥ 85% statement coverage; 100% branch coverage
on budget enforcement, experiment state transitions, incumbent selection,
submission validation, resume safety; E2E runs < 10 min on dev CPU;
reproducibility verified on two clean executions.

## Three interaction modes (same harness, later features expose MCP)

1. **Manual** — the human proposes experiments via the CLI.
2. **Assisted** (default first agent mode) — agent proposes → human approves →
   harness executes.
3. **Autonomous bounded** — agent proposes sequentially within budgets; the
   harness enforces every limit.

See the approval policy in [02-architecture.md](02-architecture.md#approval-policy-runtime-interaction-model).
