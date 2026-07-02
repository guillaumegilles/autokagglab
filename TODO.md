If the MVP succeeds, I would **not** jump to multi-agent systems, forum mining, or paper reading.

The next feature should be:

# Meta-Learning / Research Strategy Engine

Not a better model generator.

A better **experiment chooser**.

Why?

Because after a few hundred experiments, the bottleneck changes.

Initially:

```text
Problem:
No experiments exist.
```

Later:

```text
Problem:
Too many possible experiments.
```

The real challenge becomes:

> Which experiment should I run next?

A human Kaggle Grandmaster spends much of their value on exactly this decision.

***

## Example

Suppose your agent has already run:

```text
50 feature engineering experiments
20 hyperparameter experiments
10 model family experiments
```

It should be able to infer:

```text
Feature engineering improvements:
+0.025

Hyperparameter improvements:
+0.003

Model switching:
+0.002
```

Then automatically conclude:

```text
Next effort should focus on features.
```

This is much more valuable than generating another CatBoost configuration.

***

# The Feature I'd Build

A new component:

```text
Strategy Engine
```

Input:

```text
Research Log
Experiment History
Leaderboard Scores
Insights
```

Output:

```yaml
recommended_direction:
  feature_engineering

confidence:
  0.82

reason:
  Last 25 experiments indicate feature changes
  have produced 85% of total score gains.
```

Now the agent is learning how to research.

***

# Why This Before Forum Mining

Many people would add:

```text
Research Forum Agent
```

next.

I would not.

Because:

```text
External knowledge
=
more ideas
```

But:

```text
Strategy Engine
=
better selection of ideas
```

The second tends to produce more value.

A mediocre set of ideas selected intelligently often outperforms a huge set of ideas selected randomly.

***

# Second Feature After That

Once the Strategy Engine works:

## Automatic Ensembling

Not deep learning.

Not RAG.

Not 20 agents.

Ensembling.

A surprisingly large amount of Kaggle ranking comes from:

```text
Blending
Rank averaging
Stacking
Weighted ensembles
```

The agent should automatically discover:

```text
Model A: 0.812

Model B: 0.811

Model C: 0.809

Ensemble: 0.818
```

This is often one of the highest ROI capabilities you can add.

***

# Third Feature

After ensembling:

## Cross-Competition Memory

This is where things become really interesting.

Imagine:

```text
Competition 1:
Credit Risk

Competition 2:
Fraud Detection

Competition 3:
Customer Churn
```

The system learns:

```text
Target encoding often helps.

CatBoost performs well with
high-cardinality categoricals.

Adversarial validation frequently
detects leaderboard shakeup risk.
```

Now every new Kaggle competition starts with accumulated experience.

At that point the agent begins looking less like a competition-specific tool and more like an actual machine-learning researcher.

***

# My Roadmap

If I were building this myself:

```text
MVP
│
├── Competition analysis
├── Hypothesis generation
├── Experiment execution
├── Research log
├── MLflow
└── Memory
```

Then:

```text
V2
│
└── Strategy Engine
```

Then:

```text
V3
│
└── Automatic Ensembling
```

Then:

```text
V4
│
└── Cross-Competition Learning
```

Then:

```text
V5
│
├── Forum mining
├── Notebook mining
└── External research
```

Only after all of that would I seriously consider:

```text
Multi-agent research teams
```

because in practice, a single well-designed research agent with strong memory and a strong strategy engine will usually outperform a swarm of agents that don't know how to prioritize experiments.
