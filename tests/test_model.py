from pathlib import Path

import pyomo.environ as pe

from strength_training_optimizer.data import load_clean_dataset
from strength_training_optimizer.model import build_model


DATA_PATH = Path("data/processed/exercises_clean.csv")


def test_build_model_creates_expected_components():
    df = load_clean_dataset(DATA_PATH).head(20)
    model = build_model(df)

    assert isinstance(model, pe.ConcreteModel)
    assert len(model.exercise) == len(df)
    assert hasattr(model, "muscle_volume")
