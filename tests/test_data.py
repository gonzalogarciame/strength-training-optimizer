from pathlib import Path

from strength_training_optimizer.data import build_muscle_exercise_weights, load_clean_dataset


DATA_PATH = Path("data/processed/exercises_clean.csv")


def test_load_clean_dataset_has_expected_columns():
    df = load_clean_dataset(DATA_PATH)

    assert len(df) > 0
    assert "Exercise Name" in df.columns
    assert "Duration" in df.columns


def test_muscle_exercise_weights_include_main_muscle_weight():
    df = load_clean_dataset(DATA_PATH).head(5)
    weights = build_muscle_exercise_weights(df)
    first = df.iloc[0]

    assert weights[(first["Exercise Name"], first["Main_muscle"])] == 2
