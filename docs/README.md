# AutoKagglab — Documentation

AutoKagglab is an **autonomous Kaggle research harness**: a local, offline-first
system that improves leaderboard solutions through a bounded, reproducible
scientific experimentation loop — not by generating notebooks, but by
continuously observing results, generating hypotheses, running experiments,
evaluating them against frozen cross-validation, and remembering what it learned.

The durable intellectual property of this project is the **research protocol**
(competition config, experiment schema, immutable evaluation harness, budgets,
append-only research log, memory). Agent runtimes (Goose, Pi, …) and editors
(Zed via ACP, …) are replaceable scaffolding around that core.

## Current status

| Item | State |
|---|---|
| Feature `001-competition-baseline` | Implemented — all 40 tasks in `specs/001-competition-baseline/tasks.md` are done |
| CLI | `kaggle-agent init / validate / baseline / status` (see [03-harness-usage.md](03-harness-usage.md)) |
| Scope | Tabular CSV, binary classification + regression, LightGBM/CatBoost, CPU, local, single user, no network |
| Spec artifacts | `specs/001-competition-baseline/` (spec, plan, research, data-model, contracts, quickstart, tasks, checklist) |
| Constitution | `.specify/memory/constitution.md` — 13 non-negotiable principles |
| Roadmap | `001` done → `002` strategy engine → `003` ensembling → `004` cross-competition memory → `005` external research → `006` multi-agent (see [06-roadmap.md](06-roadmap.md)) |

## Document map

| Doc | What it covers |
|---|---|
| [01-overview.md](01-overview.md) | Vision, core philosophy, non-negotiable principles, the research model (Hypothesis → Experiment → Result → Insight) |
| [02-architecture.md](02-architecture.md) | Layered architecture (methodology / runtime / interface / execution), harness internals, workspace layout, domain model, JSON contracts, safety & governance |
| [03-harness-usage.md](03-harness-usage.md) | What the harness can do today and how to use it: install, CLI reference, config schema, artifacts, guarantees, tests & CI gates |
| [04-automlab-lessons.md](04-automlab-lessons.md) | The `automlab/` autoresearch-style reference implementation and how each of its mechanisms maps onto this harness |
| [05-development-workflow.md](05-development-workflow.md) | How we build the harness itself: the SDD (Spec Kit) loop, dev-time vs runtime loops, phase gates, CI, conventions |
| [06-roadmap.md](06-roadmap.md) | Future features with rationale and suggestions: strategy engine, ensembling, cross-competition memory, external research, multi-agent — plus resources |

## Source material

These docs synthesize the project's research inputs:

- `WORKFLOW.md` — the SDD workflow, feature roadmap, anatomy of feature 001, CI gates, runtime interaction model, conventions
- `openai-research.md` — the architecture conversation: vision, layered design (Autoresearch methodology / Goose runtime / Zed cockpit), MVP spec, build-vs-reuse decisions, post-MVP priorities
- `TODO.md` — the post-MVP roadmap and rationale (strategy engine before forum mining, ensembling, cross-competition memory, multi-agent last)
- `automlab/` — a working autoresearch-style reference repo (read-only) used as the behavioral blueprint
