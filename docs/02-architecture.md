# 02 — Architecture

## The layered view

The system is deliberately split into layers so that no single vendor or tool is
load-bearing. The durable IP is the **Kaggle research core**; everything around
it is replaceable.

```text
┌─────────────────────────────────────┐
│  Human cockpit (optional)           │  CLI now; Zed via ACP later —
│  review, approve, interrupt         │  specification, diffs, approvals
└───────────────┬─────────────────────┘
                │ ACP (optional)
┌───────────────▼─────────────────────┐
│  Agent runtime (replaceable)        │  Goose (recommended) or Pi —
│  probabilistic reasoning: propose,  │  agent loop, model access, tools,
│  interpret, draft hypotheses        │  sessions, recipes
└───────────────┬─────────────────────┘
                │ MCP tools / CLI
┌───────────────▼─────────────────────┐
│  Kaggle research harness (ours)     │  AUTHORITATIVE — deterministic:
│  src/kaggle_agent/                  │  validation, frozen CV, execution,
│                                     │  budgets, memory, submission checks
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│  Isolated execution environment     │  Python 3.12, data, CV, models,
│                                     │  MLflow, SQLite, JSONL artifacts
└─────────────────────────────────────┘
                │ git + append-only lineage
┌───────────────▼─────────────────────┐
│  Platform (human-operated in MVP)   │  Kaggle CLI — manual submission
└─────────────────────────────────────┘
```

| Layer | Technology | Role | Replaceable? |
|---|---|---|---|
| Methodology | Autoresearch discipline (see `automlab/`) | Behavioral blueprint: small editable surface, immutable evaluator, keep/reject | No — this is our IP |
| Agent runtime | Goose (recommended) / Pi (alternative) | The "brain": proposes hypotheses, interprets results | Yes |
| Tools bridge | Thin Kaggle MCP server (later features) | Narrow tools: `propose_experiment`, `run_experiment`, `compare_with_incumbent`, `generate_submission`, … | Yes, thin by design |
| Harness core | `src/kaggle_agent/` CLI + Python API | The "hands": validates, executes, evaluates, remembers | No — this is our IP |
| Human interface | CLI now; Zed via ACP later | Review, approval, interruption | Yes |
| Lineage | Git + append-only JSONL | Experiment ancestry, keep/reject, audit | No |
| Platform | Official Kaggle CLI | Data download, submission (human-approved) | No |

**Harness authority** (constitution XI): the agent proposes; the harness
disposes. Scientific rules live in deterministic code, never in a prompt.
`run_experiment()` in the future MCP server must enforce fixed CV folds,
timeouts, memory limits, deterministic seeds, artifact collection, and failure
classification in code — not by asking the model nicely.

## Harness internals (`src/kaggle_agent/`)

Modular monolith with one synchronous orchestrator. Implemented today (feature
001); marked *(planned)* where WORKFLOW.md §5.3 adds them in later features.

```text
src/kaggle_agent/
├── cli/            Typer commands: init, validate, baseline, status
│                   (planned: research, report, resume, submission)
├── domain/         CompetitionConfig, entities, fingerprints, leakage,
│                   metrics, splits (frozen CV), transforms (allowlisted)
├── application/    workspace, validate_service, profile_service,
│                   baseline_service, run_service
│                   (planned: ResearchRunService, ExperimentLoop,
│                    SubmissionService, ReportService)
├── infrastructure/ SQLite registry, append-only JSONL research log,
│                   MLflow adapter, trainers (LightGBM/CatBoost)
└── (planned) models/, features/, validation/, reporting/
```

Design constraints:

- Experiments are **declarative `ExperimentSpec` objects**, never arbitrary
  generated code. Allowed MVP changes: model family (LightGBM/CatBoost),
  allowlisted hyperparameters, predefined safe feature transforms,
  missing-value strategy, categorical-handling strategy.
- **Immutable inputs**: dataset files are read-only during runs; the evaluator,
  splitter, and governance config are protected paths the agent may never touch.
- **Fingerprints** (dataset / config / experiment) give reproducibility and
  duplicate detection.
- **Explicit run-state persistence** so an interrupted run can resume.
- Planner behind a protocol: `RuleBasedPlanner` first (deterministic); an LLM
  planner comes later, off the acceptance path.

## Workspace layout on disk

```text
competitions/<slug>/
├── competition.yaml          # declarative config (see contracts)
├── data/                     # train.csv, test.csv, sample_submission.csv (read-only)
├── registry.sqlite           # structured runs / experiments / results / profile
├── research_log.jsonl        # append-only research log (one JSON entry per line)
├── mlruns/                   # local MLflow store (params, metrics, artifacts)
└── runs/<run-id>/artifacts/  # per-run artifacts (predictions, models, configs)
```

## Domain model

| Entity | Purpose | Key attributes |
|---|---|---|
| **Competition** | A validated workspace | slug, config JSON, config fingerprint → many ResearchRuns |
| **DatasetProfile** | Machine-readable profile + fingerprints of the inputs | shape, dtypes, missing, target distribution, id uniqueness, constant/likely-categorical columns, leakage warnings, fingerprints → belongs to one Competition |
| **ResearchRun** | One execution of the CLI | run_id, kind, status, budgets, timestamps, exit code → belongs to one Competition |
| **Hypothesis** | A falsifiable statement with an expected effect | statement, rationale, expected_effect |
| **Experiment** | One trained-and-evaluated candidate | experiment_id, parent_id, hypothesis, one controlled change, model family + params, feature-set version, CV strategy, seed, status, git commit, experiment fingerprint |
| **Result** | Metrics + metadata for one experiment | fold-level metrics, mean, std, direction, runtime, environment, mlflow_run_id, conclusion |
| **Insight** | What was learned | conclusion, confidence → feeds the next hypothesis |
| **ResearchLogEntry** | Append-only log line linking it all together | entry_id, timestamp, run_id, experiment_id, type, status, hypothesis, observed, conclusion, parent_entry_id |

Relationships:

```text
Competition 1──* ResearchRun 1──* Experiment 1──1 Result
                                    │
Experiment *──1 Experiment (parent/child lineage)
ResearchRun 1──* ResearchLogEntry *──1 Experiment
```

## API contracts (JSON schemas)

Machine-readable contracts live in
`specs/001-competition-baseline/contracts/`:

| Schema | Required fields |
|---|---|
| `competition-config.schema.json` | name, task, target, id_columns, metric, cv, seed, budgets |
| `hypothesis.schema.json` | statement, expected_effect |
| `experiment.schema.json` | experiment_id, run_id, hypothesis, change, model_family, params |
| `result.schema.json` | experiment_id, metric_name, direction, fold_metrics, mean, std, runtime_seconds |
| `research-entry.schema.json` | entry_id, timestamp, run_id, type, status |

These are validated by the contract test suite (`tests/contract/test_schemas.py`).

## Safety & governance

Explicit protections (constitution III, IV, VII, XIII):

- **No infinite loops / repeated experiments** — experiment-count, per-experiment
  and per-run timeouts, consecutive-failure budget; duplicate experiment
  fingerprints rejected.
- **No leakage** — leakage preflight in the profile; target-derived transforms
  fitted inside each training fold only; fail safely on confirmed leakage,
  identifier leakage, row overlap, or invalid splits.
- **No leaderboard-driven selection** — incumbent chosen by frozen local CV only.
- **No unsafe code execution** — declarative experiment specs, isolated run
  directory, read-only data, no network/credentials/outside paths.
- **Submission governance** — in the MVP, submission *files* may be generated,
  but upload to Kaggle is a human action. Target flow (later features):

```text
Experiment accepted on CV → reproduced from clean environment → leakage checks
→ materially different from prior submission → human approval → Kaggle submission
```

### Approval policy (runtime interaction model)

| Action | Policy |
|---|---|
| Read profile / research history, propose a hypothesis, run an allowlisted config within budget, reject duplicates, kill a timed-out experiment, generate a submission file | Green — autonomous |
| Change CV strategy (new run), add generated feature code, download competition data, upload to Kaggle | Amber — human approval |
| Modify protected evaluator / splits / raw data, delete experiment history, network access, auto-submit (MVP) | Red — prohibited |
