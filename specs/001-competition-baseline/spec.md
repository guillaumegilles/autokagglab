# Feature Specification: Competition Baseline

**Feature Branch**: `001-competition-baseline`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "First vertical slice of the autonomous Kaggle research harness: a standalone CLI that validates a local competition workspace, profiles and fingerprints the dataset, and produces a deterministic cross-validation baseline with full run recording. No LLM, no agent runtime, no network."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate a competition workspace (Priority: P1)

As a Kaggle competitor, I want to point the CLI at a dataset directory and a
competition configuration and have invalid inputs rejected immediately, so that
I never waste compute on a malformed competition setup.

**Why this priority**: Every later capability (baseline, experiment loop,
submission) depends on a trustworthy input contract. Failing fast before any
training is the cheapest correctness guarantee the system can offer.

**Independent Test**: Run the `validate` command against fixture workspaces
covering each invalid case; each must fail before training with a clear error
message and a non-zero exit code, and no run record may be created.

**Acceptance Scenarios**:

1. **Given** a directory missing `train.csv`, **When** the user runs `validate`, **Then** validation fails, the missing file is named, and the exit code is non-zero.
2. **Given** a `train.csv` without the configured target column, **When** the user runs `validate`, **Then** validation fails before any model training, the missing target column is identified, and no completed run is recorded.
3. **Given** duplicate identifier values in train or test, **When** the user runs `validate`, **Then** validation fails and reports the identifier column.
4. **Given** a feature present in `train.csv` but absent from `test.csv`, **When** the user runs `validate`, **Then** validation fails and the schema difference is reported.
5. **Given** an unsupported evaluation metric or task type, **When** the user runs `validate`, **Then** validation fails and lists the supported values.
6. **Given** a dataset too small for the configured number of folds, **When** the user runs `validate`, **Then** validation fails with a clear message.

---

### User Story 2 - Inspect the dataset profile (Priority: P1)

As a Kaggle competitor, I want a machine-readable profile of the dataset —
shape, column types, missing values, target distribution, identifier uniqueness,
constant and likely categorical columns, and likely leakage risks — plus a
stable fingerprint of the inputs, so that every later experiment is comparable
and reproducible.

**Why this priority**: The profile is what makes experiments evidence-based;
the fingerprint is what makes them reproducible. Both are prerequisites for
the experiment loop (feature `002`).

**Independent Test**: Run `validate` on a valid fixture and inspect the stored
profile and fingerprint; rerun and confirm the fingerprint is identical.

**Acceptance Scenarios**:

1. **Given** a valid competition workspace, **When** the user runs `validate`, **Then** a profile is produced covering row/column counts, column types, missing-value counts, target distribution, identifier uniqueness, constant columns, likely categorical columns, and likely leakage risks.
2. **Given** a completed validation, **When** the same dataset is validated again, **Then** the dataset fingerprint is identical.
3. **Given** a modified `train.csv`, **When** validation runs, **Then** the fingerprint differs from the previous one.

---

### User Story 3 - Produce a deterministic baseline (Priority: P1)

As a Kaggle competitor, I want to run a `baseline` command that trains a
default gradient-boosting model (LightGBM or CatBoost) under a frozen,
deterministic cross-validation strategy and records fold-level and aggregate
metrics, so that I have a trustworthy local benchmark before any autonomous
experimentation.

**Why this priority**: The baseline is the incumbent every future experiment is
compared against. Without a deterministic, fully recorded baseline, no
improvement claim is meaningful.

**Independent Test**: Run `baseline` twice on the same fixture with the same
configuration and seed; both runs must produce the same folds, the same
aggregate metric within 0.000001, and complete with exit code 0.

**Acceptance Scenarios**:

1. **Given** a valid binary classification dataset with ROC AUC as the metric and unique identifiers, **When** the user runs `baseline`, **Then** the system executes the configured number of validation folds, stores one metric per fold plus the aggregate score, records a tracked run with full experiment metadata (source revision, configuration, dataset fingerprint, model family and parameters, random seeds, CV strategy, environment, duration, metric), appends a completed baseline entry to the research log, and exits with status 0.
2. **Given** a completed baseline, **When** the same dataset, configuration, source revision, and seed are used again, **Then** the second run has the same dataset fingerprint, the same fold assignments, and an aggregate metric differing by no more than 0.000001.
3. **Given** a regression task, **When** the user runs `baseline`, **Then** an unflagged KFold strategy is used and the same recording guarantees hold.
4. **Given** a run with an imbalanced binary target, **When** the user runs `baseline`, **Then** stratification is applied and the target distribution is visible in the profile.

---

### User Story 4 - Keep validation leakage-safe (Priority: P2)

As a Kaggle competitor, I want any target-derived transformation used by the
baseline to be fitted only inside each training fold, so that my validation
score is never inflated by leakage.

**Why this priority**: A leaky baseline invalidates every future comparison.
Lower priority than producing any baseline because the default baseline uses
no target-derived features; this story guarantees the invariant for the
predefined transformations that exist.

**Independent Test**: Enable a predefined target-dependent transformation and
inspect that, for every validation fold, the transformation was fitted only on
that fold's training rows.

**Acceptance Scenarios**:

1. **Given** a predefined target-dependent transformation is enabled, **When** cross-validation runs, **Then** the transformation for each validation fold is fitted only on that fold's training rows, and no validation target value is accessible during fitting.
2. **Given** a column flagged as a likely leakage risk in the profile, **When** validation runs, **Then** the risk is reported in the profile and the baseline does not silently use the column as a feature.

---

### Edge Cases

- Missing input files (`train.csv`, `test.csv`, `sample_submission.csv`) → named error, non-zero exit, no run recorded.
- Missing configured target column → fail before training.
- Duplicate identifiers in train or test → fail with the offending column named.
- Train/test schema mismatch → fail with the difference reported.
- Unsupported metric or task type → fail with supported values listed.
- Dataset too small for the configured fold count → fail with a clear message.
- Constant feature columns → reported in the profile; excluded from the baseline feature set.
- Missing values → handled by the default missing-value strategy and reported in the profile.
- Imbalanced binary target → stratified folds; distribution shown in the profile.
- Target leakage indicators → reported; the run fails safely on confirmed target leakage in the target/identifier configuration.
- NaN or non-finite metric after training → the run is marked failed, recorded as such, and the command exits non-zero.
- Attempts to run with a configuration that exceeds declared budgets → rejected at validation time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a dataset directory containing `train.csv`, `test.csv`, and `sample_submission.csv`, plus a declarative competition configuration specifying competition name, task type (binary classification or regression), target column, identifier column(s), evaluation metric, cross-validation strategy, random seed, and experiment/time budgets.
- **FR-002**: The system MUST verify the presence and readability of all required files before any training.
- **FR-003**: The system MUST validate the target, identifiers, task type, metric, and split configuration, and reject unsupported values with a message listing supported ones.
- **FR-004**: The system MUST fingerprint the input datasets without modifying them.
- **FR-005**: The system MUST reject incompatible train, test, and sample-submission schemas.
- **FR-006**: The system MUST produce a structured dataset profile (shape, column types, missing values, target distribution, identifier uniqueness, constant columns, likely categorical columns, likely leakage risks, fingerprints).
- **FR-007**: The system MUST detect common leakage and validation risks and report them in the profile.
- **FR-008**: The system MUST create at least one valid baseline using LightGBM or CatBoost.
- **FR-009**: The baseline MUST use deterministic cross-validation (default: 5 folds; stratified for binary classification, plain KFold for regression; default seed 42).
- **FR-010**: The system MUST record fold-level and aggregate metrics plus full experiment metadata (source revision, configuration, dataset fingerprint, model family and parameters, random seeds, CV strategy, environment metadata, execution duration, metric) in a structured run registry and a tracked experiment record.
- **FR-011**: The system MUST append a completed baseline entry to an append-only research log; historical entries MUST NOT be rewritten.
- **FR-012**: The system MUST expose CLI commands `init`, `validate`, `baseline`, and `status`, with exit code 0 on success and non-zero on any validation or run failure.
- **FR-013**: Rerunning a baseline with the same inputs MUST reproduce the aggregate metric within 0.000001.
- **FR-014**: The system MUST NOT access the network, load credentials, or submit anything to Kaggle in this feature.

### Key Entities

- **Competition**: a validated workspace — configuration plus dataset profile and fingerprints. Relates to many ResearchRuns.
- **DatasetProfile**: the machine-readable profile and fingerprint of the inputs. Belongs to one Competition.
- **ResearchRun**: one execution of the CLI (validate/baseline) with status, budgets, and timestamps. Belongs to one Competition.
- **Experiment**: one trained-and-evaluated candidate (the baseline in this feature) with exactly one parent (none for the baseline), a hypothesis, a controlled change, and a status. Belongs to one ResearchRun.
- **Result**: fold-level and aggregate metrics plus metadata for one Experiment.
- **ResearchLogEntry**: one append-only entry per run/experiment, linking hypothesis, result, and conclusion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can validate a competition workspace and produce a baseline on a small synthetic fixture via the CLI in under 10 minutes on a standard development CPU.
- **SC-002**: Rerunning the baseline with unchanged inputs reproduces the aggregate metric within 0.000001 and identical fold assignments.
- **SC-003**: 100% of the invalid-input edge cases listed above are rejected before training, with a specific error message and non-zero exit code.
- **SC-004**: Every successful baseline run produces one metric per fold, the aggregate metric, a structured run record, a tracked experiment record, and exactly one appended research-log entry.
- **SC-005**: The feature requires zero network access and zero credentials.
- **SC-006**: Every baseline artifact is traceable to its run, configuration, dataset fingerprint, and source revision.

## Assumptions

- Local, single-user CLI; tabular CSV data only; binary classification and regression only; CPU only.
- Model families are limited to LightGBM and CatBoost (project constitution).
- Default cross-validation: 5 folds, stratified for binary classification, plain KFold for regression, seed 42.
- Structured run registry, experiment tracking, and append-only JSONL research log per the project constitution; exact technologies are chosen in the planning phase.
- No LLM or agent runtime is involved in this feature; the harness must work fully standalone.
- `sample_submission.csv` defines the submission shape but submission generation itself belongs to a later feature.
- The user runs commands on their own machine; there is no server, web UI, or multi-user support.
