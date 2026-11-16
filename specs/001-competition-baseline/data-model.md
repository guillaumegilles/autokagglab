# Data Model: Competition Baseline (Phase 1)

Entities extracted from `spec.md` (Key Entities) and FR-001..FR-014. Storage:
SQLite registry for structured records, MLflow for tracked metrics/artifacts,
JSONL for the append-only log (see `research.md` D6).

## Entities

### Competition

A validated workspace. One Competition has many ResearchRuns.

| Field | Type | Notes |
|---|---|---|
| slug | string | Primary key; directory name under `competitions/` |
| config_json | JSON | Canonical competition.yaml (Pydantic-validated) |
| config_fingerprint | string | SHA-256 of canonical config JSON |
| created_at | UTC datetime | |

### DatasetProfile

Belongs to one Competition. Produced by `validate`.

| Field | Type | Notes |
|---|---|---|
| competition_slug | FK → Competition | |
| n_rows_train / n_rows_test | int | |
| columns | JSON | name, dtype, missing count, n_unique, is_constant, is_likely_categorical per column |
| target_distribution | JSON | class counts (classification) or stats (regression) |
| id_unique | bool | identifier uniqueness in train and test |
| leakage_warnings | JSON array | non-blocking risks (FR-007) |
| train_sha256 / test_sha256 / submission_sha256 | string | Byte-level fingerprints (FR-004) |
| schema_diff | JSON or null | train vs test feature mismatch (blocking if present, FR-005) |
| created_at | UTC datetime | |

### ResearchRun

One CLI execution. Belongs to one Competition; has many Experiments.

| Field | Type | Notes |
|---|---|---|
| run_id | UUID | Primary key |
| competition_slug | FK → Competition | |
| kind | enum: validate, baseline | |
| status | enum (see below) | |
| budgets_json | JSON | max_experiments, experiment_timeout_s, run_timeout_s, failure_limit from config |
| started_at / finished_at | UTC datetime | |
| exit_code | int | 0/2/3/4 (research.md D10) |
| error | string or null | Failure classification, no secrets |

**State transitions**: `CREATED → VALIDATING → RUNNING → COMPLETED | FAILED`
(`VALIDATING` fails → `FAILED` with exit code 2).

### Experiment

One trained-and-evaluated candidate. The baseline is an Experiment with
`parent_id = null`. Belongs to one ResearchRun; has one Result.

| Field | Type | Notes |
|---|---|---|
| experiment_id | string (`exp-NNNN`) | Primary key |
| run_id | FK → ResearchRun | |
| parent_id | FK → Experiment, nullable | null for baseline |
| hypothesis | string | Explicit, falsifiable (constitution I); baseline: "Default LightGBM under frozen 5-fold CV establishes the reference score" |
| change_json | JSON | One controlled change vs parent; baseline: `{type: "baseline"}` |
| model_family | enum: lightgbm, catboost | |
| params_json | JSON | Model parameters |
| feature_set_version | string | |
| experiment_fingerprint | string | Hash of normalized spec (duplicate detection, feature 002) |
| cv_strategy / seed | string / int | Frozen per run |
| status | enum: PROPOSED, RUNNING, COMPLETED, FAILED, TIMED_OUT | Baseline uses RUNNING → COMPLETED | FAILED |
| git_commit | string | Source revision (constitution II) |

### Result

One per Experiment. Fold-level and aggregate metrics plus metadata.

| Field | Type | Notes |
|---|---|---|
| experiment_id | FK → Experiment | Primary key |
| metric_name | string | From metric registry (research.md D4) |
| direction | enum: max, min | |
| fold_metrics | JSON array | One entry per fold |
| mean / std | float | Aggregate |
| runtime_seconds | float | |
| environment_json | JSON | Python/package versions, CPU, platform |
| mlflow_run_id | string | Link to tracked run |

### ResearchLogEntry

Append-only JSONL record; one per completed/failed run or experiment.
Never updated; corrections are new linked entries (constitution VI).

| Field | Type | Notes |
|---|---|---|
| entry_id | UUID | |
| timestamp | UTC datetime | |
| run_id / experiment_id | string | Links |
| type | enum: run, experiment | |
| hypothesis | string | |
| expected_effect | string | |
| observed | JSON | Metrics, runtime, status |
| conclusion | string | Required on completion (constitution I) |
| parent_entry_id | string or null | Correction linking |

## Relationships

```text
Competition 1──* DatasetProfile
Competition 1──* ResearchRun 1──* Experiment 1──1 Result
ResearchRun 1──* ResearchLogEntry
Experiment 0──1 Experiment (parent, self-ref; null for baseline)
```
