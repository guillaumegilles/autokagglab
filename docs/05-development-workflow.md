# 05 — Development workflow: how the harness itself is built

We build the harness with **spec-driven development (SDD)** using GitHub Spec
Kit, exposed in this repo as the `speckit-*` skills. Key principle: **Spec Kit
governs development of the software — it never sits inside the competition
research loop.**

## Two loops, kept separate

```text
DEV-TIME LOOP (builds the harness)          RUNTIME LOOP (harness runs a competition)
─────────────────────────────────           ─────────────────────────────────────────
Human + coding agent                        Human sets policy + budgets
  │  speckit-* skills                          │
  ▼                                            ▼
Constitution → Specify → Clarify → Plan     Agent runtime (Goose / Pi)
→ Tasks → Analyze → Implement                  │ proposes hypothesis / ExperimentSpec
  │  (artifacts in specs/, code in src/)        ▼
  ▼                                           Harness CLI / MCP (ours)
Harness code                                    │ validates, executes, evaluates
                                                ▼
                                          Research log → Insight → next hypothesis
```

## The SDD loop per feature

Each phase is gated: do not start the next until the current artifact is reviewed
and the gate passes.

| # | Skill | Produces | Gate |
|---|---|---|---|
| 1 | `speckit-constitution` | `.specify/memory/constitution.md` (seeded; refine as needed) | Constitution acceptance gate: mandatory experiment metadata, no LB-driven selection, compute/iteration limits, append-only log, single-agent MVP, tests + traceability |
| 2 | `speckit-specify <feature description>` | `specs/NNN-<feature>/spec.md` (+ feature branch `NNN-<feature>`) | User stories independent & testable; Given/When/Then scenarios; no implementation details |
| 3 | `speckit-clarify` | Resolved decisions appended to spec.md | No open blocking questions; scope unchanged |
| 4 | `speckit-plan <tech context>` | `plan.md`, `research.md`, `data-model.md`, `contracts/*.json`, `quickstart.md` | Constitution check passes; simpler compliant design preferred |
| 5 | `speckit-tasks` | `tasks.md` (T-IDs mapped to US / FR / AT) | Tests-before-code ordering; parallel only if disjoint files |
| 6 | `speckit-analyze` | Findings report | **Blocking**: zero critical findings (leakage, unbounded loops, LB-driven selection, untraced artifacts, scope creep) |
| 7 | `speckit-implement` | Code + tests in `src/`, `tests/` | Per story: acceptance tests pass, then commit |
| 8 | `speckit-checklist` | Quality checklist | All items green before merge |

Also available: `speckit-converge` (append unbuilt work to tasks.md) and
`speckit-taskstoissues` (convert tasks to GitHub issues).

Merge discipline: **one feature = one branch (`NNN-<short-name>`) = one PR**,
and the CI gates below must pass.

## Feature roadmap as spec-kit features

```text
001-competition-baseline   DONE — validate → profile → deterministic baseline
                           (specs/001-competition-baseline/, all tasks complete)
002-strategy-engine        V2 — choose the next experiment from the research log
003-auto-ensembling        V3 — blend / rank-average / stack top candidates
004-cross-competition-memory  V4 — transfer insights across competitions
005-external-research      V5 — forum / notebook mining
006-multi-agent-teams      V6 — only after 001–005 prove out
```

Do not start 002+ while 001 has critical analyze findings or failing P1 tests.
Details and rationale: [06-roadmap.md](06-roadmap.md).

## Anatomy of a feature slice (feature 001 as the template)

- **Outcome statement:** given a local tabular dataset + declarative competition
  config, the system builds a valid baseline, runs bounded reproducible
  experiments, keeps improvements by frozen CV, and emits a valid submission +
  research report.
- **User stories:** US1 validate workspace (P1) · US2 dataset profile (P1) ·
  US3 deterministic baseline (P1) · US4 leakage-safe validation (P2).
- **Requirements:** FR-001…FR-028 in `spec.md`; every FR maps to US + T-ID + AT-ID.
- **Acceptance tests:** AT-xxx in Given/When/Then form, executable in
  `tests/acceptance/` (AT-001…AT-005 shipped with 001; the WORKFLOW blueprint
  extends the scheme to AT-018 for the loop, submission, and resume stories).
- **Clarify defaults** (encoded in the spec): 5-fold CV; StratifiedKFold (binary) /
  KFold (regression); seed 42; failed/timed-out attempts count against the
  attempt budget, duplicates don't; improvement = absolute metric delta vs
  threshold; dataset change blocks resume; one experiment = one config dimension
  or one predefined feature bundle; Parquet predictions, CSV submission; UUID
  ids; UTC timestamps; no target-derived features in the MVP until fold-isolation
  tests exist.
- **Task phases:** A setup → B foundational domain/persistence → C US1 → D US2 →
  E US3 → F US4 → G hardening (E2E both tasks, malformed inputs, append-only
  integrity, traceability, budget enforcement). Acceptance tests are written
  **before** the implementation task of each story (constitution IX).

## CI acceptance gates (every PR)

```bash
ruff check . && ruff format --check . && mypy src
pytest tests/unit && pytest tests/contract && pytest tests/integration \
  && pytest tests/acceptance
pytest --cov=src/kaggle_agent --cov-report=term-missing
```

Thresholds: 100% P1 acceptance tests; 100% safety/validation-integrity tests;
≥ 85% statement coverage; 100% branch coverage on budget enforcement, experiment
state transitions, incumbent selection, submission validation, resume safety;
E2E synthetic classification + regression < 10 min on dev CPU; reproducibility
test passes on two clean executions.

## Conventions

- **Branches:** `NNN-<short-name>` per feature.
- **IDs:** FR-xxx requirements, USx stories, AT-xxx acceptance tests, T-xxx
  tasks — kept in test metadata so `speckit-analyze` can verify traceability.
- **Append-only:** `research_log.jsonl` and research reports are never rewritten;
  corrections are new linked entries.
- **Immutable at runtime:** evaluator, splitter, governance config, raw data.
  Agent-editable: the declarative solution surface only.
- **Source research inputs:** `constitution-prompt.md`, `openai-research.md`,
  `TODO.md`, `WORKFLOW.md`, `automlab/` (see [index](index.md#source-material)).
