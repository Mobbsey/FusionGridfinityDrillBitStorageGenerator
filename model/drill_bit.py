"""Fusion-independent drill-bit domain model."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class DrillBitType(str, Enum):
    """Drill types offered by the command."""

    HSS = "HSS"
    BRAD_POINT_WOOD = "Brad Point / Wood"
    MASONRY = "Masonry"
    TILE = "Ceramic Tile"

    @classmethod
    def from_display_name(cls, name: str) -> DrillBitType:
        """Resolve a UI display string to a domain enum member."""
        try:
            return cls(name)
        except ValueError as error:
            raise ValueError(f"Unsupported drill type: {name!r}") from error


@dataclass
class DrillBit:
    """A drill bit, with all dimensions expressed in millimetres."""

    diameter_mm: float
    bit_type: DrillBitType = DrillBitType.HSS
    explicit_length_mm: float | None = None

    BITS_PER_SLOT: ClassVar[int] = 2
    MINIMUM_SLOT_WIDTH_MM: ClassVar[float] = 12.0
    SLOT_SIDE_ALLOWANCE_MM: ClassVar[float] = 2.0
    LENGTH_ALLOWANCE_MM: ClassVar[float] = 10.0

    def __post_init__(self) -> None:
        self.diameter_mm = _positive_finite(self.diameter_mm, "Drill-bit diameter")
        if not isinstance(self.bit_type, DrillBitType):
            raise TypeError("bit_type must be a DrillBitType.")
        if self.explicit_length_mm is not None:
            self.explicit_length_mm = _positive_finite(
                self.explicit_length_mm, "Explicit drill-bit length"
            )

    @property
    def slot_width_mm(self) -> float:
        """Width allocated to this drill size in the bin."""
        calculated_width = (
            self.diameter_mm * self.BITS_PER_SLOT + self.SLOT_SIDE_ALLOWANCE_MM
        )
        return max(self.MINIMUM_SLOT_WIDTH_MM, calculated_width)

    @property
    def required_length_mm(self) -> float:
        """Minimum bin length needed for this drill size."""
        if self.explicit_length_mm is not None:
            return self.explicit_length_mm + self.LENGTH_ALLOWANCE_MM

        if self.bit_type == DrillBitType.HSS:
            estimated_length = (
                -0.34 * self.diameter_mm**2 + 14.5 * self.diameter_mm + 36.0
            )
        elif self.bit_type == DrillBitType.BRAD_POINT_WOOD:
            estimated_length = (
                (-0.4 * self.diameter_mm**2) + (15.5 * self.diameter_mm) + 34
            )
        elif self.bit_type == DrillBitType.MASONRY:
            estimated_length = (
                (-0.32 * self.diameter_mm**2) + (13.7 * self.diameter_mm) + 25
            )
        elif self.bit_type == DrillBitType.TILE:
            estimated_length = min(100, 85 + (1.5 * self.diameter_mm))
        else:
            raise RuntimeError(
                f"No automatic length estimate exists for {self.bit_type.value}."
            )
        # Keep extrapolated results physically meaningful outside the measured
        # ranges of the empirical sizing curves.
        return max(self.diameter_mm, estimated_length) + self.LENGTH_ALLOWANCE_MM

    @property
    def required_depth_mm(self) -> float:
        """Depth needed for the slot profile."""
        return max(1.2 + max(2.0, self.diameter_mm), self.diameter_mm * 2.0)


def _positive_finite(value: float, description: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{description} must be numeric.")
    numeric_value = float(value)
    if not math.isfinite(numeric_value) or numeric_value <= 0:
        raise ValueError(f"{description} must be positive and finite.")
    return numeric_value
