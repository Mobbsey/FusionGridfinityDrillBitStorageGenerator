"""Small, explicit helpers at the Autodesk Fusion API boundary."""

from __future__ import annotations

import adsk.core
import adsk.fusion

FUSION_INTERNAL_LENGTH_TO_MM = 10.0


def internal_length_to_mm(value_cm: float) -> float:
    """Convert Fusion Design's internal centimetre length to millimetres."""
    return value_cm * FUSION_INTERNAL_LENGTH_TO_MM


def mm_to_internal_length(value_mm: float) -> float:
    """Convert domain millimetres to Fusion Design's internal centimetres."""
    return value_mm / FUSION_INTERNAL_LENGTH_TO_MM


def get_active_design() -> adsk.fusion.Design:
    """Return the active Fusion Design or raise a clear command error."""
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct) if app else None
    if design is None:
        raise RuntimeError(
            "Open or create a Fusion Design before running this command."
        )
    return design


def require_healthy_entity(entity, description: str) -> None:
    """Raise when a newly created Fusion sketch or feature is in error."""
    if entity is None:
        raise RuntimeError(f"{description} was not created.")
    health_state = getattr(entity, "healthState", None)
    if health_state == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
        details = getattr(entity, "errorOrWarningMessage", "")
        suffix = f": {details}" if details else "."
        raise RuntimeError(f"{description} is in an error state{suffix}")
