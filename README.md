# Strength Training Optimizer

Strength Training Optimizer is a Python project that builds personalized strength training plans using mathematical optimization.

The objective of the project is to adapt a training plan to the needs of a user without requiring a personal training coach. Instead of manually choosing exercises, muscle-group volume, training days, and session limits, the project formulates those decisions as an optimization problem and lets a solver search for a balanced plan.

At a high level, the system answers this question:

> Given a database of exercises, target muscle-group volume, available training days, and session duration limits, what combination of exercises and sets best matches the user's needs?

## Motivation

Many people want structured strength training but do not have access to a coach. A good training plan should not simply list random exercises. It should consider:

- which muscle groups each exercise trains
- whether a muscle is trained directly or secondarily
- how much weekly or monthly volume each muscle group should receive
- how many days the user can train
- how long each workout session can last
- how to avoid overtraining one muscle group while neglecting another

This project turns those practical coaching decisions into a formal optimization model. The goal is not to replace expert medical or sports advice, but to provide a systematic way to generate a coherent baseline plan from data.

## What The Optimizer Does

The current model creates a training plan across a 28-day planning horizon. It chooses how many sets of each exercise should be performed on each day.

The optimizer tries to match target training volume for each muscle group. If the generated plan trains a muscle too much or too little, the model creates a deviation. The objective is to minimize the total deviation across all muscle groups.

In simpler terms:

- A perfect plan reaches the desired number of sets for each muscle group.
- A less perfect plan misses some targets.
- The solver searches for the plan with the smallest total mismatch.

## Optimization Objective

The mathematical objective is:

```text
minimize total positive and negative deviation from target muscle volume
```

Each muscle group has a target number of series/sets. For example, chest and back may require more total volume than neck or forearms. The model compares the selected exercises against those targets.

Main muscles and secondary muscles are weighted differently:

- main muscle contribution: 2
- secondary muscle contribution: 1
- no contribution: 0

This allows compound exercises to be represented more realistically. For example, a chest exercise may also involve shoulders, but not with the same importance as the main target muscle.

## Constraints

The optimizer respects practical limits:

- maximum number of training days per month
- maximum workout duration per session
- maximum sets of the same exercise per day
- target volume for each muscle group
- exercise duration estimates
- exercise-to-muscle relationships

These constraints make the generated plan closer to something a person could actually follow.

## Repository Structure

```text
.
|-- data/
|   |-- raw/
|   |   `-- .gitkeep
|   `-- processed/
|       |-- README.md
|       `-- exercises_clean.csv
|-- notebooks/
|   `-- problem.ipynb
|-- src/
|   `-- strength_training_optimizer/
|       |-- __init__.py
|       |-- cli.py
|       |-- config.py
|       |-- data.py
|       `-- model.py
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

## Main Files

`src/strength_training_optimizer/data.py`

Loads, validates, and cleans the exercise dataset. It also maps detailed muscle names into the model's main muscle categories.

`src/strength_training_optimizer/config.py`

Contains tunable values such as target series per muscle group, maximum training days, maximum session duration, and estimated exercise duration.

`src/strength_training_optimizer/model.py`

Builds the Pyomo optimization model, solves it with an external solver, and extracts the selected workout plan.

`src/strength_training_optimizer/cli.py`

Provides the command-line interface for cleaning data and running the optimizer.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the project:

```bash
python -m pip install -e .
```

Pyomo requires an external optimization solver. This project defaults to Gurobi because the original notebook used it.

## Usage

Run the optimizer with the processed dataset:

```bash
strength-optimize --solver gurobi
```

Save the generated workout plan:

```bash
strength-optimize --solver gurobi --output results/workout_plan.csv
```

Rebuild the processed dataset from a raw dataset:

```bash
strength-optimize clean --raw data/raw/gym_exercise_dataset.csv --output data/processed/exercises_clean.csv
```

## Data

The processed dataset is stored at:

```text
data/processed/exercises_clean.csv
```

It includes:

- exercise name
- difficulty
- utility/basic flag
- main muscle group
- secondary muscle group
- estimated duration

The model also creates stable exercise identifiers internally when exercise names are duplicated.

## Current Limitations

The current model is a first serious optimization baseline. It does not yet include:

- user-specific injuries or forbidden exercises
- preferred equipment
- progressive overload across weeks
- rest-day spacing between muscle groups
- exercise variety preferences
- beginner/intermediate/advanced templates

Those features can be added naturally because the project is now structured as a Python package instead of a single notebook.

## Project Status

This repository is intended as a clean foundation for a personalized training-plan optimizer. The next step would be to add user inputs, such as training level, available days, session length, available equipment, and target muscle emphasis.
