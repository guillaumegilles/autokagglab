# Research: Competition Baseline (Phase 0)

All technical unknowns from the plan's Technical Context, resolved. Format:
Decision / Rationale / Alternatives considered.

## D1 — CLI framework

- **Decision**: Typer (on top of Click) for the `kaggle-agent` CLI.
- **Rationale**: Constitution fixes Typer; it gives typed subcommands
  (`init`, `validate`, `baseline`, `status`) and clean exit-code handling with
  almost no boilerplate.
- **Alternatives considered**: argparse (stdlib, but manual exit codes and help
  text), Click alone (fine, but Typer adds type-checked options for budgets and
  paths).

## D2 — Competition configuration format

- **Decision**: a single `competition.yaml` per workspace, validated by a
  Pydantic v2 model and exported as JSON Schema to `contracts/`.
- **Rationale**: YAML is human-editable (the human writes policy, per
  Autoresearch discipline); Pydantic gives fail-fast validation with precise
  error messages required by FR-003/FR-005.
- **Alternatives considered**: JSON (no comments, hostile for humans), TOML
  (fine, but YAML matches the research doc and Kaggle conventions).

## D3 — Cross-validation strategy

- **Decision**: scikit-learn splitters; 5 folds default; `StratifiedKFold`
  for binary classification, `KFold` for regression; seed 42; fold assignments
  persisted per run so every later experiment reuses identical folds.
- **Rationale**: Deterministic, widely understood, and stratification is
  required for imbalanced binary targets (spec edge case).
- **Alternatives considered**: GroupKFold / TimeSeriesSplit — out of scope for
  the MVP (no time-series competitions).

## D4 — Metric registry

- **Decision**: a registry mapping metric name → scorer + optimization
  direction. MVP set: binary classification `roc_auc` (max), `log_loss` (min);
  regression `rmse` (min), `mae` (min), `r2` (max). Unknown metric → validation
  error listing supported names (FR-003).
- **Rationale**: Direction must be explicit per metric so later incumbent
  selection (feature 002) never guesses.
- **Alternatives considered**: free-form metric strings — rejected, ambiguous
  direction breaks evidence-based selection.

## D5 — Baseline model families

- **Decision**: LightGBM as the default baseline (fast on CPU, deterministic
  with `deterministic=true`, `force_row_wise=true`, fixed seed, fixed
  `num_threads`); CatBoost available as the alternative family. Both wrapped
  behind a single `Trainer` protocol so feature 002 can switch families via a
  declarative spec.
- **Rationale**: Constitution limits MVP model families to these two; a
  protocol boundary keeps the planner declarative (constitution VII/VIII).
- **Alternatives considered**: XGBoost — deferred (research doc's later MVP
  scope narrowed to LightGBM + CatBoost); sklearn ensembles — too slow for
  the 10-minute budget.

## D6 — Persistence layout

- **Decision**: per-competition workspace
  `competitions/<slug>/{competition.yaml, data/, runs/<run-id>/artifacts/,
  research_log.jsonl}`; structured registry in `registry.sqlite` at workspace
  root via SQLAlchemy 2; MLflow tracking URI `file:./mlruns`; research log is
  append-only JSONL.
- **Rationale**: Everything about a competition stays in one portable
  directory; SQLite + local MLflow need no server; JSONL is diff-friendly and
  trivially append-only (constitution VI).
- **Alternatives considered**: PostgreSQL — rejected (constitution: no
  external services in MVP); MLflow server — rejected (local file store only).

## D7 — Fingerprinting

- **Decision**: dataset fingerprint = SHA-256 over file bytes + canonical
  schema hash (column names, dtypes); config fingerprint = SHA-256 over
  canonical JSON of the Pydantic model; experiment fingerprint = hash of
  normalized experiment spec (used by feature 002 duplicate detection).
  Fingerprints are computed without modifying inputs (FR-004).
- **Rationale**: Byte-level hashing catches any data change (resume safety in
  feature 004); canonical JSON hashing makes config equality order-independent.
- **Alternatives considered**: row-count-only checksums — rejected, they miss
  value changes.

## D8 — Leakage and validation preflight

- **Decision**: blocking failures for missing files/target, duplicate
  identifiers, train/test schema mismatch, unsupported metric/task, dataset
  too small for folds; warnings (reported in profile, not blocking) for
  constant columns, high-cardinality ID-like columns, target present in
  features, imbalanced target. Any target-derived transform must be fitted
  inside each training fold (AT-005).
- **Rationale**: Matches the spec's edge-case list and constitution III;
  warnings preserve visibility without blocking legitimate runs.
- **Alternatives considered**: fail on every warning — rejected, too strict
  (e.g., constant columns are merely reported).

## D9 — Determinism and tolerance

- **Decision**: seed 42 everywhere; LightGBM `deterministic=true`,
  `force_row_wise=true`, fixed `num_threads=4`; CatBoost `thread_count=4`,
  `deterministic` via fixed seed; metric tolerance for reruns: 0.000001
  (FR-013/SC-002).
- **Rationale**: CPU gradient boosting is deterministic given these settings;
  the tolerance absorbs platform-level float noise.
- **Alternatives considered**: `n_jobs=-1` — rejected, thread-count variance
  can perturb results.

## D10 — CLI exit codes

- **Decision**: 0 success; 2 validation/config error; 3 run failure (e.g., NaN
  metric, model crash); 4 budget violation. `status` is read-only and always
  exits 0 unless the workspace is unknown.
- **Rationale**: Distinct codes let scripts and later automation react without
  parsing stderr; FR-012 requires non-zero on any failure.
- **Alternatives considered**: single non-zero code — rejected, loses
  actionable distinction.

## D11 — Testing strategy

- **Decision**: pytest with a synthetic fixture generator
  (`tests/fixtures/make_fixture.py`) producing a small binary-classification
  and a regression workspace; acceptance tests mirror AT-001..AT-005;
  `pytest-timeout` guards runaway runs; contract tests validate artifacts
  against `contracts/*.schema.json`.
- **Rationale**: Constitution IX requires executable acceptance tests written
  before implementation; synthetic fixtures keep CI offline and fast.
- **Alternatives considered**: real Kaggle data in tests — rejected (offline,
  licensing, size).

## D12 — Logging

- **Decision**: structlog with JSON lines to stderr plus a human-readable run
  log under `runs/<run-id>/`; no secrets ever logged (none exist offline).
- **Rationale**: Constitution VII forbids credential access; structured logs
  make failures classifiable later (feature 002 failure budget).
- **Alternatives considered**: stdlib logging — rejected, unstructured output
  is hard to classify automatically.
