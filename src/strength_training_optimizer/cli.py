"""Command-line interface for the gym optimization project."""

from __future__ import annotations

import argparse
from pathlib import Path

import pyomo.environ as pe

from strength_training_optimizer.data import clean_raw_dataset, load_clean_dataset
from strength_training_optimizer.model import build_model, extract_solution, save_solution, solve_model


DEFAULT_DATA_PATH = Path("data/processed/exercises_clean.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and solve a strength training optimization model.")
    subparsers = parser.add_subparsers(dest="command")

    clean_parser = subparsers.add_parser("clean", help="Clean the original raw exercise dataset.")
    clean_parser.add_argument("--raw", required=True, help="Path to the raw gym_exercise_dataset.csv file.")
    clean_parser.add_argument(
        "--output",
        default=str(DEFAULT_DATA_PATH),
        help="Path where the cleaned dataset will be written.",
    )

    parser.add_argument("--data", default=str(DEFAULT_DATA_PATH), help="Path to the cleaned exercise dataset.")
    parser.add_argument("--solver", default="gurobi", help="Pyomo solver name. Defaults to gurobi.")
    parser.add_argument("--output", help="Optional CSV path for the workout plan.")
    parser.add_argument("--tee", action="store_true", help="Show solver output.")
    return parser


def run_clean(args: argparse.Namespace) -> int:
    df = clean_raw_dataset(args.raw, args.output)
    print(f"Wrote {len(df)} cleaned exercises to {args.output}")
    return 0


def run_optimization(args: argparse.Namespace) -> int:
    df = load_clean_dataset(args.data)
    model = build_model(df)
    results = solve_model(model, solver_name=args.solver, tee=args.tee)
    solution = extract_solution(model)

    status = results.solver.status
    termination = results.solver.termination_condition
    objective = pe.value(model.cost)
    print(f"Solver status: {status}")
    print(f"Termination: {termination}")
    print(f"Objective deviation: {objective:g}")
    print(f"Selected exercise rows: {len(solution)}")

    if args.output:
        save_solution(solution, args.output)
        print(f"Wrote solution to {args.output}")
    elif not solution.empty:
        print(solution.to_string(index=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "clean":
        return run_clean(args)
    return run_optimization(args)


if __name__ == "__main__":
    raise SystemExit(main())
