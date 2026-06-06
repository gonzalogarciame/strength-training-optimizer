"""Data loading and cleaning utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from strength_training_optimizer.config import MUSCLE_DURATION


REQUIRED_CLEAN_COLUMNS = [
    "Exercise Name",
    "Difficulty (1-5)",
    "Utility",
    "Main_muscle",
    "Secondary Muscles",
    "Duration",
]

RAW_COLUMNS = [
    "Exercise Name",
    "Difficulty (1-5)",
    "Utility",
    "Main_muscle",
    "Secondary Muscles",
    "Target_Muscles",
]

BICEPS_KEYS = ("biceps brachii", "brachialis", "brachioradialis")
TRICEPS_KEYS = ("triceps brachii",)

SECONDARY_MUSCLE_MAP = {
    "sternocleidomastoid": "Neck",
    "levator scapulae": "Neck",
    "splenius": "Neck",
    "deltoid": "Shoulder",
    "supraspinatus": "Shoulder",
    "infraspinatus": "Shoulder",
    "teres minor": "Shoulder",
    "subscapularis": "Shoulder",
    "biceps": "Biceps",
    "triceps": "Triceps",
    "brachialis": "Biceps",
    "brachioradialis": "Biceps",
    "trapezius": "Back",
    "rhomboids": "Back",
    "latissimus dorsi": "Back",
    "erector spinae": "Back",
    "pectoralis": "Chest",
    "gluteus maximus": "Hips",
    "iliopsoas": "Hips",
    "hip flexors": "Hips",
    "quadriceps": "Thighs",
    "hamstrings": "Thighs",
    "adductors": "Thighs",
    "gastrocnemius": "Calves",
    "soleus": "Calves",
    "tibialis anterior": "Calves",
}


def refine_upper_arms(main_muscle: str, target_muscle: str | float | None) -> str:
    """Classify upper-arm exercises as biceps or triceps when target text allows it."""

    if main_muscle != "Upper Arms":
        return main_muscle
    if not isinstance(target_muscle, str):
        return "Upper Arms"

    text = target_muscle.lower().strip(",")
    if any(key in text for key in BICEPS_KEYS):
        return "Biceps"
    if any(key in text for key in TRICEPS_KEYS):
        return "Triceps"
    return "Upper Arms"


def map_secondary_to_main(secondary_muscle: str | float | None) -> str | None:
    """Map detailed secondary muscle names to the model's main muscle categories."""

    if not isinstance(secondary_muscle, str):
        return None

    text = secondary_muscle.lower().strip()
    for keyword, main_category in SECONDARY_MUSCLE_MAP.items():
        if keyword in text:
            return main_category
    return None


def clean_raw_dataset(raw_path: str | Path, output_path: str | Path | None = None) -> pd.DataFrame:
    """Clean the original exercise dataset used by the notebook."""

    df = pd.read_csv(raw_path)
    missing_columns = set(RAW_COLUMNS).difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Raw dataset is missing required columns: {missing}")

    df = df[RAW_COLUMNS].copy()
    df["Utility"] = (df["Utility"] == "Basic").astype(int)
    df["Main_muscle"] = df.apply(
        lambda row: refine_upper_arms(row["Main_muscle"], row["Target_Muscles"]),
        axis=1,
    )
    df["Secondary Muscles"] = df["Secondary Muscles"].apply(map_secondary_to_main)
    df["Duration"] = df["Main_muscle"].map(MUSCLE_DURATION)
    df.loc[df["Main_muscle"] == df["Secondary Muscles"], "Secondary Muscles"] = None
    df = df.drop(columns=["Target_Muscles"]).drop_duplicates().reset_index(drop=True)

    if df["Duration"].isna().any():
        missing_muscles = sorted(df.loc[df["Duration"].isna(), "Main_muscle"].dropna().unique())
        raise ValueError(f"Missing duration mapping for muscles: {missing_muscles}")

    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
    return df


def load_clean_dataset(path: str | Path) -> pd.DataFrame:
    """Load and validate the cleaned exercise dataset."""

    df = pd.read_csv(path)
    missing_columns = set(REQUIRED_CLEAN_COLUMNS).difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Clean dataset is missing required columns: {missing}")

    df = df[REQUIRED_CLEAN_COLUMNS].copy()
    df["Secondary Muscles"] = df["Secondary Muscles"].where(df["Secondary Muscles"].notna(), None)
    df = df.drop_duplicates().reset_index(drop=True)
    df["Exercise ID"] = _make_exercise_ids(df["Exercise Name"])
    return df


def build_muscle_exercise_weights(df: pd.DataFrame) -> dict[tuple[str, str], int]:
    """Return exercise-muscle weights: 2 for main muscle, 1 for secondary, 0 otherwise."""

    exercise_column = "Exercise ID" if "Exercise ID" in df.columns else "Exercise Name"
    exercises = df[exercise_column].tolist()
    muscles = df["Main_muscle"].dropna().unique().tolist()
    weights: dict[tuple[str, str], int] = {}

    indexed = df.set_index(exercise_column)
    for exercise in exercises:
        row = indexed.loc[exercise]
        for muscle in muscles:
            if muscle == row["Main_muscle"]:
                weights[(exercise, muscle)] = 2
            elif muscle == row["Secondary Muscles"]:
                weights[(exercise, muscle)] = 1
            else:
                weights[(exercise, muscle)] = 0
    return weights


def _make_exercise_ids(names: pd.Series) -> list[str]:
    """Create stable unique IDs while keeping original exercise names for display."""

    counts: dict[str, int] = {}
    ids = []
    for name in names:
        counts[name] = counts.get(name, 0) + 1
        if counts[name] == 1:
            ids.append(str(name))
        else:
            ids.append(f"{name} [{counts[name]}]")
    return ids
