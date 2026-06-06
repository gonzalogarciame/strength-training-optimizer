"""Configuration values for the gym optimization model."""

from dataclasses import dataclass, field


MUSCLE_DURATION = {
    "Neck": 1.5,
    "Calves": 1.5,
    "Hips": 2.0,
    "Back": 5.0,
    "Thighs": 5.0,
    "Chest": 5.0,
    "Shoulder": 3.5,
    "Upper Arms": 3.0,
    "Forearm": 2.0,
    "Biceps": 3.0,
    "Triceps": 3.0,
}

SERIES_PER_MUSCLE = {
    "Neck": 6,
    "Calves": 12,
    "Hips": 12,
    "Back": 20,
    "Thighs": 12,
    "Chest": 20,
    "Shoulder": 15,
    "Forearm": 8,
    "Biceps": 16,
    "Triceps": 16,
}


@dataclass(frozen=True)
class OptimizationConfig:
    """User-tunable model settings."""

    days: tuple[int, ...] = tuple(range(1, 29))
    max_training_days_per_month: int = 16
    max_session_minutes: float = 90.0
    max_sets_per_exercise_per_day: int = 6
    series_per_muscle: dict[str, int] = field(default_factory=lambda: SERIES_PER_MUSCLE.copy())
