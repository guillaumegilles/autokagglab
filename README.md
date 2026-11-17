# AutoKagglab

![License](https://img.shields.io/github/license/guillaumegilles/autokagglab)
![Python](https://img.shields.io/badge/python-3.12-blue)

**An autonomous Kaggle research harness** — a local, offline-first CLI that
improves leaderboard solutions through a bounded, reproducible scientific
experimentation loop.

> The agent is **not** a notebook generator. It is an **experiment optimization
> system**: it observes results, generates hypotheses, runs experiments,
> evaluates them against frozen cross-validation, and remembers what it learned.
> Every component is judged by one question: *does this help discover better
> leaderboard solutions faster?*

The durable intellectual property is the **research protocol** — competition
config, experiment schema, immutable evaluation harness, budgets, append-only
research log, memory. Agent runtimes (Goose, Pi, …) and editors (Zed via ACP,
…) are replaceable scaffolding around that core. Core principle: **the agent
proposes; the harness disposes** — all scientific rules live in deterministic
code, never in a prompt.

---

## What it can do today (feature `001-competition-baseline`, shipped)

- **Validate** a competition workspace: fail fast on missing files, missing
  target, duplicate ids, train/test schema mismatch, unsupported metric/task —
  before any training.
- **Profile & fingerprint** the dataset: shape, dtypes, missing values, target
  distribution, identifier uniqueness, constant/likely-categorical columns,
  leakage warnings, stable dataset fingerprints.
- **Run a deterministic CV baseline** (LightGBM / CatBoost, 5-fold
  StratifiedKFold for binary classification, KFold for regression, seed 42) with
  per-fold and aggregate metrics.
- **Record everything**: SQLite registry, local MLflow run, and exactly one
  append-only entry per run in `research_log.jsonl` (schema-validated).
- **Inspect progress** via a read-only `status` command (runs, profile,
  leakage warnings, budgets, incumbent experiment).

Scope: tabular CSV · binary classification + regression · LightGBM + CatBoost ·
CPU · local · single user · **no network, no credentials, no GPU, no LLM
required**. Rerunning a baseline with unchanged inputs reproduces the aggregate
metric within **1e-6**.

## Quickstart

```bash
# Python 3.12 — install (editable, with dev tooling)
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e '.[dev]'
# or: pip install -e '.[dev]'

# 1. Generate a synthetic competition fixture
python -m tests.fixtures.make_fixture --out competitions/demo --task binary-classification

# 2. Validate the workspace (exit 0; prints the dataset profile as JSON)
kaggle-agent validate competitions/demo

# 3. Run the deterministic baseline
kaggle-agent baseline competitions/demo

# 4. Inspect runs and the incumbent
kaggle-agent status competitions/demo
```

Verified end-to-end on the synthetic fixture:

```text
runs: 2
  validate: COMPLETED (exit 0)
  baseline: COMPLETED (exit 0)
profile: 400 train rows, 120 test rows, 10 columns, id_unique=True
budgets: {'max_experiments': 10, 'experiment_timeout_seconds': 1200,
          'run_timeout_seconds': 10800, 'max_consecutive_failures': 3,
          'min_improvement': 0.001}
incumbent: exp-0001 roc_auc=0.868635 ± 0.028402
```

### CLI reference

| Command | Purpose | Exit codes |
|---|---|---|
| `kaggle-agent init <path> --task <t> --target <col> --id <col> --metric <m>` | Scaffold a workspace with a default `competition.yaml` | 0, 2 |
| `kaggle-agent validate <path> [--config <yaml>]` | Validate inputs, profile + fingerprint, record a run | 0, 2 |
| `kaggle-agent baseline <path> [--target-encoding]` | Deterministic CV baseline; optional fold-isolated target encoding | 0, 2, 3, 4 |
| `kaggle-agent status <path>` | Read-only runs / profile / incumbent summary | 0, 2 |

Exit codes: `0` ok · `2` validation error · `3` run failure · `4` budget violation.
Metrics: `roc_auc`, `log_loss` (binary) · `rmse`, `mae`, `r2` (regression).
Planned commands (features 002+): `research`, `report`, `resume`, `submission`.

### Workspace layout

```text
competitions/<slug>/
├── competition.yaml          # declarative config (name, task, target, ids, metric, cv, seed, budgets)
├── data/                     # train.csv, test.csv, sample_submission.csv (read-only at runtime)
├── registry.sqlite           # competitions, profiles, runs, experiments, results
├── research_log.jsonl        # append-only research log (contracts/research-entry.schema.json)
├── mlruns/                   # local MLflow store (params, metrics, artifacts)
└── runs/<run-id>/artifacts/
```

## How it works

```text
ResearchProgram → Hypothesis → Experiment → Result → Insight → Next Hypothesis
                 (PROPOSED → RUNNING → COMPLETED | FAILED → SUPERSEDED)
```

```text
┌──────────────────────┐   ACP (optional)   ┌──────────────────────────┐
│  Human cockpit       │ ◄────────────────► │  Agent runtime           │  Goose / Pi — proposes
│  CLI now, Zed later  │                    │  (replaceable)           │  hypotheses, interprets
└──────────────────────┘                    └───────────┬──────────────┘
                                                        │ MCP tools / CLI
                              ┌───────────────────────▼──────────────┐
                              │  kaggle-agent harness (authoritative)  │  validates, frozen CV,
                              │  src/kaggle_agent/                     │  budgets, memory, logs
                              └───────────────────────┬──────────────┘
                                                      │
                              ┌───────────────────────▼──────────────┐
                              │  Isolated execution: Python, data,   │  models, MLflow, SQLite
                              └──────────────────────────────────────┘
```

Safety is enforced in code: immutable evaluator/splits/raw data, fold-isolated
target-derived transforms, leakage preflight, experiment-count/time/failure
budgets, duplicate-experiment rejection, append-only history, no network, and no
automatic Kaggle submission (submission files are generated; upload is a
human-approved action). The full approval policy (green/amber/red) and the
domain model + JSON contracts are in [docs/02-architecture.md](docs/02-architecture.md).

## Documentation

Comprehensive docs live in [`docs/`](docs/README.md):

| Doc | Contents |
|---|---|
| [docs/01-overview.md](docs/01-overview.md) | Vision, philosophy, research model, the 13 constitution principles |
| [docs/02-architecture.md](docs/02-architecture.md) | Layers, harness internals, workspace, domain model, contracts, governance |
| [docs/03-harness-usage.md](docs/03-harness-usage.md) | CLI usage, config reference, artifacts, guarantees, tests & CI gates |
| [docs/04-automlab-lessons.md](docs/04-automlab-lessons.md) | Lessons from the `automlab/` autoresearch reference + mapping to this harness |
| [docs/05-development-workflow.md](docs/05-development-workflow.md) | The Spec Kit (SDD) workflow used to build the harness, phase gates, conventions |
| [docs/06-roadmap.md](docs/06-roadmap.md) | Roadmap 002–006 with rationale, implementation suggestions, resources |

Spec artifacts for the shipped feature: [`specs/001-competition-baseline/`](specs/001-competition-baseline/)
(spec, plan, research, data-model, contracts, quickstart, tasks, checklist).
Project constitution: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

## Roadmap

```text
001 competition baseline        ✅ shipped (validate → profile → deterministic baseline → recorded runs)
002 strategy engine             next — learn which experiment families pay off; choose the next experiment
003 auto-ensembling             blend / rank-average / stack top candidates
004 cross-competition memory    transfer insights across competitions
005 external research           forum / notebook / paper mining
006 multi-agent teams           deliberately last
```

Rationale and detail: [docs/06-roadmap.md](docs/06-roadmap.md). The behavioral
blueprint is autoresearch-style (see [`automlab/`](automlab/), a read-only
reference checkout): small editable surface, immutable evaluator, one hypothesis
per run, fixed budget, append-only ledger, git keep/reject.

## Development

The harness itself is built with **spec-driven development** (GitHub Spec Kit
skills: `speckit-constitution` → `speckit-specify` → `speckit-clarify` →
`speckit-plan` → `speckit-tasks` → `speckit-analyze` → `speckit-implement` →
`speckit-checklist`), one branch + one PR per feature. See
[docs/05-development-workflow.md](docs/05-development-workflow.md).

```bash
# lint, type-check, test — the CI gates (see .github/workflows/ci.yml)
ruff check . && ruff format --check . && mypy src
pytest tests/unit && pytest tests/contract && pytest tests/integration \
  && pytest tests/acceptance
pytest --cov=src/kaggle_agent --cov-report=term-missing   # 44 tests, fail_under = 85
```

CI thresholds: 100% of P1 acceptance and safety tests pass; ≥ 85% statement
coverage; 100% branch coverage on budget enforcement, state transitions,
incumbent selection, submission validation, and resume safety.

### Tech stack

Python 3.12 · Typer · Pydantic v2 · PyYAML · pandas/pyarrow · scikit-learn ·
LightGBM + CatBoost · SQLAlchemy 2 + SQLite · MLflow (local) · structlog ·
pytest / pytest-cov / pytest-timeout / jsonschema · Ruff · mypy.

### Repository layout

```text
├── src/kaggle_agent/         # the harness (cli / domain / application / infrastructure)
├── tests/                    # unit · contract · integration · acceptance · fixtures (44 tests)
├── specs/                    # spec-kit artifacts per feature (001-competition-baseline done)
├── docs/                     # comprehensive documentation (start at docs/README.md)
├── .specify/                 # spec-kit memory: constitution, templates, workflows
├── automlab/                 # read-only autoresearch-style reference repo (separate embedded git repo)
└── competitions/             # created at runtime — one workspace per competition
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Workflow in one line: pick the next
feature from the roadmap → `speckit-specify` on a `NNN-<name>` branch → gates →
PR with green CI.

## License

[GPL-3.0](LICENSE).
