# Strength Training Optimizer

A Pyomo-based optimization project for designing monthly strength training plans from an exercise dataset.

The project started as a Jupyter notebook and has been refactored into a reusable Python package with a command-line interface, tests, and a clean data layout.

## Repository Structure

```text
.
├── data/
│   ├── raw/                         # Original datasets, not required for normal runs
│   └── processed/
│       └── exercises_clean.csv      # Validated exercise dataset used by the model
├── notebooks/
│   └── problem.ipynb                # Original exploratory notebook
├── src/
│   └── strength_training_optimizer/
│       ├── cli.py                   # Command-line entry point
│       ├── config.py                # Optimization constants and tunable settings
│       ├── data.py                  # Dataset loading, validation, and cleaning
│       └── model.py                 # Pyomo model, solve routine, and solution extraction
├── tests/
│   ├── test_data.py
│   └── test_model.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
```

Pyomo requires an external solver. This project defaults to Gurobi because the original notebook used it.

## Usage

Run the optimizer:

```bash
strength-optimize --solver gurobi
```

Save a generated workout plan:

```bash
strength-optimize --solver gurobi --output results/workout_plan.csv
```

Rebuild the processed dataset from a raw file:

```bash
strength-optimize clean --raw data/raw/gym_exercise_dataset.csv --output data/processed/exercises_clean.csv
```

## Tests

```bash
pytest
```

## Current Model

The model chooses daily exercise sets across a 28-day planning horizon. It balances target series per muscle group while respecting:

- maximum training days per month
- maximum session duration
- maximum sets per exercise per day
- main and secondary muscle contribution weights

The current objective minimizes total positive and negative deviation from target muscle volume.
