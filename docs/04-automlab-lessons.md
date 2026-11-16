# 04 — Lessons from `automlab/`: the autoresearch reference

`automlab/` (read-only reference, do not edit) is a working **autoresearch-style**
repo — a local adaptation of [`karpathy/autoresearch`](https://github.com/karpathy/autoresearch)
that runs one LLM-driven experiment at a time against a fixed-budget benchmark
and keeps or rejects the change based on a single metric (`val_bpb` on a
language-model training program). It is the behavioral blueprint for this
project: **we borrow its discipline, applied to Kaggle competitions.**

## The autoresearch discipline (from `automlab/program.md` and `AGENTS.md`)

- **Small editable surface.** Edit `train.py` only; never edit `prepare.py`.
  The agent may touch a constrained part of the implementation; the evaluator
  stays immutable. This is what protects the score from being "improved" by
  changing the measurement.
- **One hypothesis per run.** Make exactly one change per experiment.
- **Fixed experiment budget.** Every run has a timed budget (300 s in automlab);
  the benchmark is run before claiming success.
- **Start from the current promoted master**, not stale history:
  `uv run scripts/refresh_master.py --fetch-dag` treats `train_orig.py`,
  `research/live/master.json`, and `research/results.tsv` as the source of truth.
- **Append-only run ledger.** `research/results.tsv` records every completed run:
  `run_id, created_at, status, job_id, campaign, experiment_id, hypothesis,
  parent_hash, candidate_hash, val_bpb, training_seconds, peak_vram_mb,
  mfu_percent, promoted, comment`.
- **Git-based keep/reject.** `uv run scripts/submit_patch.py --comment "..."`
  records the run; promotion is *local* and happens only when the observed metric
  beats the current master. Failed diffs stay in `research/diffs/` for reference.
- **Do-not-repeat ledger.** `research/do-not-repeat.md` makes failed ideas
  searchable; duplicates are defined by same parent hash + same change class +
  materially similar hypothesis.
- **Human-authored research policy.** `program.md` is written by the human; the
  agent executes it. The policy, not the prompt, carries the rules.
- **Isolated workers.** Code-mutating work happens in isolated git worktrees
  (`scripts/opencode_worker.py create/run`); `memory-keeper` is the only writer
  of durable notes; planner/reviewer/researcher/reporter are read-only.
- **Structured experiment notes.** `research/notes.md` and
  `research/experiments/*.md` follow a fixed shape: *Hypothesis → Change →
  Observed → Conclusion*. Templates live in `research/templates/`.
- **Managed execution.** Experiments run as Hugging Face Jobs
  (`scripts/hf_job.py launch --mode experiment`), metric parsed from logs
  (`scripts/parse_metric.py`), results reported to Trackio.
- **Upstream sync.** `scripts/sync_upstream.py` keeps the benchmark files aligned
  with `karpathy/autoresearch` without touching the local ledger.

## Mapping: automlab concept → autokagglab equivalent

| automlab (autoresearch) | autokagglab (this repo) |
|---|---|
| `train.py` — the only editable file | `solution/features.py`, `solution/model.py`, `solution/config.yaml` — agent-editable surface (declarative `ExperimentSpec` instead of free code) |
| `prepare.py` / evaluator — immutable | `harness/evaluate.py`, `harness/splits.py`, `governance.yaml`, `data/raw/` — protected paths; harness code in `src/kaggle_agent/domain` (splits, metrics, leakage) |
| `program.md` — human research policy | `competition.yaml` + `budgets` + constitution — declarative policy the harness enforces |
| local promoted master / `train_orig.py` | the **incumbent experiment** in `registry.sqlite` (promoted only above `min_improvement` on frozen CV) |
| `research/results.tsv` — append-only ledger | `research_log.jsonl` (append-only, schema-validated) + `registry.sqlite` + MLflow |
| `submit_patch.py` keep/reject on `val_bpb` | incumbent selection: candidate replaces incumbent only if Δmetric ≥ `min_improvement` under identical folds |
| `research/do-not-repeat.md` | duplicate detection via experiment fingerprints + research-log insights |
| one hypothesis per run, timed budget | `Hypothesis` entity + `budgets` (max_experiments, per-experiment/run timeouts, failure limit) |
| HF Jobs managed runner | isolated local runner with timeout/memory limits (feature 001); compute backend replaceable later |
| git worktrees for workers | per-run isolated directories `runs/<run-id>/`; git lineage via `git_commit` on experiments |
| `val_bpb` single objective | competition metric from `competition.yaml` (`roc_auc`, `log_loss`, `rmse`, `mae`, `r2`) under frozen CV |
| OpenCode agents/skills | replaceable agent runtime (Goose/Pi) + thin Kaggle MCP tools (later features) |

## What we adopted, and what we deliberately changed

Adopted verbatim as principles: small editable surface, immutable evaluator,
explicit objective, fixed budget, append-only history, git keep/reject,
human-authored policy.

Changed because Kaggle ≠ a single training program:

- **Richer acceptance than "metric improved, keep."** A better acceptance
  function also weighs variance across folds, runtime, leakage risk, prediction
  diversity (a slightly worse standalone model can still earn its place in an
  ensemble), and reproducibility:

  ```text
  utility = validation_gain
          - variance_penalty
          - runtime_penalty
          - leakage_risk_penalty
          + diversity_value
  ```

- **Cross-validation instead of a fixed holdout.** automlab has one validation
  metric; Kaggle needs fold-level CV with stratification and fold-isolated
  target-derived transforms (leakage control).
- **Submissions are governed, not automatic.** Public leaderboard feedback is
  sparse, limited, and exploitable; the main loop optimizes frozen out-of-fold
  validation, and submission is a human-approved action (see
  [02-architecture.md](02-architecture.md#safety--governance)).
- **Structured records over MLflow-only.** A schema-validated JSONL research log
  (hypothesis → observed → conclusion) is the primary memory; MLflow tracks
  params/metrics/artifacts alongside SQLite for structured queries.
