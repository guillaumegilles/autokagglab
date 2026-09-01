Yes. I would implement the MVP as a single vertical slice in GitHub Spec Kit, rather than specifying the entire long-term platform at once. The slice should prove one outcome: given a prepared tabular dataset and competition configuration, the system can create a baseline, run several reproducible experiments, retain improvements, and produce a valid submission artifact.

GitHub Spec Kit’s standard flow is Constitution → Specify → Plan → Tasks → Implement, with Markdown artifacts feeding each subsequent phase. Its specification template emphasizes independently testable user stories and Given/When/Then acceptance scenarios, which fits this project particularly well.

1. MVP outcome
MVP statement

Given a local, Kaggle-style tabular dataset and a declarative competition configuration, the agent autonomously builds a valid baseline, proposes and executes bounded experiments, records the hypotheses and results, selects the best experiment using cross-validation, and generates a reproducible submission file and research report.

MVP boundaries
Included
Local tabular datasets
Binary classification
Regression
CSV input
LightGBM and CatBoost
CPU execution
One agent
One competition at a time
Deterministic cross-validation
Bounded autonomous experiment loop
SQLite experiment registry
MLflow artifact and metric tracking
Append-only research log
Submission file generation
CLI interface
Explicitly excluded
Kaggle API submission
Public leaderboard feedback
Forum and notebook mining
Hyperparameter optimization frameworks
Cross-competition memory
Multi-agent orchestration
Ensembling
Neural networks
Image, text and time-series competitions
Web interface
Cloud execution

This scope prevents the MVP from becoming an orchestration platform before the experiment loop itself has been validated.

2. Recommended Spec Kit feature

Treat the entire MVP as one feature:

001-autonomous-experiment-loop


Recommended repository artifacts:

.specify/
├── memory/
│   └── constitution.md
└── feature.json

specs/
└── 001-autonomous-experiment-loop/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── competition-config.schema.json
    │   ├── hypothesis.schema.json
    │   ├── experiment.schema.json
    │   ├── result.schema.json
    │   └── research-entry.schema.json
    └── tasks.md


This follows Spec Kit’s intended artifact structure, where the implementation plan can produce research.md, data-model.md, quickstart.md, and contracts before task generation.

3. Phase 0: Initialize Spec Kit

The exact commands can vary slightly by the coding-agent integration, but Spec Kit documents specify init as the initialization entry point and /speckit.* as the common command form.

specify init


Select your preferred agent integration. For a new Python repository, I would then create:

kaggle-research-agent/
├── src/
├── tests/
├── examples/
├── pyproject.toml
└── README.md
``````

Do not manually create the feature specification files if the Spec Kit commands are managing them.

## 4. Phase 1: Project constitution

### Constitution prompt

```
Create the project constitution for an autonomous Kaggle research agent.

The project's purpose is to improve machine-learning solutions through a
bounded, reproducible scientific experimentation loop.

Establish the following non-negotiable principles:

I. Scientific Method First

Every experiment MUST begin with an explicit, falsifiable hypothesis.
Every completed experiment MUST produce a structured result and conclusion.
An experiment without a hypothesis is invalid.
A result without a conclusion is incomplete.

II. Reproducibility

Every experiment MUST record:
- source-code revision
- competition configuration
- dataset fingerprint
- feature-set version
- model family
- model parameters
- random seeds
- cross-validation strategy
- environment metadata
- execution duration
- evaluation metric

Rerunning an experiment with the same inputs MUST reproduce its metric within
a documented numerical tolerance.

III. Validation Integrity

Model selection MUST use local cross-validation, never the Kaggle public
leaderboard.
Training data MUST remain isolated from validation data.
Target-derived transformations MUST be fitted inside each training fold.
The system MUST fail safely if it detects target leakage, identifier leakage,
row overlap, or an invalid split configuration.

IV. Bounded Autonomy

Every autonomous research run MUST have explicit limits for:
- maximum number of experiments
- maximum duration per experiment
- maximum duration for the research run
- maximum number of consecutive failures

The agent MUST stop when any limit is reached.
The agent MUST NOT submit automatically to Kaggle in the MVP.

V. Evidence-Based Selection

The system MUST compare experiments using a consistent validation protocol.
An experiment MUST NOT replace the incumbent unless it satisfies the configured
improvement threshold.
Metric variance and fold-level results MUST be preserved.
A worse experiment may be retained as knowledge but not promoted as incumbent.

VI. Append-Only Research Memory

Hypotheses, experiment outcomes, failures, and insights MUST be written to an
append-only research log.
Historical records MUST NOT be silently rewritten.
Corrections MUST be represented as new linked entries.

VII. Safe and Reviewable Code Execution

Generated experiment changes MUST be constrained to declared extension points.
The runner MUST execute experiments in an isolated working directory.
Dataset source files and accepted experiment artifacts MUST be read-only during
execution.
No generated code may access network services, credentials, or paths outside
the workspace.

VIII. Simplicity and Single-Agent Architecture

The MVP MUST use one agent and one sequential experiment loop.
New infrastructure MUST be justified by a current acceptance criterion.
Multi-agent orchestration, distributed execution, cloud infrastructure, and a
web UI are prohibited in the MVP.

IX. Test-First Delivery

Each user story MUST have executable acceptance tests.
Critical data leakage, reproducibility, budget enforcement, and artifact
validity behavior MUST be covered by automated tests.
No user story is complete until its independent acceptance tests pass.

X. Traceability

Every functional requirement MUST map to:
- at least one user story
- one or more implementation tasks
- one or more acceptance tests

Every experiment artifact MUST be traceable to the hypothesis that caused it.

Governance:

- Constitution checks are mandatory before planning and after technical design.
- Any exception requires a written justification in the implementation plan.
- A simpler compliant design MUST be preferred over a more sophisticated one.
- Changes to validation integrity, reproducibility, or safety principles require
  an explicit constitution amendment.

Constitution acceptance gate

The constitution passes when:

It defines mandatory experiment metadata.
It prohibits leaderboard-driven model selection.
It establishes compute and iteration limits.
It makes the research log append-only.
It prohibits multi-agent design in the MVP.
It requires acceptance tests and requirement traceability.
```

## 5. Phase 2: Specify the MVP

### MVP specification prompt

```
Build the MVP of an autonomous Kaggle research agent.

The system is a local Python CLI application for a single user. It accepts:

1. A directory containing train.csv, test.csv, and sample_submission.csv.
2. A YAML competition configuration describing:
   - competition name
   - task type: binary classification or regression
   - target column
   - identifier column or columns
   - evaluation metric
   - cross-validation strategy
   - random seed
   - experiment and time budgets

The system must validate the input contract and create a Competition record.

The system must inspect the dataset and produce a machine-readable competition
profile covering:
- row and column counts
- column types
- missing values
- target distribution
- identifier uniqueness
- constant columns
- likely categorical columns
- likely leakage risks
- dataset fingerprints

The system must generate and execute a deterministic baseline using LightGBM
or CatBoost. It must evaluate the baseline using the configured cross-validation
strategy and record fold-level and aggregate metrics.

After the baseline, the system must run a bounded autonomous experiment loop.
For every experiment, it must:

1. Observe the current incumbent and prior research log.
2. propose exactly one explicit hypothesis;
3. define one controlled change;
4. predict the expected outcome;
5. execute the experiment;
6. evaluate it with the same validation protocol;
7. compare it with the incumbent;
8. write an append-only research entry;
9. retain or reject it;
10. stop when the configured budget is exhausted.

Allowed experiment changes in the MVP are restricted to:

- selecting LightGBM or CatBoost;
- modifying an allowlisted set of model parameters;
- enabling or disabling predefined safe feature transformations;
- changing missing-value handling from a predefined strategy catalog;
- changing categorical handling from a predefined strategy catalog.

The agent must not freely rewrite the runner, evaluator, storage system,
validation splitter, or submission validator.

The system must use:

- SQLite for structured competition, hypothesis, experiment, result and insight
  records;
- MLflow for parameters, metrics and artifacts;
- an append-only JSON Lines research log;
- local filesystem storage for predictions, models, configurations and reports.

The system must produce:

- best experiment reference;
- out-of-fold predictions;
- test predictions;
- submission.csv;
- research-report.md;
- machine-readable run-summary.json.

The submission must preserve the sample submission row count, identifier values,
column order and prediction column names.

MVP scope:

- tabular CSV data only;
- binary classification and regression only;
- LightGBM and CatBoost only;
- CPU only;
- local execution;
- single user;
- single agent;
- sequential experiments;
- no automatic Kaggle submission;
- no leaderboard feedback;
- no external research;
- no notebook or forum mining;
- no ensembling;
- no multi-agent workflow;
- no web interface.

Prioritize user stories as follows:

P1: Validate a competition and produce a reproducible baseline.

P1: Execute a bounded hypothesis-driven experiment loop and retain the best
local-validation result.

P1: Generate a structurally valid Kaggle submission and research report.

P2: Resume an interrupted research run without repeating completed experiments.

P2: Explain why each experiment was accepted, rejected or failed.

Define independently testable acceptance scenarios in Given/When/Then form.

Define measurable success criteria without prescribing implementation details.

Include edge cases covering:

- missing input files;
- missing target;
- duplicate identifiers;
- train/test schema mismatch;
- unsupported metric;
- too-small datasets;
- imbalanced binary target;
- constant features;
- missing values;
- target leakage;
- experiment timeout;
- model failure;
- NaN metric;
- duplicate experiment proposal;
- interrupted execution;
- invalid submission shape;
- attempts to exceed research budget.
```

## 6. Functional requirements

The generated `spec.md` should contain at least the following requirements.

### Competition ingestion

FR-001: The system MUST accept a dataset directory and competition configuration.
FR-002: The system MUST verify the presence and readability of all required files.
FR-003: The system MUST validate the target, identifiers, task type, metric and split configuration.
FR-004: The system MUST fingerprint the input datasets without modifying them.
FR-005: The system MUST reject incompatible train, test and submission schemas.

### Analysis and baseline

FR-006: The system MUST create a structured dataset profile.
FR-007: The system MUST detect common leakage and validation risks.
FR-008: The system MUST create at least one valid baseline.
FR-009: The baseline MUST use deterministic cross-validation.
FR-010: The system MUST record fold-level and aggregate metrics.

### Experiment loop

FR-011: Every experiment MUST reference exactly one hypothesis.
FR-012: Every experiment MUST contain one controlled change relative to a parent.
FR-013: The system MUST reject duplicate experiment configurations.
FR-014: All experiments MUST use the baseline validation protocol.
FR-015: The system MUST enforce experiment-count and time budgets.
FR-016: Failed experiments MUST be recorded and MUST NOT terminate the full run unless the failure budget is exhausted.
FR-017: The system MUST select an incumbent using the configured optimization direction and minimum improvement threshold.
FR-018: Every result MUST produce a structured conclusion.

### Storage and traceability

FR-019: The system MUST persist competition, hypothesis, experiment, result and insight records.
FR-020: The system MUST track parameters, metrics and artifacts in MLflow.
FR-021: The system MUST maintain an append-only research log.
FR-022: Every artifact MUST be traceable to its experiment and hypothesis.
FR-023: An interrupted run MUST be resumable.

### Outputs

FR-024: The best experiment MUST generate out-of-fold predictions.
FR-025: The best experiment MUST generate test predictions.
FR-026: The system MUST validate submission structure against sample_submission.csv.
FR-027: The system MUST generate submission.csv, run-summary.json, and research-report.md.
FR-028: The system MUST exit with a non-zero status when no valid baseline can be produced.

## 7. User stories and acceptance tests

US1, Create a reproducible baseline

Priority: P1
 Independent value: The user can obtain a trustworthy local benchmark before enabling autonomous experiments.

AT-001: Valid classification baseline
Feature: Reproducible baseline generation

  Scenario: Generate a baseline for a valid binary classification dataset
    Given a dataset directory contains train.csv, test.csv, and sample_submission.csv
    And the configuration declares a binary target and ROC AUC metric
    And the identifier is unique in both train and test data
    When the user runs the baseline command
    Then the system creates a competition profile
    And executes the configured number of validation folds
    And stores one metric for every fold
    And stores the aggregate validation score
    And creates an MLflow run
    And writes a completed baseline experiment to the research log
    And exits with status 0

AT-002: Deterministic reproduction
Scenario: Reproduce an unchanged baseline
  Given a completed baseline experiment
  When the same dataset, configuration, source revision, and random seed are used
  Then the second run has the same dataset fingerprint
  And the same cross-validation assignments
  And the aggregate metric differs by no more than 0.000001
  And the generated predictions differ by no more than the documented tolerance

AT-003: Missing target rejection
Scenario: Reject a training dataset without its configured target
  Given train.csv does not contain the configured target column
  When the competition is validated
  Then validation fails before model training
  And the error identifies the missing target column
  And no completed experiment is recorded
  And the process exits with a non-zero status

AT-004: Train-test schema mismatch
Scenario: Reject an unexplained feature-schema mismatch
  Given train.csv contains a required feature absent from test.csv
  When the competition is validated
  Then validation fails before cross-validation
  And the schema difference is reported

AT-005: Leakage-safe transformations
Scenario: Fit target-derived transformations within each fold
  Given a predefined target-dependent transformation is enabled
  When cross-validation is executed
  Then the transformation for each validation fold is fitted only on that fold's training rows
  And no validation target value is accessible during fitting

US2, Run bounded hypothesis-driven experiments

Priority: P1
 Independent value: The system can autonomously test improvements without uncontrolled execution.

AT-006: Complete a bounded loop
Feature: Autonomous experiment loop

  Scenario: Run three experiments after the baseline
    Given a valid baseline has completed
    And the research budget permits exactly three additional experiments
    When autonomous research starts
    Then no more than three additional experiments are started
    And every started experiment references exactly one hypothesis
    And every hypothesis defines an expected outcome
    And every completed experiment records a result and conclusion
    And the system stops after the third experiment

AT-007: Promote an improved experiment
Scenario: Replace the incumbent with a meaningful improvement
  Given the incumbent score is 0.8000
  And higher metric values are better
  And the minimum improvement threshold is 0.0010
  When a candidate produces a score of 0.8030 using the same validation folds
  Then the candidate becomes the incumbent
  And the decision records an improvement of 0.0030
  And the research log marks the hypothesis as supported

AT-008: Reject an insignificant experiment
Scenario: Retain knowledge without promoting an insignificant improvement
  Given the incumbent score is 0.8000
  And the minimum improvement threshold is 0.0010
  When a candidate produces a score of 0.8005
  Then the incumbent remains unchanged
  And the candidate result remains stored
  And the conclusion states that the improvement was below the threshold

AT-009: Reject duplicate proposals
Scenario: Avoid repeating an equivalent experiment
  Given an experiment with a normalized configuration fingerprint already exists
  When the planner proposes an equivalent configuration
  Then the experiment is not executed
  And a duplicate-proposal event is recorded
  And the proposal does not consume a completed-experiment slot

AT-010: Enforce timeout
Scenario: Stop an experiment that exceeds its time budget
  Given the per-experiment timeout is 60 seconds
  When an experiment runs for more than 60 seconds
  Then its process is terminated
  And its status becomes TIMED_OUT
  And the timeout is appended to the research log
  And the loop may continue if the failure budget remains

AT-011: Handle model failure
Scenario: Continue after a recoverable model failure
  Given the consecutive failure limit is two
  When the first candidate raises a model-training exception
  Then the experiment is marked FAILED
  And the exception is stored without secrets
  And the incumbent remains unchanged
  And the planner may select another experiment

AT-012: Stop after repeated failure
Scenario: Stop after exhausting the failure budget
  Given the consecutive failure limit is two
  When two consecutive experiments fail
  Then no further experiment is started
  And the run status becomes STOPPED_FAILURE_BUDGET
  And a final summary explains the stopping reason

AT-013: Prevent unconstrained changes
Scenario: Reject a change outside approved extension points
  Given the experiment proposal attempts to modify the validation splitter
  When the proposal is validated
  Then the proposal is rejected before execution
  And the protected source file remains unchanged
  And a policy violation is logged

US3, Generate a valid submission and research report

Priority: P1
 Independent value: The user receives competition-ready predictions and an auditable account of the research.

AT-014: Produce a structurally valid submission
Feature: Submission generation

  Scenario: Generate a submission from the best experiment
    Given at least one valid experiment has completed
    And the best experiment has generated test predictions
    When output generation runs
    Then submission.csv has the same number of rows as sample_submission.csv
    And identifier values match sample_submission.csv in the same order
    And column names and column order match sample_submission.csv
    And prediction values contain no NaN or infinite values

AT-015: Reject invalid predictions
Scenario: Refuse a submission containing invalid values
  Given the best experiment's test predictions contain NaN values
  When submission generation runs
  Then no validated submission is published
  And the run summary identifies the invalid prediction count
  And the process exits with a non-zero status

AT-016: Generate traceable report
Scenario: Generate an auditable research report
  Given the research run has completed
  When report generation runs
  Then research-report.md identifies the dataset fingerprint
  And documents the validation strategy
  And lists every hypothesis in execution order
  And records each result and disposition
  And identifies the best experiment
  And states the stopping reason
  And links the final submission to its source experiment

US4, Resume an interrupted run

Priority: P2
 Independent value: Long research sessions can recover without wasting compute.

AT-017: Resume without rerunning completed work
Feature: Research run recovery

  Scenario: Resume an interrupted research run
    Given a research run contains one completed experiment
    And one experiment was RUNNING when the process stopped
    When the user resumes the run
    Then the completed experiment is not executed again
    And the interrupted experiment is reconciled according to recovery policy
    And the original experiment-count budget is preserved
    And new research-log entries are appended rather than replacing old entries

AT-018: Detect changed inputs on resume
Scenario: Refuse unsafe resume after dataset modification
  Given a research run has been interrupted
  And train.csv has changed since the run started
  When the user attempts to resume
  Then resume is refused
  And the old and new dataset fingerprints are reported
  And no additional experiment is started

8. Phase 3: Clarify the specification

Run:

/speckit.clarify


Use this prompt:

Review the MVP specification for unresolved ambiguity.

Prioritize clarification of:

1. whether metric direction is explicit for every supported metric;
2. whether cross-validation defaults are deterministic;
3. how classification probabilities and regression predictions are represented;
4. what constitutes an equivalent or duplicate experiment;
5. how the minimum improvement threshold is applied;
6. whether failed and timed-out experiments consume experiment budget;
7. how interrupted RUNNING experiments are reconciled;
8. which feature transformations and parameters are allowlisted;
9. how data leakage checks distinguish warnings from blocking failures;
10. the numerical tolerance for reproducibility;
11. the required submission-schema invariants;
12. which artifacts are mandatory for experiment completion.

Do not expand the MVP scope.
Prefer explicit defaults where several reasonable choices exist.
Update the specification with the resolved decisions.

Recommended defaults

If the framework asks for decisions, I recommend:

Five-fold cross-validation.
StratifiedKFold for binary classification.
KFold for regression.
Seed 42.
Failed and timed-out attempts count against the total attempt budget.
Duplicate rejected proposals do not count as executed experiments.
Improvement threshold measured as absolute metric difference.
Dataset changes prohibit resume.
One experiment changes one configuration dimension or one predefined feature bundle.
Predictions stored as Parquet where practical, submission as CSV.
Run IDs and experiment IDs use UUIDs.
Timestamps use UTC.
No target-derived features in the first MVP unless fold-isolation tests are implemented first.
9. Phase 4: Create the technical plan

Run:

/speckit.plan


Spec Kit’s implementation-plan template explicitly captures technical context, constitution gates, project structure, research outputs, data model, contracts, and complexity exceptions.

Planning prompt
Create the technical implementation plan for the autonomous experiment-loop MVP.

Use:

- Python 3.12
- Typer for the CLI
- Pydantic v2 for contracts and configuration
- PyYAML for configuration loading
- pandas and pyarrow for tabular data and artifacts
- scikit-learn for validation splitters and metrics
- LightGBM and CatBoost as the only model families
- SQLAlchemy 2 with SQLite
- Alembic only if schema migrations are necessary for the MVP
- MLflow with a local file or SQLite-backed tracking store
- structlog or standard library structured logging
- pytest, pytest-cov and pytest-timeout
- Ruff and mypy
- JSON Lines for append-only research logging

Architecture constraints:

1. Use a modular monolith.
2. Use one synchronous orchestration process.
3. Separate pure domain logic from infrastructure adapters.
4. Do not introduce an event bus, message broker, vector database, web service,
   dependency-injection framework, workflow engine or multi-agent framework.
5. Implement the experiment planner behind a protocol so deterministic rule-based
   planning can be used in tests and an LLM-backed planner can be added later.
6. Restrict experiments to validated declarative ExperimentSpec objects.
7. Do not execute unconstrained generated Python code in the MVP.
8. Treat the dataset files and completed artifacts as immutable.
9. Make interruption recovery explicit through persisted run states.
10. Use dataset, configuration and experiment fingerprints for reproducibility
    and duplicate detection.

Proposed source structure:

src/kaggle_agent/
  cli/
  domain/
  application/
  infrastructure/
  models/
  features/
  validation/
  reporting/

tests/
  unit/
  contract/
  integration/
  acceptance/
  fixtures/

Produce:

- research.md resolving technical uncertainties;
- data-model.md;
- JSON schemas in contracts/;
- quickstart.md using a small synthetic fixture;
- plan.md;
- a requirement-to-test traceability approach.

Define the aggregate roots and state transitions for:

ResearchRun
Hypothesis
Experiment
Result
Insight

Define explicit statuses for:

ResearchRun:
CREATED, VALIDATING, BASELINING, RESEARCHING, GENERATING_OUTPUTS,
COMPLETED, STOPPED_BUDGET, STOPPED_FAILURE_BUDGET, FAILED, INTERRUPTED

Experiment:
PROPOSED, VALIDATED, RUNNING, COMPLETED, FAILED, TIMED_OUT,
REJECTED_DUPLICATE, REJECTED_POLICY

Define transaction boundaries and failure recovery.

Do not implement code.
Do not add features outside the specification.

10. Proposed implementation architecture

The plan should converge on a structure like this:

CLI
 │
 ▼
ResearchRunService
 │
 ├── CompetitionValidator
 ├── DatasetProfiler
 ├── BaselineService
 ├── ExperimentLoop
 │    ├── Planner
 │    ├── ProposalPolicy
 │    ├── DuplicateDetector
 │    ├── ExperimentRunner
 │    ├── Evaluator
 │    └── IncumbentSelector
 ├── SubmissionService
 └── ReportService
      │
      ├── SQLite repositories
      ├── MLflow tracker
      ├── JSONL research logger
      └── Artifact store


The essential design choice is that the planner returns a declarative experiment specification, not arbitrary executable code:

{
  "hypothesis": {
    "statement": "CatBoost native categorical handling will improve ROC AUC",
    "expected_direction": "increase",
    "rationale": "The dataset profile identified 12 categorical columns"
  },
  "change": {
    "type": "model_family",
    "from": "lightgbm",
    "to": "catboost"
  },
  "model_parameters": {
    "iterations": 500,
    "depth": 6,
    "learning_rate": 0.05
  }
}


That gives you autonomy at the research level while retaining safety and reproducibility at the execution level.

11. Phase 5: Generate tasks

Run:

/speckit.tasks


The Spec Kit task format supports dependencies, parallel tasks, user-story mapping, and exact file paths. It recommends grouping implementation by user story so each story can be delivered and tested independently.

Task-generation prompt
Generate implementation tasks from the approved specification and plan.

Requirements:

- Organize tasks by user story.
- Include exact file paths.
- Create acceptance tests before implementation tasks for every user story.
- Mark tasks parallelizable only when they touch independent files and have no
  unresolved dependency.
- Include requirement IDs and acceptance-test IDs in every relevant task.
- Do not create implementation tasks for out-of-scope features.
- Add explicit checkpoints after the baseline, experiment-loop, and output stories.
- Include CI, linting, type checking, unit tests, contract tests, integration tests,
  acceptance tests and coverage enforcement.
- Implement a deterministic RuleBasedPlanner for MVP acceptance testing.
- Keep any LLM-backed planner optional and outside the critical acceptance path.
- Require a full end-to-end test using a version-controlled synthetic fixture.

12. Suggested task breakdown
Phase A: Setup
T001 Create Python package structure and pyproject.toml
T002 Configure Ruff, mypy, pytest, coverage and pytest-timeout
T003 Create GitHub Actions quality workflow
T004 Add version-controlled classification and regression fixtures
T005 Add CLI smoke-test infrastructure

Phase B: Foundational domain
T006 Define CompetitionConfig and validation contracts
T007 Define Competition, ResearchRun, Hypothesis, Experiment, Result and Insight
T008 Implement state-transition rules
T009 Implement canonical serialization and fingerprinting
T010 Implement SQLAlchemy persistence models and repositories
T011 Implement append-only JSONL research logger
T012 Implement MLflow tracking adapter
T013 Implement workspace and immutable artifact conventions

Phase C: US1 baseline
T014 Write AT-001 through AT-005
T015 Implement competition input validation
T016 Implement dataset fingerprinting
T017 Implement dataset profiling
T018 Implement leakage preflight checks
T019 Implement deterministic split generation
T020 Implement metric registry and direction
T021 Implement LightGBM adapter
T022 Implement CatBoost adapter
T023 Implement baseline execution
T024 Persist baseline metrics, predictions and metadata
T025 Add CLI baseline command
T026 Pass US1 acceptance checkpoint

Phase D: US2 experiment loop
T027 Write AT-006 through AT-013
T028 Define ExperimentSpec contract
T029 Implement allowlisted proposal policy
T030 Implement RuleBasedPlanner
T031 Implement experiment fingerprint and duplicate detector
T032 Implement bounded experiment runner
T033 Implement timeout and failure handling
T034 Implement result evaluator
T035 Implement incumbent-selection policy
T036 Implement structured conclusion generation
T037 Implement sequential research loop
T038 Add CLI research command
T039 Pass US2 acceptance checkpoint

Phase E: US3 outputs
T040 Write AT-014 through AT-016
T041 Implement out-of-fold prediction artifact
T042 Implement final fit and test prediction generation
T043 Implement submission validator
T044 Implement submission writer
T045 Implement run-summary generator
T046 Implement Markdown research report
T047 Pass US3 acceptance checkpoint

Phase F: US4 recovery
T048 Write AT-017 and AT-018
T049 Implement interrupted-run detection
T050 Implement RUNNING experiment reconciliation
T051 Implement immutable input verification on resume
T052 Implement budget restoration
T053 Add CLI resume command
T054 Pass US4 acceptance checkpoint

Phase G: Final hardening
T055 Add end-to-end classification run
T056 Add end-to-end regression run
T057 Add malformed-input test suite
T058 Add research-log append-only integrity test
T059 Add artifact traceability test
T060 Add resource-budget enforcement test
T061 Run specification-to-task traceability analysis
T062 Complete quickstart validation
T063 Enforce quality gates in CI

13. Phase 6: Cross-artifact analysis

Before implementation, run:

/speckit.analyze


Use:

Analyze constitution.md, spec.md, plan.md, data-model.md, contracts and tasks.md.

Report:

- requirements without acceptance tests;
- acceptance tests without implementation tasks;
- tasks without requirement or user-story references;
- contradictions between the constitution and implementation plan;
- undefined domain terms;
- inconsistent state transitions;
- unbounded execution paths;
- any component that introduces multi-agent behavior;
- any use of leaderboard feedback for model selection;
- any pathway that allows arbitrary generated code execution;
- any artifact that cannot be traced to an experiment and hypothesis;
- any out-of-scope functionality.

Treat validation integrity, bounded autonomy, reproducibility, append-only memory
and submission validity as critical severity.

Do not modify implementation files.


Do not begin implementation while there are critical findings.

14. Phase 7: Implement

After the specification, plan, contracts, tasks, and analysis pass:

/speckit.implement


Use:

Implement tasks.md in dependency order.

Rules:

1. Write and execute each acceptance test before implementing its corresponding
   behavior.
2. Do not weaken an acceptance test to make implementation pass.
3. Stop and report if implementation requires changing the constitution or
   expanding scope.
4. Commit after each independently passing user-story checkpoint.
5. Maintain requirement, task and test identifiers in test metadata.
6. Run unit, contract, integration and acceptance tests after each checkpoint.
7. Do not implement Kaggle API submission, external research, arbitrary code
   generation, multi-agent orchestration, ensembling or a web interface.

15. CI acceptance gates

The pull request should be blocked unless all these gates pass:

ruff check .
ruff format --check .
mypy src
pytest tests/unit
pytest tests/contract
pytest tests/integration
pytest tests/acceptance
pytest --cov=src/kaggle_agent --cov-report=term-missing


Recommended quality thresholds:

100% of P1 acceptance tests pass.
100% of safety and validation-integrity tests pass.
At least 85% statement coverage.
100% branch coverage for:
budget enforcement;
experiment state transitions;
incumbent selection;
submission validation;
resume safety.
No type-checking errors.
No lint errors.
End-to-end classification run completes within 10 minutes on a normal development CPU using the test fixture.
End-to-end regression run completes within 10 minutes.
Reproducibility tests pass on two clean executions.

Coverage alone should not determine readiness. Traceability and end-to-end behavior are more important for this system.

16. MVP Definition of Done

The MVP is complete only when all of the following are true:

Functional
A user can configure and validate a local binary classification or regression competition.
A deterministic baseline is generated.
At least two supported model families can be evaluated.
A bounded loop can execute at least three unique experiments.
Each experiment has a hypothesis, controlled change, result and conclusion.
The best experiment is selected using consistent local cross-validation.
A valid submission file is generated.
The system generates a research report and machine-readable summary.
An interrupted run can be resumed safely.
Scientific integrity
No validation observation participates in fitting fold-specific transformations.
All experiments use identical folds unless a new research run is explicitly created.
Duplicate experiments are not executed.
An insignificant score change does not replace the incumbent.
Failed experiments remain available as research knowledge.
Reproducibility
Dataset, code, environment, configuration and experiment fingerprints are stored.
Repeated execution stays within the configured metric tolerance.
Predictions, fold assignments and parameters are retained.
Every final artifact traces back to its hypothesis and experiment.
Safety
Experiment count, runtime and failure budgets are enforced.
Protected files cannot be modified by experiment proposals.
No network access is required.
No credentials are loaded.
Invalid submissions are never marked ready.
Changed datasets prevent unsafe resume.
Delivery
All P1 acceptance tests pass in CI.
The quickstart can be followed from a clean checkout.
The synthetic example produces a baseline, experiments, a report and a submission.
Spec Kit analysis reports no critical inconsistencies.
Out-of-scope capabilities have not slipped into the implementation.
Final recommendation

The most important implementation decision is to make the first planner rule-based and deterministic, even if you eventually intend to use an LLM. Build the complete scientific loop around a planner interface first:

Research context
       ↓
Planner protocol
       ↓
Declarative ExperimentSpec
       ↓
Policy validation
       ↓
Controlled execution


Once the acceptance suite proves that the loop is bounded, reproducible, traceable, and leakage-safe, you can replace or complement RuleBasedPlanner with an LLM planner. That lets you test whether the agent improves experiment selection without confusing planner intelligence with execution reliability.