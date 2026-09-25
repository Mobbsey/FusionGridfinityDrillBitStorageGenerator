"""Fusion-independent Gridfinity drill-bit bin model."""

from __future__ import annotations

import math

from .drill_bit import DrillBit, DrillBitType

class GridfinityDrillBitBin:
    """Calculated dimensions and contents for one Gridfinity bin."""

    GRID_UNIT_MM = 42.0
    HEIGHT_UNIT_MM = 7.0
    BASE_HEIGHT_MM = 3.8
    MINIMUM_GAP_MM = 4.0
    OUTER_OFFSET_MM = 4.3
    CLEARANCE_MM = 0.25
    DEPRESSION_EXTRA_DEPTH_MM = 4.0
    DEPRESSION_LENGTH_MM = 18.0
    CHAMFER_SIZE_MM = 1.2
    LABEL_AREA_HEIGHT_MM = 10.0
    LABEL_FONT_HEIGHT_MM = 7.0
    LABEL_DEPTH_MM = 1.2

    def __init__(self, bit_type: DrillBitType = DrillBitType.HSS) -> None:
        if not isinstance(bit_type, DrillBitType):
            raise TypeError("bit_type must be a DrillBitType.")
        self.bit_type = bit_type
        self.drill_bits: list[DrillBit] = []
        self._explicit_u_width: int | None = None
        self._explicit_u_length: int | None = None
        self._explicit_u_height: int | None = None
        self._split_for_multicolor = False

    @property
    def split_for_multicolor(self) -> bool:
        return self._split_for_multicolor

    @split_for_multicolor.setter
    def split_for_multicolor(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Split-for-multicolour must be a boolean value.")
        self._split_for_multicolor = value

    @property
    def explicit_u_width(self) -> int | None:
        return self._explicit_u_width

    @explicit_u_width.setter
    def explicit_u_width(self, value: int | None) -> None:
        self._explicit_u_width = _optional_positive_int(value, "Bin width")

    @property
    def explicit_u_length(self) -> int | None:
        return self._explicit_u_length

    @explicit_u_length.setter
    def explicit_u_length(self, value: int | None) -> None:
        self._explicit_u_length = _optional_positive_int(value, "Bin length")

    @property
    def explicit_u_height(self) -> int | None:
        return self._explicit_u_height

    @explicit_u_height.setter
    def explicit_u_height(self, value: int | None) -> None:
        self._explicit_u_height = _optional_positive_int(value, "Bin height")

    def add_bit(self, diameter_mm: float, length_mm: float | None = None, width:int = 2, depth:int = 2) -> DrillBit:
        """Add and sort a drill bit, rejecting invalid dimensions."""
        drill_bit = DrillBit(
            diameter_mm=diameter_mm,
            bit_type=self.bit_type,
            explicit_length_mm=length_mm,
            bin_width_count=width,
            bin_depth_count=depth
        )
        self.drill_bits.append(drill_bit)
        self.drill_bits.sort(key=lambda bit: bit.diameter_mm)
        return drill_bit

    def clear_bits(self) -> None:
        self.drill_bits.clear()

    def set_bit_type(self, bit_type: DrillBitType) -> None:
        if not isinstance(bit_type, DrillBitType):
            raise TypeError("bit_type must be a DrillBitType.")
        self.bit_type = bit_type
        for drill_bit in self.drill_bits:
            drill_bit.bit_type = bit_type

    def remove_bit(self, drill_bit: DrillBit) -> None:
        self.drill_bits.remove(drill_bit)

    @property
    def required_width_mm(self) -> float:
        return sum(bit.slot_width_mm for bit in self.drill_bits)

    @property
    def required_depth_mm(self) -> float:
        return max((bit.required_depth_mm for bit in self.drill_bits), default=0.0)

    @property
    def depression_depth_mm(self) -> float:
        return self.required_depth_mm + self.DEPRESSION_EXTRA_DEPTH_MM

    @property
    def required_length_mm(self) -> float:
        longest_bit = max(
            (bit.required_length_mm for bit in self.drill_bits), default=0.0
        )
        if longest_bit == 0:
            return 0.0
        return longest_bit + self.LABEL_AREA_HEIGHT_MM + 2.0

    @property
    def u_width(self) -> int:
        return self.explicit_u_width or self.calculated_u_width

    @property
    def calculated_u_width(self) -> int:
        if not self.drill_bits:
            return 1
        required_width = self.minimum_required_width_mm
        return max(1, math.ceil(required_width / self.GRID_UNIT_MM))

    @property
    def u_length(self) -> int:
        return self.explicit_u_length or self.calculated_u_length

    @property
    def calculated_u_length(self) -> int:
        if not self.drill_bits:
            return 1
        return max(
            1,
            math.ceil(
                (self.required_length_mm + self.OUTER_OFFSET_MM) / self.GRID_UNIT_MM
            ),
        )

    @property
    def u_height(self) -> int:
        return self.explicit_u_height or self.calculated_u_height

    @property
    def calculated_u_height(self) -> int:
        if not self.drill_bits:
            return 1
        return max(
            1,
            math.ceil((self.depression_depth_mm + 10.0) / self.HEIGHT_UNIT_MM),
        )

    @property
    def width_mm(self) -> float:
        return self.u_width * self.GRID_UNIT_MM

    @property
    def height_mm(self) -> float:
        return self.u_height * self.HEIGHT_UNIT_MM + self.BASE_HEIGHT_MM

    @property
    def slot_gap_mm(self) -> float:
        if not self.drill_bits:
            return 0.0
        available_width = self.width_mm - 2 * self.CLEARANCE_MM
        spare_width = available_width - self.required_width_mm
        return spare_width / (len(self.drill_bits) + 1)

    @property
    def minimum_required_width_mm(self) -> float:
        if not self.drill_bits:
            return 0.0
        return (
            self.required_width_mm
            + (len(self.drill_bits) + 1) * self.MINIMUM_GAP_MM
            + 2 * self.CLEARANCE_MM
        )

    @property
    def width_utilisation_exact(self) -> float:
        if not self.drill_bits:
            return 0.0
        available = self.width_mm - 2 * self.CLEARANCE_MM
        required = self.minimum_required_width_mm - 2 * self.CLEARANCE_MM
        return 100 * required / available

    @property
    def length_utilisation_exact(self) -> float:
        if not self.drill_bits:
            return 0.0
        return 100 * self.required_length_mm / (self.u_length * self.GRID_UNIT_MM)

    @property
    def height_utilisation_exact(self) -> float:
        if not self.drill_bits:
            return 0.0
        required = self.depression_depth_mm + 10.0
        return 100 * required / (self.u_height * self.HEIGHT_UNIT_MM)

    @property
    def width_utilisation(self) -> int:
        return round(self.width_utilisation_exact)

    @property
    def length_utilisation(self) -> int:
        return round(self.length_utilisation_exact)

    @property
    def height_utilisation(self) -> int:
        return round(self.height_utilisation_exact)

    @property
    def validation_errors(self) -> tuple[str, ...]:
        """Return user-correctable specification problems."""
        errors = []
        if not self.drill_bits:
            errors.append("Add at least one drill bit with a positive diameter.")
        if self.width_utilisation_exact > 100:
            errors.append("The selected bin width is too small.")
        if self.length_utilisation_exact > 100:
            errors.append("The selected bin length is too small.")
        if self.height_utilisation_exact > 100:
            errors.append("The selected bin height is too small.")
        return tuple(errors)

    @property
    def is_valid(self) -> bool:
        return not self.validation_errors

    @property
    def overview(self) -> dict[str, float | int]:
        return {
            "required_width_mm": self.required_width_mm,
            "required_depth_mm": self.required_depth_mm,
            "required_length_mm": self.required_length_mm,
            "u_width": self.u_width,
            "u_length": self.u_length,
            "u_height": self.u_height,
            "slot_gap_mm": self.slot_gap_mm,
            "width_utilisation": self.width_utilisation,
            "length_utilisation": self.length_utilisation,
            "height_utilisation": self.height_utilisation,
        }


def _optional_positive_int(value: int | None, description: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{description} must be a whole number of Gridfinity units.")
    if value <= 0:
        raise ValueError(f"{description} must be at least one Gridfinity unit.")
    return value
