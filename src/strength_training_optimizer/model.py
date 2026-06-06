"""Pyomo model construction and solution extraction."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyomo.environ as pe
import pyomo.opt as po

from strength_training_optimizer.config import OptimizationConfig
from strength_training_optimizer.data import build_muscle_exercise_weights


def build_model(df: pd.DataFrame, config: OptimizationConfig | None = None) -> pe.ConcreteModel:
    """Build the monthly gym optimization model."""

    config = config or OptimizationConfig()
    exercise_column = "Exercise ID" if "Exercise ID" in df.columns else "Exercise Name"
    exercises = df[exercise_column].tolist()
    muscles = df["Main_muscle"].dropna().unique().tolist()

    missing_targets = set(muscles).difference(config.series_per_muscle)
    if missing_targets:
        missing = ", ".join(sorted(missing_targets))
        raise ValueError(f"Missing target series for muscles: {missing}")

    model = pe.ConcreteModel("Strength Training Optimization Problem")
    model.exercise = pe.Set(initialize=exercises)
    model.muscles = pe.Set(initialize=muscles)
    model.days = pe.Set(initialize=config.days)

    model.duration = pe.Param(
        model.exercise,
        initialize=dict(zip(df[exercise_column], df["Duration"])),
        within=pe.NonNegativeReals,
    )
    model.difficulty = pe.Param(
        model.exercise,
        initialize=dict(zip(df[exercise_column], df["Difficulty (1-5)"])),
        within=pe.NonNegativeReals,
    )
    model.exercise_basic = pe.Param(
        model.exercise,
        initialize=dict(zip(df[exercise_column], df["Utility"])),
        within=pe.Binary,
    )
    model.exercise_name = pe.Param(
        model.exercise,
        initialize=dict(zip(df[exercise_column], df["Exercise Name"])),
        within=pe.Any,
    )
    model.muscle_group_exercise = pe.Param(
        model.exercise,
        model.muscles,
        initialize=build_muscle_exercise_weights(df),
        within=pe.NonNegativeIntegers,
    )
    model.series_per_muscle = pe.Param(
        model.muscles,
        initialize={muscle: config.series_per_muscle[muscle] for muscle in muscles},
        within=pe.NonNegativeIntegers,
    )
    model.number_days_per_month = pe.Param(initialize=config.max_training_days_per_month)
    model.duration_session_max = pe.Param(initialize=config.max_session_minutes)

    model.training_day = pe.Var(model.days, domain=pe.Binary)
    model.sets_day = pe.Var(model.days, model.exercise, domain=pe.NonNegativeIntegers)
    model.positive_deviation = pe.Var(model.muscles, domain=pe.NonNegativeIntegers)
    model.negative_deviation = pe.Var(model.muscles, domain=pe.NonNegativeIntegers)

    def objective_rule(m: pe.ConcreteModel) -> pe.Expression:
        return sum(m.positive_deviation[muscle] + m.negative_deviation[muscle] for muscle in m.muscles)

    model.cost = pe.Objective(rule=objective_rule, sense=pe.minimize)

    def max_training_days_rule(m: pe.ConcreteModel) -> pe.Expression:
        return sum(m.training_day[day] for day in m.days) <= m.number_days_per_month

    model.max_training_days = pe.Constraint(rule=max_training_days_rule)

    def session_duration_rule(m: pe.ConcreteModel, day: int) -> pe.Expression:
        return (
            sum(m.sets_day[day, exercise] * m.duration[exercise] for exercise in m.exercise)
            <= m.duration_session_max * m.training_day[day]
        )

    model.session_duration = pe.Constraint(model.days, rule=session_duration_rule)

    def sets_activation_rule(m: pe.ConcreteModel, day: int, exercise: str) -> pe.Expression:
        return m.sets_day[day, exercise] <= config.max_sets_per_exercise_per_day * m.training_day[day]

    model.sets_activation = pe.Constraint(model.days, model.exercise, rule=sets_activation_rule)

    def muscle_volume_rule(m: pe.ConcreteModel, muscle: str) -> pe.Expression:
        trained_series = sum(
            m.sets_day[day, exercise] * m.muscle_group_exercise[exercise, muscle]
            for day in m.days
            for exercise in m.exercise
        )
        return trained_series + m.negative_deviation[muscle] - m.positive_deviation[muscle] == m.series_per_muscle[muscle]

    model.muscle_volume = pe.Constraint(model.muscles, rule=muscle_volume_rule)
    return model


def solve_model(
    model: pe.ConcreteModel,
    solver_name: str = "gurobi",
    tee: bool = False,
) -> po.results.results_.SolverResults:
    """Solve a Pyomo model with the requested solver."""

    solver = po.SolverFactory(solver_name)
    if not solver.available(exception_flag=False):
        raise RuntimeError(
            f"Solver '{solver_name}' is not available. Install it or pass another solver with --solver."
        )
    return solver.solve(model, tee=tee)


def extract_solution(model: pe.ConcreteModel) -> pd.DataFrame:
    """Extract non-zero exercise sets into a tidy dataframe."""

    rows = []
    for day in model.days:
        if pe.value(model.training_day[day]) < 0.5:
            continue
        for exercise in model.exercise:
            sets = round(pe.value(model.sets_day[day, exercise]))
            if sets > 0:
                rows.append(
                    {
                        "day": int(day),
                        "exercise_id": str(exercise),
                        "exercise": str(pe.value(model.exercise_name[exercise])),
                        "sets": sets,
                        "duration_minutes": float(pe.value(model.duration[exercise]) * sets),
                    }
                )
    return pd.DataFrame(rows)


def save_solution(solution: pd.DataFrame, output_path: str | Path) -> None:
    """Save a solution dataframe to CSV."""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    solution.to_csv(output_path, index=False)
