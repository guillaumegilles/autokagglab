You are a Principal AI Architect and Research Systems Engineer.

Your task is to design the MVP of an Autonomous Kaggle Research Agent.

The objective is not code generation.

The objective is autonomous leaderboard improvement through the scientific method.

The agent must operate as a research organization that continuously:

1. Observes competition results.
2. Generates hypotheses.
3. Runs experiments.
4. Evaluates outcomes.
5. Extracts insights.
6. Updates research memory.
7. Selects the next best experiment.

The design should take inspiration from:

- Autonomous research systems
- Experiment-driven optimization
- Scientific method workflows
- Research logging systems
- Continuous self-improving agents

Avoid designing a generic AI assistant.

Design a system optimized specifically for Kaggle competitions.

---

CORE PHILOSOPHY

The agent is NOT a notebook generator.

The agent is NOT a coding assistant.

The agent is an experiment optimization system.

Every system component should be evaluated against one question:

"Does this help the system discover better leaderboard solutions faster?"

---

MVP SCOPE

Initially support only:

- Tabular competitions
- Binary classification
- Multi-class classification
- Regression

Model families:

- LightGBM
- CatBoost
- XGBoost

Execution:

- Local machine
- Single user
- Python only

Storage:

- MLflow
- SQLite or PostgreSQL

No cloud infrastructure required.

---

OUT OF SCOPE

Do not include:

- Vision competitions
- NLP competitions
- Deep learning training
- GPU clusters
- Distributed systems
- Kubernetes
- Multi-user collaboration
- Automated paper reading
- Multi-agent swarms

These may be future extensions.

---

SECTION 1 — PRODUCT VISION

Define:

- Target user
- Problem statement
- Success metrics
- Non-goals

Answer:

What would make this system genuinely useful to an experienced Kaggle competitor?

---

SECTION 2 — DESIGN PRINCIPLES

Define principles such as:

- Experiment First
- Reproducibility Over Complexity
- Evidence-Based Decisions
- Incremental Improvements
- Memory Before Intelligence
- Failures Are Assets

Explain the rationale of each.

---

SECTION 3 — DOMAIN MODEL

Create a complete domain model.

Required entities:

Competition
Dataset
Experiment
Hypothesis
Result
Insight
FeatureSet
ModelConfiguration
Submission
LeaderboardScore
ResearchProgram

For each entity define:

- Purpose
- Attributes
- Relationships

Show a UML-style diagram.

---

SECTION 4 — RESEARCH MODEL

Design the scientific workflow.

ResearchProgram
    ↓
Hypothesis
    ↓
Experiment
    ↓
Result
    ↓
Insight
    ↓
Next Hypothesis

Define state transitions.

Example:

PROPOSED
RUNNING
COMPLETED
FAILED
SUPERSEDED

---

SECTION 5 — FUNCTIONAL REQUIREMENTS

Define requirements using IDs.

Example:

FR-001 Competition Analysis

FR-002 Baseline Generation

FR-003 Hypothesis Generation

FR-004 Experiment Execution

FR-005 Result Evaluation

FR-006 Insight Extraction

FR-007 Research Memory Update

FR-008 Next Experiment Selection

FR-009 Submission Generation

FR-010 Experiment Reproducibility

Each requirement should include:

- Description
- Inputs
- Outputs
- Acceptance Criteria

---

SECTION 6 — SYSTEM ARCHITECTURE

Design a modular architecture.

Required modules:

Competition Analyzer

Research Planner

Hypothesis Generator

Experiment Generator

Experiment Runner

Result Evaluator

Insight Extractor

Research Memory

Strategy Engine

Submission Manager

Experiment Store

MLflow Integration

Human Review Interface

For each module define:

Responsibilities

Inputs

Outputs

Dependencies

Failure modes

---

SECTION 7 — RESEARCH MEMORY

Design long-term memory carefully.

This is a first-class subsystem.

Store:

Experiment history

Hypotheses

Observations

Conclusions

Failures

Successful patterns

Leaderboard outcomes

Memory must answer questions like:

"What feature engineering approaches historically worked?"

"What experiments repeatedly failed?"

"Which model family currently dominates?"

Design:

Storage model

Retrieval strategy

Indexing

Memory lifecycle

Memory pruning

Memory summarization

---

SECTION 8 — RESEARCH LOG

Design an append-only research log.

Every experiment must create:

Hypothesis

Implementation details

Expected outcome

Observed outcome

Conclusion

Confidence level

Example structure:

Research Entry

Hypothesis:
Target encoding will improve categorical handling.

Experiment:
Added target encoding on 14 categorical features.

Result:
+0.0037 CV score.

Conclusion:
Hypothesis validated.

This research log must become part of agent memory.

---

SECTION 9 — EXPERIMENT LOOP

Design the autonomous loop.

Observe
→ Analyze
→ Hypothesize
→ Experiment
→ Evaluate
→ Learn
→ Repeat

Produce:

Sequence diagram

State machine

Decision flow diagram

Stopping criteria

Budget controls

---

SECTION 10 — SELF-EVALUATION

Design a subsystem that evaluates not only experiments but reasoning quality.

Questions include:

Was the hypothesis reasonable?

Was the experiment informative?

Was the result statistically meaningful?

Was compute wasted?

Should similar experiments be avoided?

Generate a Self-Evaluation Report after each experiment.

---

SECTION 11 — EXPERIMENT TRACKING

Use MLflow.

Track:

Parameters

Metrics

Artifacts

Generated code

CV results

Feature sets

Predictions

Submissions

Research insights

Define schemas.

---

SECTION 12 — STRATEGY ENGINE

Design a strategy engine capable of deciding:

Explore
or
Exploit

Examples:

Try new feature families

Tune hyperparameters

Switch model families

Attempt ensembling

Generate formal decision rules.

---

SECTION 13 — SAFETY & GOVERNANCE

Prevent:

Infinite loops

Repeated experiments

Data leakage

Invalid CV strategies

Overfitting to public leaderboard

Excessive compute costs

Corrupted experiment history

Unsafe code generation

Every protection should be explicit.

---

SECTION 14 — API CONTRACTS

Define JSON schemas for:

Competition

Hypothesis

Experiment

Result

Insight

Research Log Entry

Research Program

---

SECTION 15 — MVP IMPLEMENTATION PLAN

Phase 1

Competition analysis
Baseline model
MLflow tracking

Phase 2

Hypothesis generation
Experiment automation
Research memory

Phase 3

Insight extraction
Strategy engine
Automated submissions

For each phase include:

Deliverables

Risks

Exit criteria

---

SECTION 16 — FUTURE EVOLUTION

Describe evolution toward:

Discussion forum analysis

Notebook mining

Paper reading

Auto-ensembling

Meta-learning

Multi-agent research teams

Agent-of-agents orchestration

Competition portfolio management

Cross-competition knowledge transfer

---

IMPORTANT CONSTRAINTS

1. Simplicity over sophistication.

2. Every experiment must be reproducible.

3. Every decision must be traceable.

4. Every experiment must have an explicit hypothesis.

5. Every result must produce an insight.

6. Memory is more important than agent count.

7. The MVP should work effectively with a single agent.

8. Multi-agent capabilities are future enhancements.

9. The primary output of the system is not code.

10. The primary output of the system is accumulated research knowledge that improves leaderboard performance.

Produce a professional software architecture specification suitable for implementation by a senior engineering team.
