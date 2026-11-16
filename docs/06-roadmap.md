# 06 — Roadmap: future features, rationale, and suggestions

## The roadmap at a glance

```text
MVP (001)  Competition analysis · baseline · bounded experiment loop
           · research log · MLflow · memory            ✅ shipped
   │
   ▼
V2 (002)   Strategy Engine — a better experiment chooser
   │
   ▼
V3 (003)   Automatic Ensembling — blend / rank-average / stack
   │
   ▼
V4 (004)   Cross-Competition Memory — transferable ML research knowledge
   │
   ▼
V5 (005)   External research — forum mining, notebook mining, papers
   │
   ▼
V6 (006)   Multi-agent research teams — deliberately last
```

Each item is its own spec-kit feature (own branch, spec, plan, tasks — see
[05-development-workflow.md](05-development-workflow.md)).

## Why this order

After a few hundred experiments, the bottleneck changes:

```text
Initially:   Problem: no experiments exist.
Later:       Problem: too many possible experiments.
```

The real challenge becomes: **which experiment should I run next?** That is where
a human Kaggle Grandmaster spends much of their value. So:

- **Strategy Engine before forum mining.** External knowledge = *more ideas*;
  the strategy engine = *better selection of ideas*. A mediocre set of ideas
  selected intelligently often outperforms a huge set selected randomly.
- **Single well-designed agent before multi-agent.** A single agent with strong
  memory and a strong strategy engine usually outperforms a swarm of agents that
  cannot prioritize experiments.
- **One correction to the naive greedy loop:** the first post-MVP work should
  also make the loop an **experiment portfolio manager** — branch from several
  strong parent solutions instead of keeping only one incumbent. A greedy
  keep/reject loop can get stuck on a local optimum; a small frontier of
  candidates preserves diversity and prepares the ground for ensembling (V3).

## V2 — Strategy Engine (feature 002): meta-learning / research strategy

Not a better model generator — a better **experiment chooser**.

- **Input:** research log, experiment history, leaderboard scores, insights.
- **Output:**

  ```yaml
  recommended_direction: feature_engineering
  confidence: 0.82
  reason: Last 25 experiments indicate feature changes
          have produced 85% of total score gains.
  ```

- **Mechanism sketch:** aggregate score gains by experiment family (feature
  engineering / hyperparameters / model family / ensembling). Example: 50
  feature experiments → +0.025, 20 hyperparameter → +0.003, 10 model switches →
  +0.002 ⇒ next effort focuses on features. This is the agent learning *how to
  research*.
- **Explore vs exploit:** the strategy engine also decides when to try new
  feature families vs tune what works (formal decision rules over the research
  log, not vibes).

## V3 — Automatic Ensembling (feature 003)

A large share of Kaggle ranking comes from blending, rank averaging, stacking,
and weighted ensembles. The agent should automatically discover:

```text
Model A: 0.812
Model B: 0.811
Model C: 0.809
Ensemble: 0.818
```

Often one of the highest-ROI capabilities to add. Depends on the V2 portfolio
(frontier of candidates) and on the diversity term in the acceptance function
([04-automlab-lessons.md](04-automlab-lessons.md)).

## V4 — Cross-Competition Memory (feature 004)

Transfer learned patterns across competitions:

```text
Competition 1: Credit Risk      ┐
Competition 2: Fraud Detection ├─►  "target encoding often helps",
Competition 3: Customer Churn   ┘  "CatBoost handles high-cardinality
                                   categoricals well", "adversarial validation
                                   detects leaderboard shakeup risk"
```

Every new competition then starts with accumulated experience. At that point the
agent looks less like a competition-specific tool and more like an actual
machine-learning researcher. Storage: the research memory plus a queryable
insight store (vector DB such as Qdrant/LanceDB is a candidate here, not before).

## V5 — External research (feature 005)

Forum mining, public-notebook mining, paper reading — a Kaggle-specific "deep
research" component. Studies the discussion forum, previous competitions, public
notebooks, and papers; stores findings in memory (e.g. "CatBoost performs well
here, frequency encoding helps, rank averaging is common, adversarial validation
is useful").

## V6 — Multi-agent research teams (feature 006)

Only after 001–005 prove out. Possible decomposition: Competition Analyzer,
Research Agent, Feature Engineering Agent, Modeling Agent, Experiment Manager,
Ensemble Agent, Submission Agent, Strategy Agent — orchestrated behind the same
harness (which stays the single authority on validation, budgets, and memory).

## Implementation suggestions (from the architecture research)

- **Agent runtime:** reuse Goose (or Pi) as the runtime — agent loop, model
  access, tool calling, sessions, recipes. A competition *recipe* packages
  instructions, parameters (`competition_slug`, `time_budget_minutes`,
  `maximum_experiments`), extensions, and a structured experiment-report schema.
- **Thin Kaggle MCP server** exposing high-level, safe tools:
  `inspect_competition()`, `profile_dataset()`, `create_baseline()`,
  `propose_experiment()`, `run_experiment()`, `evaluate_predictions()`,
  `compare_experiments()`, `record_insight()`, `create_submission()`,
  `request_submission_approval()`. Enforcement (fixed folds, timeouts, seeds,
  artifact collection, failure classification) lives in the tool code, not the
  prompt.
- **Human cockpit:** connect the runtime to Zed via ACP for reviewing hypotheses,
  diffs, experiment summaries, approving submissions, and interrupting runs.
  Optional — the CLI remains the stable interface.
- **Leaderboard strategy (later):** understand public/private split, estimate
  shake-up risk (adversarial validation), and plan submission allocation
  (e.g. 5/day → 2 exploration, 2 exploitation, 1 ensemble). Model selection
  itself never uses the public leaderboard.
- **Experiment record** (target shape for the loop, extending feature 001's
  schema):

  ```json
  {
    "experiment_id": "exp-0007",
    "parent_id": "exp-0004",
    "hypothesis": "Frequency encoding will improve high-cardinality categoricals.",
    "expected_effect": "Increase mean CV AUC by at least 0.001.",
    "files_changed": ["solution/features.py"],
    "budget_seconds": 1200,
    "metric": { "name": "roc_auc", "mean": 0.8421, "std": 0.0019 },
    "baseline_metric": 0.8404,
    "runtime_seconds": 684,
    "status": "accepted",
    "conclusion": "Validated with consistent improvements across four of five folds.",
    "git_commit": "abc123",
    "next_candidates": ["Combine frequency encoding with CatBoost"]
  }
  ```

- **Self-evaluation after each experiment:** was the hypothesis reasonable? was
  the experiment informative? was the result statistically meaningful? was
  compute wasted? should similar experiments be avoided? Emit a self-evaluation
  report alongside every result.
- **Defer until the protocol is stable:** MLflow-only tracking is already in;
  add a vector DB and a strategy service only once the experiment schema and
  acceptance function are proven.

## Out of scope for the foreseeable roadmap

Vision/NLP competitions, deep-learning training, GPU clusters, distributed
systems, Kubernetes, multi-user collaboration, web UI, cloud execution,
autonomous Kaggle uploads in the MVP. Success is objectively measurable
(leaderboard score), experiments are cheap, and the feedback loop is tight —
that is what makes this domain realistic for autonomous AI.

## Resources

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — the
  autoresearch pattern (mirrored locally in `automlab/`)
- `automlab/` — working reference: see [04-automlab-lessons.md](04-automlab-lessons.md)
- `openai-research.md` — full architecture conversation (vision, layered stack,
  MVP spec, post-MVP priorities)
- `TODO.md` — original roadmap notes
- `WORKFLOW.md` — SDD workflow and feature anatomy
