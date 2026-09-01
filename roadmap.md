# Roadmap

## 3 Layers System

1. Autoresearch as the research methodology
2. Goose as the initial agent runtime
3. Zed as the human supervision interface

┌─────────────────────────────────────┐
│               Zed                   │
│  Specification, review, control     │
│  experiment browsing, code diffs    │
└─────────────────┬───────────────────┘
                  │ ACP
                  ▼
┌─────────────────────────────────────┐
│              Goose                  │
│ Agent loop, model access, tools,    │
│ shell execution, files, sessions    │
└─────────────────┬───────────────────┘
                  │ MCP / CLI
                  ▼
┌─────────────────────────────────────┐
│       Kaggle Research System        │ 
│  program.md                         │
│  competition.yaml                   │
│  experiments/                       │
│  research_log.jsonl                 │
│  runner.py                          │
│  evaluate.py                        │
│  memory.py                          │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│        Isolated ML runtime         │
│  Python, data, CV, models, MLflow  │
└─────────────────────────────────────┘


Zed and Goose are **replaceable infrastructure**. Your durable intellectual
property should be the Kaggle research protocol, experiment schema, evaluation
harness, memory, and accumulated competition knowledge.

### The role of each component

#### Autoresearch: the behavioral blueprint

Autoresearch is deliberately narrow. The agent reads human-authored research
instructions from `program.md`, modifies a constrained part of the
implementation, runs a fixed-budget experiment, evaluates one objective, and
keeps or rejects the change.

For your system, this becomes:

```
Human edits:
    program.md
    competition.yaml
    constraints.yaml

Agent may edit:
    solution/features.py
    solution/model.py
    solution/config.yaml

Agent must not edit:
    evaluation.py
    splits.py
    governance.py
    data/raw/
```

> This is more important than multi-agent orchestration. The immutable evaluation
> harness protects the system from improving its score by accidentally changing
> validation or introducing leakage.

I would borrow these Autoresearch principles:

- Small editable surface
- Immutable evaluator
- Explicit objective
- Fixed experiment budget
- Append-only experiment history
- Git-based keep/reject mechanism
- Human-authored research policy

But Kaggle needs a richer decision than a simple “metric improved, therefore
keep.” You also care about runtime, variance across folds, leakage risk,
prediction diversity, and reproducibility.

A better acceptance function is:

```
utility =
    validation_gain
    - variance_penalty
    - runtime_penalty
    - leakage_risk_penalty
    + diversity_value
```

An experiment that slightly reduces standalone CV performance might still be
valuable if its predictions are sufficiently different to improve an ensemble.

#### Goose: the runtime you probably do not need to build

Goose already provides the generic capabilities your Kaggle agent requires:

- agent interaction loop
- local command execution
- file reading and modification
- model-provider abstraction
- tool integrations through MCP
- CLI and desktop interfaces
- reusable workflows through recipes

Its architecture separates the interface, agent core, and connected extensions.
Its extensions expose tools through MCP, and Goose can also run as an ACP server
for editors such as Zed.

> Goose recipes are particularly relevant because they package instructions, prompts,
model configuration, parameters, extensions, and structured response schemas into
reusable YAML or JSON workflows.

That maps naturally to a competition recipe:

```yaml
version: "1.0.0"
title: "Kaggle Tabular Autoresearch"

instructions: |
  Read program.md and competition.yaml.
  Run exactly one controlled experiment.
  Do not modify the evaluation harness.
  Record the hypothesis before changing code.
  Roll back failed experiments.
  Return a structured experiment report.

parameters:
  competition_slug:
    type: string

  time_budget_minutes:
    type: integer
    default: 20

  maximum_experiments:
    type: integer
    default: 10

extensions:
  - developer
  - kaggle-research
```

Goose should initially be the executor, **not the owner of your Kaggle domain
logic**.

Your custom code should tell Goose:

- what an experiment is
- what files may be changed
- how datasets must be handled
- how CV is frozen
- how results are evaluated
- when a submission is permissible
- what evidence must be logged
- Build a thin Kaggle MCP server

Rather than writing a large Goose fork, I would create a small, domain-specific
MCP server exposing controlled tools:

```python
inspect_competition()
profile_dataset()
create_baseline()
propose_experiment()
run_experiment()
evaluate_predictions()
compare_experiments()
record_insight()
create_submission()
request_submission_approval()
```

Goose already treats MCP servers as extensions providing agent tools.

The tools should be high-level and safe. Avoid giving the model only an
unrestricted shell and expecting it to manage scientific integrity through
prompting.

For example, run_experiment() should automatically enforce:

1. fixed CV folds
2. timeout
3. memory limits
4. deterministic seeds
5. artifact collection
6. metric extraction
7. environment snapshot
8. failure classification

> This moves correctness out of the prompt and into deterministic code.

#### Zed: the cockpit, not the engine

Zed supports extensions for languages, debuggers, themes, MCP servers, and
agent servers.

More importantly, Zed supports external agents through ACP. In this model, Zed
hosts the thread and editor experience, while the external agent owns its
runtime, authentication, model selection, tools, and configuration.

Goose supports operating as an ACP server, and Goose is listed among ACP-compatible
agents. Therefore, I would not build a conventional Zed extension first. I would
connect Goose to Zed through ACP and use Zed for:

- editing program.md
- reviewing proposed hypotheses
- inspecting code changes
- viewing experiment summaries
- approving submissions
- interrupting autonomous runs
- comparing accepted and rejected changes

ACP standardizes communication between agents and editors, including local
subprocess communication over JSON-RPC and editor-oriented concepts such as
diffs.

That gives you the interface benefits without coupling the Kaggle agent to one
editor.

### What this means for the MVP

#### MVP objective

Starting from a prepared tabular competition workspace, run ten reproducible
autonomous experiments and produce a better cross-validation result without
changing the evaluation protocol.

Notice what is missing:

- automatic forum research
- automatic Kaggle submissions
- vector database
- elaborate web dashboard
- multi-agent system
- cross-competition learning
- advanced strategy engine

#### Minimal MVP components

```
kaggle-agent/
├── program.md
├── competition.yaml
├── governance.yaml
├── solution/
│   ├── features.py
│   ├── model.py
│   └── config.yaml
├── harness/
│   ├── evaluate.py
│   ├── splits.py
│   ├── runner.py
│   └── compare.py
├── experiments/
│   └── results.jsonl
├── artifacts/
├── recipe.yaml
└── README.md
```

##### Immutable files

- `harness/evaluate.py`
- `harness/splits.py`
- `governance.yaml`
- `data/raw/`

##### Agent-editable files

- `solution/features.py`
- `solution/model.py`
- `solution/config.yaml`

##### Append-only files

- `experiments/results.jsonl`

##### Experiment record

Every run should produce something like:

```json
{
  "experiment_id": "exp-0007",
  "parent_id": "exp-0004",
  "hypothesis": "Frequency encoding will improve high-cardinality categoricals.",
  "expected_effect": "Increase mean CV AUC by at least 0.001.",
  "files_changed": [
    "solution/features.py"
  ],
  "budget_seconds": 1200,
  "metric": {
    "name": "roc_auc",
    "mean": 0.8421,
    "std": 0.0019
  },
  "baseline_metric": 0.8404,
  "runtime_seconds": 684,
  "status": "accepted",
  "conclusion": "Validated with consistent improvements across four of five folds.",
  "git_commit": "abc123",
  "next_candidates": [
    "Combine frequency encoding with CatBoost",
    "Test count encoding with smoothing"
  ]
}
```

The Kaggle CLI supports competition discovery, data download, submissions,
submission history, leaderboard access, notebook operations, and discussion
browsing. That does not mean the agent should submit after each experiment.

The primary optimization target should remain frozen out-of-fold validation.
Public leaderboard feedback is sparse, limited, and exploitable. Submission
should therefore be a governed action:

```
Experiment accepted on CV
        ↓
Reproduced from clean environment
        ↓
Passed leakage checks
        ↓
Materially different from prior submission
        ↓
Human approval
        ↓
Kaggle submission
```

For the MVP, I would generate submission files but require manual approval
before uploading them.

### Build versus reuse

#### Reuse

1. Goose for the generic agent runtime, model access, sessions, tool calling,
  and recipes.
2. Zed + ACP for human interaction, code review, and supervision.
3. Kaggle CLI for official platform operations.
4. Git for experiment lineage and rollback.

#### Build

competition specification
immutable evaluation harness
experiment schema
research policy
leakage controls
experiment comparison logic
Kaggle-specific MCP tools
keep/reject policy
Defer
custom agent harness
custom Zed user interface
multi-agent planning
semantic memory
autonomous submissions
notebook and forum mining
cross-competition meta-learning
My revised recommendation

I would now formulate the project as:

> A Kaggle Autoresearch recipe and MCP extension for Goose, supervised through
any ACP-compatible editor, initially Zed.

The architecture becomes:

- **Methodology**: Autoresearch
- **Runtime**:     Goose
- **Tools**:       Kaggle MCP server
- **Interface**:   Zed through ACP
- **Execution**:   isolated Python environment
- **Lineage**:     Git + append-only JSONL
- **Platform**:    official Kaggle CLI

## Next Features

The first feature after MVP should then not be a strategy engine. It should be
a robust experiment portfolio manager that supports branching from several
strong parent solutions, rather than maintaining only one incumbent. A greedy
keep-or-reject loop can get stuck on a local optimum. Maintaining a small
frontier of candidates preserves diversity and prepares the system for
ensembling later.

> So yes, I would rethink the project substantially: build less infrastructure,
formalize the experiment contract more rigorously, and use Goose plus ACP as
replaceable scaffolding around an Autoresearch-style Kaggle core.

## Kaggle Titanic Onboarding

Create a tutorial with Kaggle Titanic competition to slowly walk throught the
harness and its capabillities.

--- 

- no automatic Kaggle submission;
- no leaderboard feedback;
- no external research;
- no notebook or forum mining;
- no ensembling;
- no multi-agent workflow;
- no web interface

---

first analyse step : detailed EDA