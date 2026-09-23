"""Pure geometry and mathematical helpers."""

from __future__ import annotations

import math


def require_positive_finite(value: float, name: str) -> float:
    """Return a value after asserting it is positive and finite."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric.")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite.")
    return float(value)
