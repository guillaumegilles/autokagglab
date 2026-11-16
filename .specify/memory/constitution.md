<!--
Sync Impact Report — constitution amendment (temporary, remove before commit)

Version change: 1.0.0 → 1.1.0 (MINOR: new principles added; no existing
principle removed or redefined in a backward-incompatible way).
Note: .specify/memory/constitution.md was still the unfilled core template.
Project content was sourced from the root constitution.md (v1.0.0, ratified
2026-11-16) and amended with decisions from the architecture conversation
(Autoresearch discipline, harness/agent separation, CLI-first interface,
runtime independence, human approval for external actions).

Modified principles:
- VII. Safe and Reviewable Code Execution — added the declarative
  ExperimentSpec rule (no unconstrained generated code execution in the MVP)
- VIII. Simplicity and Single-Agent Architecture — planner behind a protocol,
  deterministic rule-based planner first
- Development Workflow — corrected agent integration (Vibe skills, not Pi
  prompt files) and added the layered build order

Added principles:
- XI. Harness Authority — The Agent Proposes, the Harness Disposes
- XII. Runtime Independence — replaceable agent runtimes and editors
- XIII. Human Approval for External Actions

Removed: none. Follow-up TODOs: none.
-->

# AutoKagglab Constitution

## Core Principles

### I. Scientific Method First

Every experiment MUST begin with an explicit, falsifiable hypothesis.
Every completed experiment MUST produce a structured result and conclusion.
An experiment without a hypothesis is invalid.
A result without a conclusion is incomplete.
The primary output of the system is accumulated research knowledge that
improves leaderboard performance, not generated code.

### II. Reproducibility

Every experiment MUST record: source-code revision, competition configuration,
dataset fingerprint, feature-set version, model family, model parameters, random
seeds, cross-validation strategy, environment metadata, execution duration, and
evaluation metric.
Rerunning an experiment with the same inputs MUST reproduce its metric within a
documented numerical tolerance.

### III. Validation Integrity

Model selection MUST use local cross-validation, never the Kaggle public
leaderboard.
Training data MUST remain isolated from validation data.
Target-derived transformations MUST be fitted inside each training fold.
The system MUST fail safely if it detects target leakage, identifier leakage,
row overlap, or an invalid split configuration.
The evaluation harness (splits, evaluator, governance) is immutable during a
research run; the agent may never modify it.

### IV. Bounded Autonomy

Every autonomous research run MUST have explicit limits for: maximum number of
experiments, maximum duration per experiment, maximum duration for the research
run, and maximum number of consecutive failures.
The agent MUST stop when any limit is reached.
Budgets MUST be enforced by the harness in code, not by asking the model to
remember to stop.
The agent MUST NOT submit automatically to Kaggle in the MVP.

### V. Evidence-Based Selection

The system MUST compare experiments using a consistent validation protocol.
An experiment MUST NOT replace the incumbent unless it satisfies the configured
improvement threshold.
Metric variance and fold-level results MUST be preserved.
A worse experiment may be retained as knowledge but not promoted as incumbent.

### VI. Append-Only Research Memory

Hypotheses, experiment outcomes, failures, and insights MUST be written to an
append-only research log.
Historical records MUST NOT be silently rewritten.
Corrections MUST be represented as new linked entries.
Memory is more important than agent count: a single well-designed research
agent with strong memory outperforms a swarm without it.

### VII. Safe and Reviewable Code Execution

Generated experiment changes MUST be constrained to declared extension points.
Experiments MUST be declarative ExperimentSpec objects validated by the harness;
the MVP MUST NOT execute unconstrained generated Python code.
The runner MUST execute experiments in an isolated working directory.
Dataset source files and accepted experiment artifacts MUST be read-only during
execution.
No generated code may access network services, credentials, or paths outside the
workspace.

### VIII. Simplicity and Single-Agent Architecture

The MVP MUST use one agent and one sequential experiment loop.
The experiment planner MUST sit behind a protocol: a deterministic rule-based
planner is the MVP and the acceptance-test baseline; an LLM-backed planner is a
later, optional replacement behind the same interface.
New infrastructure MUST be justified by a current acceptance criterion.
Multi-agent orchestration, distributed execution, cloud infrastructure, and a
web UI are prohibited in the MVP.

### IX. Test-First Delivery (NON-NEGOTIABLE)

Each user story MUST have executable acceptance tests written before
implementation.
Critical data leakage, reproducibility, budget enforcement, and artifact
validity behavior MUST be covered by automated tests.
No user story is complete until its independent acceptance tests pass.
Acceptance tests MUST NOT be weakened to make implementation pass.

### X. Traceability

Every functional requirement MUST map to at least one user story, one or more
implementation tasks, and one or more acceptance tests.
Every experiment artifact MUST be traceable to the hypothesis that caused it.

### XI. Harness Authority — The Agent Proposes, the Harness Disposes

The Kaggle research harness owns every deterministic, safety-critical rule:
competition validation, dataset fingerprinting, frozen cross-validation folds,
leakage checks, budget enforcement, metric calculation, incumbent selection,
research memory, and submission validation.
These rules MUST live in harness code, never in an LLM prompt, agent extension,
recipe, or editor.
The harness MUST be fully exercisable through its CLI with no LLM, agent
runtime, or editor present.
An agent runtime may only submit declarative experiment proposals, which the
harness validates, accepts, rejects, or executes.

### XII. Runtime Independence

Agent runtimes (Goose, Pi) and editors (Zed via ACP) are replaceable
scaffolding, not the product.
The durable assets are the research protocol, experiment schema, immutable
evaluation harness, and accumulated research memory.
No design decision may couple the harness to a specific agent runtime, editor,
or model provider.
Integration MUST happen through a narrow MCP/CLI tool surface (for example
get_research_state, propose_experiment, run_experiment, generate_report),
never through direct database writes or unrestricted shell access.

### XIII. Human Approval for External Actions

The MVP MUST NOT upload submissions to Kaggle, download competition data,
access the network, or load credentials without explicit human approval.
Submission file generation is automatic; uploading is a governed,
human-approved action.
Every external or irreversible action MUST be classified green (autonomous),
amber (human approval), or red (prohibited), and the classification MUST be
enforced by the harness, not by prompt discipline.

## Technology Stack

- Python 3.12, Typer (CLI), Pydantic v2 (contracts), PyYAML (configuration)
- pandas / pyarrow (tabular data and artifacts)
- scikit-learn (validation splitters and metrics)
- LightGBM and CatBoost (only model families in the MVP)
- SQLAlchemy 2 with SQLite (structured experiment registry)
- MLflow with a local file or SQLite-backed tracking store
- JSON Lines for the append-only research log
- MCP adapter exposing a narrow, allowlisted tool surface to agent runtimes
- Git for experiment lineage and rollback
- pytest / pytest-cov / pytest-timeout, Ruff, mypy

## Development Workflow

- Two loops are kept strictly separate:
  - Dev-time loop (builds the harness): human + coding agent run Spec Kit —
    Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement —
    with artifacts in `specs/NNN-<feature>/` and code in `src/`.
  - Runtime loop (harness runs a competition): human sets policy and budgets;
    an agent runtime proposes; the harness validates, executes, evaluates, and
    records. Spec Kit never sits inside the research loop.
- Spec Kit is installed as Vibe skills (`.vibe/skills/speckit-*`, invoked as
  `/speckit-*`). See `WORKFLOW.md` for the full loop.
- Layered build order: (1) CLI-only harness with a deterministic rule-based
  planner, (2) MCP adapter, (3) Goose recipe for supervised and bounded
  autonomous modes, (4) optional Zed/ACP cockpit.
- CI gates on every PR: `ruff check`, `ruff format --check`, `mypy src`,
  unit / contract / integration / acceptance tests, coverage report
  (>= 85% statement coverage; 100% branch coverage for budget enforcement,
  experiment state transitions, incumbent selection, submission validation, and
  resume safety).
- End-to-end synthetic classification and regression runs must complete within
  10 minutes on a development CPU.

## Governance

- The constitution supersedes all other practices; it is checked before planning
  and after technical design (`/speckit-analyze`). Critical findings block
  implementation.
- Versioning follows semantic versioning: MAJOR for removal or
  backward-incompatible redefinition of principles, MINOR for new principles or
  materially expanded guidance, PATCH for clarifications and non-semantic
  refinements.
- Any exception requires a written justification in the implementation plan.
- A simpler compliant design MUST be preferred over a more sophisticated one.
- Changes to validation integrity, reproducibility, safety principles, or the
  harness-authority boundary require an explicit constitution amendment with
  documentation and migration plan.

**Version**: 1.1.0 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16
