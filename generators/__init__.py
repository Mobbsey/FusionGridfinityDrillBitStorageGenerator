"""Geometry generators, imported lazily so pure helpers remain testable."""

from __future__ import annotations

__all__ = ["DrillSlotGenerator", "GridfinityGenerator"]


def __getattr__(name: str):
    if name == "DrillSlotGenerator":
        from .drill_slot_generator import DrillSlotGenerator

        return DrillSlotGenerator
    if name == "GridfinityGenerator":
        from .gridfinity_generator import GridfinityGenerator

        return GridfinityGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
