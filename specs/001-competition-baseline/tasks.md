---

description: "Task list for feature 001-competition-baseline: standalone offline CLI harness (validate / profile / deterministic baseline)"
---

# Tasks: Competition Baseline

**Input**: Design documents from `specs/001-competition-baseline/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. Constitution IX (Test-First, NON-NEGOTIABLE) and the spec's acceptance scenarios require executable acceptance tests written before implementation. Write tests first, watch them fail, then implement.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md) so each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1..US4); absent in Setup/Foundational/Polish phases
- Exact file paths are included in every task

## Path Conventions

Single project: `src/kaggle_agent/` and `tests/` at repository root, per plan.md.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 Create `pyproject.toml` with Python 3.12, package `kaggle-agent`, dependencies per research.md (typer, pydantic v2, pyyaml, pandas, pyarrow, scikit-learn, lightgbm, catboost, sqlalchemy 2, mlflow, structlog) and `[dev]` extras (pytest, pytest-cov, pytest-timeout, ruff, mypy)
- [X] T002 [P] Configure Ruff (lint + format) and mypy in `pyproject.toml`
- [X] T003 [P] Configure pytest, pytest-cov, pytest-timeout in `pyproject.toml`
- [X] T004 [P] Create package skeleton `src/kaggle_agent/{__init__.py,cli/__init__.py,domain/__init__.py,application/__init__.py,infrastructure/__init__.py}` plus a Typer app skeleton in `src/kaggle_agent/cli/app.py` (no commands yet) with the `kaggle-agent` entry point
- [X] T005 [P] Create `tests/` tree (`tests/{unit,contract,integration,acceptance,fixtures}/` + `tests/conftest.py`)
- [X] T006 [P] Implement synthetic fixture generator `tests/fixtures/make_fixture.py` producing a binary-classification and a regression workspace per `quickstart.md` (`competition.yaml`, `data/train.csv`, `data/test.csv`, `data/sample_submission.csv`)
- [X] T007 [P] Add CI workflow `.github/workflows/ci.yml` running `ruff check`, `ruff format --check`, `mypy src`, and the unit/contract/integration/acceptance suites with coverage report

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain logic and infrastructure that MUST be complete before ANY user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T008 Implement `CompetitionConfig` Pydantic v2 model in `src/kaggle_agent/domain/config.py` matching `contracts/competition-config.schema.json` exactly (required: name, task enum binary-classification|regression, target, id_columns minItems 1, metric enum, cv{strategy,n_folds 2-10 default 5}, seed default 42, budgets{max_experiments, experiment_timeout_seconds, run_timeout_seconds, max_consecutive_failures, min_improvement default 0.001})
- [X] T009 [P] Implement fingerprinting in `src/kaggle_agent/domain/fingerprints.py`: SHA-256 over file bytes, canonical-JSON config hash, schema hash, experiment-spec hash (research.md D7); inputs never modified
- [X] T010 [P] Implement metric registry in `src/kaggle_agent/domain/metrics.py`: roc_auc(max)/log_loss(min) for binary-classification, rmse(min)/mae(min)/r2(max) for regression; unknown metric raises validation error listing supported names (research.md D4)
- [X] T011 [P] Implement deterministic CV split generation in `src/kaggle_agent/domain/splits.py`: default 5 folds, StratifiedKFold for binary-classification, KFold for regression, seed 42, fold assignments persisted per run (research.md D3)
- [X] T012 [P] Implement leakage/validation preflight in `src/kaggle_agent/domain/leakage.py`: blocking failures for missing target, duplicate identifiers, train/test schema mismatch, dataset too small for folds; warnings for constant columns, high-cardinality ID-like columns, target-in-features, imbalanced target (research.md D8)
- [X] T013 Implement workspace layout + `init` support in `src/kaggle_agent/application/workspace.py`: `competitions/<slug>/{competition.yaml,data/,runs/<run-id>/artifacts/,mlruns/,research_log.jsonl,registry.sqlite}`; dataset files read-only during runs (research.md D6)
- [X] T014 Implement SQLite registry via SQLAlchemy 2 in `src/kaggle_agent/infrastructure/registry.py` for all entities in `data-model.md` (Competition, DatasetProfile, ResearchRun, Experiment, Result) with state-transition constraints
- [X] T015 [P] Implement MLflow tracking adapter in `src/kaggle_agent/infrastructure/tracking.py`: local file store under workspace `mlruns/`; logs params, metrics, artifacts (research.md D6)
- [X] T016 [P] Implement append-only JSONL research log in `src/kaggle_agent/infrastructure/research_log.py`: entries conform to `contracts/research-entry.schema.json`; append-only, corrections via new linked `parent_entry_id` (constitution VI)
- [X] T017 [P] Implement run lifecycle + exit codes in `src/kaggle_agent/application/run_service.py`: ResearchRun states CREATED→VALIDATING→RUNNING→COMPLETED|FAILED; exit codes 0 success / 2 validation error / 3 run failure / 4 budget violation (research.md D10); structlog JSON logging, no secrets
- [X] T018 [P] Contract tests validating example payloads against all schemas in `specs/001-competition-baseline/contracts/*.schema.json` in `tests/contract/test_schemas.py`

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Validate a competition workspace (Priority: P1) 🎯 MVP

**Goal**: `kaggle-agent validate <workspace>` rejects every invalid input before training with a specific error, exit code 2, and no run recorded; valid configs pass with a run record.

**Independent Test**: Run `tests/acceptance/test_validate_negative.py` — all edge cases fail pre-training with non-zero exit; a valid fixture passes validation (exit 0).

### Tests for User Story 1 (write FIRST, must FAIL before implementation)

- [X] T019 [P] [US1] Acceptance tests for negative cases in `tests/acceptance/test_validate_negative.py`: AT-003 missing target, AT-004 train/test schema mismatch, plus missing files, duplicate identifiers, unsupported metric/task, dataset too small for folds (spec edge cases; FR-002, FR-003, FR-005)
- [X] T020 [P] [US1] Unit tests for the validator in `tests/unit/test_validator.py`

### Implementation for User Story 1

- [X] T021 [US1] Implement `CompetitionValidator` in `src/kaggle_agent/application/validate_service.py`: file presence/readability (FR-002), target/identifiers/task/metric/split validation with supported-values error (FR-003), fingerprint inputs without modifying (FR-004), reject incompatible train/test/submission schemas (FR-005); uses T008–T013
- [X] T022 [US1] Wire `kaggle-agent validate` command in `src/kaggle_agent/cli/validate.py`: exit code 2 on validation failure, ResearchRun recorded CREATED→VALIDATING→COMPLETED|FAILED, register command in `src/kaggle_agent/cli/app.py`

**Checkpoint**: User Story 1 fully functional and independently testable.

---

## Phase 4: User Story 2 - Inspect the dataset profile (Priority: P1)

**Goal**: `validate` on a valid workspace stores a machine-readable DatasetProfile (shape, dtypes, missing values, target distribution, ID uniqueness, constant/likely-categorical columns, leakage warnings, fingerprints); `status` displays it. Depends on US1's validate command.

**Independent Test**: `tests/acceptance/test_profile.py` — profile contains all FR-006 fields; fingerprint identical across reruns and different after modifying train.csv.

### Tests for User Story 2 (write FIRST)

- [X] T023 [P] [US2] Acceptance tests for profile content and fingerprint stability/change in `tests/acceptance/test_profile.py` (FR-004, FR-006, FR-007)

### Implementation for User Story 2

- [X] T024 [US2] Implement `DatasetProfiler` in `src/kaggle_agent/application/profile_service.py`: all FR-006 profile fields + FR-007 leakage-risk reporting (blocking vs warning split per research.md D8); persist DatasetProfile per `data-model.md`
- [X] T025 [US2] Wire profile output into the validate command and add read-only `kaggle-agent status` in `src/kaggle_agent/cli/status.py` (lists runs, profile summary, budgets; exit 0)

**Checkpoint**: User Stories 1 AND 2 work independently.

---

## Phase 5: User Story 3 - Produce a deterministic baseline (Priority: P1) 🎯 MVP

**Goal**: `kaggle-agent baseline <workspace>` trains a LightGBM (default) or CatBoost model under frozen persisted CV folds and records per-fold + aggregate metrics, a structured run/experiment/result, an MLflow run, and one append-only JSONL entry with hypothesis and conclusion. Exit 0 on success, 3 on run failure.

**Independent Test**: `tests/acceptance/test_baseline.py` (AT-001) and `tests/acceptance/test_determinism.py` (AT-002: rerun reproduces aggregate metric within 0.000001 with identical folds and fingerprint).

### Tests for User Story 3 (write FIRST)

- [X] T026 [P] [US3] Acceptance AT-001 in `tests/acceptance/test_baseline.py`: valid binary-classification fixture → configured folds executed, one metric per fold + aggregate stored, MLflow run created, baseline JSONL entry appended, exit 0 (FR-008..FR-011, FR-012)
- [X] T027 [P] [US3] Acceptance AT-002 in `tests/acceptance/test_determinism.py`: same dataset/config/revision/seed → same fingerprint, same fold assignments, aggregate metric within 0.000001 (FR-013, SC-002); regression task uses KFold; NaN metric → FAILED + exit 3

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `Trainer` protocol + LightGBM adapter in `src/kaggle_agent/infrastructure/trainers.py`: deterministic (seed 42, `deterministic=true`, `force_row_wise=true`, fixed `num_threads=4`) per research.md D9
- [X] T029 [P] [US3] Implement CatBoost adapter in `src/kaggle_agent/infrastructure/trainers.py` (fixed seed, `thread_count=4`)
- [X] T030 [US3] Implement baseline service in `src/kaggle_agent/application/baseline_service.py`: train+evaluate per fold on frozen splits (T011), fold metrics + aggregate mean/std, Experiment record with baseline hypothesis and `parent_id=null`, Result per `data-model.md`, registry write (T014), MLflow run (T015), JSONL entry with conclusion (T016); full metadata per constitution II (git commit, config, fingerprints, params, seed, CV, environment, duration, metric)
- [X] T031 [US3] Wire `kaggle-agent baseline` command in `src/kaggle_agent/cli/baseline.py`: exit 0/3, NaN/non-finite metric marks run FAILED with exit 3, register in `src/kaggle_agent/cli/app.py`

**Checkpoint**: User Story 3 works end-to-end on the synthetic fixture within the 10-minute CPU budget (SC-001).

---

## Phase 6: User Story 4 - Keep validation leakage-safe (Priority: P2)

**Goal**: Predefined target-derived transformations are fitted only inside each training fold; confirmed target leakage in config fails safely. Depends on US3's baseline pipeline.

**Independent Test**: `tests/acceptance/test_leakage.py` (AT-005) — per fold, transform fitted only on that fold's training rows; no validation target accessible during fitting.

### Tests for User Story 4 (write FIRST)

- [X] T032 [P] [US4] Acceptance AT-005 in `tests/acceptance/test_leakage.py`: enabled target-dependent transform is fold-isolated; leakage-risk column reported but not silently used as feature

### Implementation for User Story 4

- [X] T033 [US4] Implement fold-isolated transform pipeline in `src/kaggle_agent/domain/transforms.py`: every target-derived transform fitted within each training fold only
- [X] T034 [US4] Integrate transforms into `src/kaggle_agent/application/baseline_service.py`; confirmed target leakage in target/identifier config → fail-safe abort (constitution III)

**Checkpoint**: All user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verification, quality gates, and traceability.

- [X] T035 [P] Contract tests validating produced artifacts (experiment, result, research-log entry) against `contracts/experiment.schema.json`, `contracts/result.schema.json`, `contracts/research-entry.schema.json` in `tests/contract/test_artifacts.py`
- [X] T036 [P] End-to-end integration test `init → validate → baseline → status` on the synthetic fixture in `tests/integration/test_e2e.py` (classification and regression)
- [X] T037 [P] Unit tests for edge cases of fingerprints, metrics, splits, leakage preflight in `tests/unit/`
- [X] T038 Run `quickstart.md` end-to-end from a clean checkout and fix any discrepancy
- [X] T039 Enforce CI gates in `.github/workflows/ci.yml`: `ruff check .`, `ruff format --check .`, `mypy src`, pytest unit/contract/integration/acceptance, coverage ≥ 85% statement and 100% branch on exit-code/state-transition paths
- [X] T040 Verify traceability against `specs/001-competition-baseline/spec.md`: every FR-001..FR-014 maps to ≥1 user story and ≥1 acceptance test; every artifact traces to run/config/fingerprint (constitution X)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately
- **Foundational (Phase 2)**: depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3–6)**: depend on Foundational; US2 depends on US1's validate command; US3 depends on US1+US2; US4 depends on US3
- **Polish (Phase 7)**: depends on all in-scope user stories

### User Story Dependencies

- **US1 (P1)**: after Foundational; no story dependencies
- **US2 (P1)**: after Foundational + US1 (reuses validate flow)
- **US3 (P1)**: after Foundational + US1 + US2 (needs validated profile and fingerprints)
- **US4 (P2)**: after US3 (needs the baseline pipeline)

### Within Each User Story

- Tests MUST be written first and FAIL before implementation (constitution IX)
- Domain/models before application services; services before CLI wiring
- Core implementation before integration; story checkpoint before moving on

### Parallel Opportunities

- All Phase 1 tasks marked [P] run in parallel
- Within Phase 2: T009, T010, T011, T012, T015, T016, T018 are [P]; T013/T014/T017 integrate them
- Within story phases: test tasks marked [P] run in parallel; trainer adapters T028/T029 are [P]
- T035, T036, T037 in Phase 7 are [P]

---

## Parallel Example: User Story 3

```bash
# Launch all US3 tests together:
Task: "T026 [P] [US3] Acceptance AT-001 in tests/acceptance/test_baseline.py"
Task: "T027 [P] [US3] Acceptance AT-002 in tests/acceptance/test_determinism.py"

# Launch both trainer adapters together:
Task: "T028 [P] [US3] Trainer protocol + LightGBM adapter in src/kaggle_agent/infrastructure/trainers.py"
Task: "T029 [P] [US3] CatBoost adapter in src/kaggle_agent/infrastructure/trainers.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 (Setup) + Phase 2 (Foundational)
2. Complete US1 → US2 → US3 (all P1; together they are the vertical slice: validate → profile → deterministic baseline)
3. STOP and VALIDATE: run `tests/acceptance` + quickstart on the synthetic fixture
4. US4 (P2, leakage-safe transforms) follows as the next increment

### Incremental Delivery

- Foundation ready → US1 independently testable → US2 → US3 (MVP demo: baseline + recorded run) → US4 → Polish/CI gates
- Each story adds value without breaking previous stories; commit after each story checkpoint

---

## Notes

- [P] = different files, no dependency on incomplete tasks
- [Story] labels map tasks to spec.md user stories for traceability (constitution X)
- Tests are mandatory here (constitution IX): write first, confirm they fail, then implement; never weaken a test to pass
- Exact constraints from `data-model.md` and `contracts/` are quoted in the relevant tasks — do not reinterpret them at implementation time
- Offline only: no task may add network access, credentials, or Kaggle API calls (constitution XIII)
