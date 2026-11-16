# 01 — Overview: Vision, Philosophy, Principles

## What this project is

An **autonomous Kaggle research agent** whose objective is *autonomous leaderboard
improvement through the scientific method* — not code generation.

Winning Kaggle competitions is no longer primarily about model training. It is
about:

- understanding the competition,
- exploring prior solutions,
- generating hypotheses,
- running experiments,
- evaluating leaderboard impact,
- managing compute budgets,
- building ensembles.

These are agentic tasks. The system operates as a small research organization:

```text
Observe → Analyze → Hypothesize → Experiment → Evaluate → Learn → Repeat
```

## Core philosophy

> The agent is NOT a notebook generator. The agent is NOT a coding assistant.
> The agent is an **experiment optimization system**.

Every component is evaluated against one question:

> "Does this help the system discover better leaderboard solutions faster?"

The primary output of the system is **accumulated research knowledge that
improves leaderboard performance**, not generated code.

| The harness IS | The harness is NOT |
|---|---|
| An experiment optimization system | A notebook generator |
| Deterministic where science demands it (validation, budgets, memory) | A black-box LLM pipeline |
| Offline and single-user in the MVP | A cloud / multi-user platform |
| Paired with a replaceable agent runtime for reasoning | Tied to one agent, editor, or vendor |

## The research model (the critical artifact)

Everything hangs on this loop:

```text
ResearchProgram
    ↓
Hypothesis   (explicit, falsifiable, with an expected effect)
    ↓
Experiment   (one controlled change relative to a parent)
    ↓
Result       (fold-level + aggregate metrics under frozen CV)
    ↓
Insight      (structured conclusion, confidence)
    ↓
Next Hypothesis
```

Experiment state machine: `PROPOSED → RUNNING → COMPLETED | FAILED → SUPERSEDED`.

If this model is elegant, the rest of the system falls into place. If it is wrong,
no amount of agent orchestration saves the project.

## Non-negotiable principles (constitution summary)

Full text: `.specify/memory/constitution.md`. The 13 principles:

1. **Scientific Method First** — every experiment starts with an explicit,
   falsifiable hypothesis and ends with a structured result and conclusion.
   No hypothesis = invalid. No conclusion = incomplete.
2. **Reproducibility** — record source revision, config, dataset fingerprint,
   feature-set version, model family/params, seeds, CV strategy, environment,
   duration, metric. Same inputs ⇒ same metric within documented tolerance (1e-6).
3. **Validation Integrity** — model selection uses local CV, never the public
   leaderboard. Target-derived transforms are fitted inside each training fold.
   The evaluator/splits/governance are immutable during a run. Fail safely on
   leakage.
4. **Bounded Autonomy** — explicit limits: max experiments, per-experiment and
   per-run timeouts, max consecutive failures. Stop when any limit is hit. No
   automatic Kaggle submission in the MVP.
5. **Evidence-Based Selection** — compare experiments under one consistent
   validation protocol; promote only above the configured improvement threshold;
   preserve fold-level variance; worse experiments are kept as knowledge, not
   promoted.
6. **Append-Only Research Memory** — hypotheses, outcomes, failures, insights are
   append-only; corrections are new linked entries, never rewrites.
7. **Safe and Reviewable Code Execution** — experiments are declarative
   `ExperimentSpec` objects constrained to allowlisted changes, never arbitrary
   generated code; isolated working directory; read-only datasets; no network,
   credentials, or paths outside the workspace.
8. **Simplicity and Single-Agent Architecture** — one agent, one sequential loop
   in the MVP; planner behind a protocol (deterministic rule-based first, LLM
   later, off the acceptance path); new infrastructure must be justified by an
   acceptance criterion.
9. **Test-First Delivery (NON-NEGOTIABLE)** — every user story has executable
   acceptance tests; leakage, reproducibility, budget enforcement, and artifact
   validity are covered by automated tests.
10. **Traceability** — every FR maps to a user story, tasks, and acceptance tests;
    every artifact traces to the hypothesis that caused it.
11. **Harness Authority — "the agent proposes; the harness disposes"** — all
    scientific rules (validation, budgets, memory, submission validity) live in
    deterministic harness code, never in an LLM prompt.
12. **Runtime Independence** — agent runtimes (Goose, Pi) and editors (Zed via
    ACP) are replaceable; the harness core never depends on them.
13. **Human Approval for External Actions** — anything with an external effect
    (downloading data, uploading submissions, network access) requires explicit
    human approval.

## MVP scope (feature 001, shipped)

- **In:** local tabular CSV; binary classification + regression; LightGBM +
  CatBoost; CPU; single user; single agent; deterministic CV; SQLite registry;
  local MLflow; append-only JSONL research log; submission-file generation
  (no upload).
- **Out:** Kaggle API submission, leaderboard feedback, forum/notebook mining,
  ensembling, HPO frameworks, NN/vision/NLP, cross-competition memory,
  multi-agent, web UI, cloud.

## Where the design comes from

- **Autoresearch** (`karpathy/autoresearch`, mirrored locally in `automlab/`):
  small editable surface, immutable evaluator, one hypothesis per run, fixed
  budget, append-only ledger, git keep/reject. See
  [04-automlab-lessons.md](04-automlab-lessons.md).
- **Layered agent stack**: methodology = Autoresearch, runtime = Goose (or Pi),
  tools = a thin Kaggle MCP server, interface = Zed via ACP (optional cockpit).
  See [02-architecture.md](02-architecture.md).
- **Spec-driven development**: the harness itself is built with GitHub Spec Kit
  phases (Constitution → Specify → Plan → Tasks → Implement). See
  [05-development-workflow.md](05-development-workflow.md).
