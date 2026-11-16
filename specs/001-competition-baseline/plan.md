# Implementation Plan: Competition Baseline

**Branch**: `001-competition-baseline` | **Date**: 2026-11-16 | **Spec**: [specs/001-competition-baseline/spec.md](spec.md)

**Input**: Feature specification from `specs/001-competition-baseline/spec.md`

## Summary

Build the first vertical slice of the Kaggle research harness: a standalone,
offline CLI (`kaggle-agent`) that validates a local competition workspace
(`train.csv`, `test.csv`, `sample_submission.csv` + `competition.yaml`),
produces a machine-readable dataset profile with stable input fingerprints, and
runs a deterministic LightGBM/CatBoost baseline under frozen cross-validation,
recording fold-level and aggregate metrics in a structured registry, a tracked
experiment record, and an append-only JSONL research log. No LLM, no agent
runtime, no network, no credentials — the harness must work fully standalone
(constitution XI).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Typer (CLI), Pydantic v2 (contracts/config), PyYAML
(competition config), pandas + pyarrow (tabular data/artifacts), scikit-learn
(splitters, metrics), LightGBM + CatBoost (baseline model families), SQLAlchemy 2
(registry), MLflow (local tracking store), structlog (logging)

**Storage**: SQLite (structured run/experiment registry) + MLflow local file
store (`mlruns/`) + append-only JSONL research log + filesystem artifacts under
the competition workspace

**Testing**: pytest, pytest-cov, pytest-timeout; Ruff (lint/format), mypy (types)

**Target Platform**: local developer machine (Linux/macOS), CPU only

**Project Type**: single modular-monolith CLI application

**Performance Goals**: `validate` completes in under 30 seconds on small
fixtures; end-to-end `baseline` on a synthetic fixture completes in under 10
minutes on a standard development CPU

**Constraints**: fully offline; no credentials; deterministic (seed 42,
fixed folds); rerun metric tolerance 0.000001; dataset files read-only during
runs; no generated code execution in this feature

**Scale/Scope**: single user, one competition at a time, tabular CSV up to
~10^6 rows; binary classification and regression only

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design (see end).*

| Principle | Gate | Status |
|---|---|---|
| I. Scientific Method First | Baseline run records an explicit hypothesis and a conclusion | Pass |
| II. Reproducibility | Full experiment metadata + dataset/config fingerprints + 1e-6 tolerance recorded | Pass |
| III. Validation Integrity | Frozen CV folds, no leaderboard use, fold-isolated target-derived transforms, leakage preflight with fail-safe | Pass |
| IV. Bounded Autonomy | Budgets declared in config and validated up front; no automatic Kaggle submission | Pass |
| V. Evidence-Based Selection | Improvement threshold config reserved; baseline is the incumbent reference | Pass |
| VI. Append-Only Research Memory | JSONL research log; no rewrites | Pass |
| VII. Safe and Reviewable Code Execution | No generated code in this feature; declarative config only; data read-only | Pass |
| VIII. Simplicity / Single-Agent | One CLI, one sequential flow, no LLM, no multi-agent, no event bus | Pass |
| IX. Test-First Delivery | Acceptance scenarios in spec map to automated tests written before implementation | Pass |
| X. Traceability | FR-001..FR-014 map to US1..US4 and acceptance scenarios; artifacts link to run/config/fingerprint | Pass |
| XI. Harness Authority | CLI fully exercisable with no LLM or agent runtime | Pass |
| XII. Runtime Independence | No coupling to any agent runtime or editor | Pass |
| XIII. Human Approval for External Actions | No network, credentials, or submissions in this feature | Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-competition-baseline/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (JSON Schemas)
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/kaggle_agent/
├── cli/                 # Typer commands: init, validate, baseline, status
├── domain/              # Pure domain logic: entities, fingerprints, metrics, policies
├── application/         # Orchestration: validate/baseline services, run lifecycle
└── infrastructure/      # Adapters: SQLite repos, MLflow tracker, JSONL logger, model trainers

tests/
├── unit/
├── contract/            # JSON Schema contract tests
├── integration/
├── acceptance/          # AT-001..AT-005 end-to-end scenarios
└── fixtures/            # Synthetic competition generator

examples/
└── titanic-like/        # Small synthetic fixture used by quickstart
```

**Structure Decision**: single modular monolith under `src/kaggle_agent` with
pure domain logic separated from infrastructure adapters. No event bus, no DI
framework, no web layer.

## Complexity Tracking

No constitution violations; this table is intentionally empty.

## Phase 0 & Phase 1 Outputs

- `research.md` — technical decisions with rationale and alternatives
- `data-model.md` — entities, fields, relationships, state transitions
- `contracts/` — JSON Schemas for competition config, experiment, result, research entry
- `quickstart.md` — runnable end-to-end validation guide

## Constitution Check (post-design re-check)

Re-evaluated after Phase 1 design artifacts were generated: all gates still
pass. The design adds no new infrastructure beyond the constitution's stack,
keeps the research log append-only, keeps the evaluator immutable, and keeps
the CLI standalone. No exceptions required.
