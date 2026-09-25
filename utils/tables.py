import re

import adsk.core

from .fusion import internal_length_to_mm

DRILL_BIT_SPEC_PREFIX = "drill_bit_"
HEADER_ROW = 0
INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
_next_row_id = 0


def reset_row_ids():
    """Reset command-input IDs for a newly created command dialog."""
    global _next_row_id
    _next_row_id = 0


def add_header(command_inputs: adsk.core.CommandInputs , table):
    """Add the fixed drill-table header row."""
    diameter_header = command_inputs.addStringValueInput(
        "diameter_header", "", "Bit Diameter (mm)"
    )
    diameter_header.isReadOnly = True

    length_header = command_inputs.addStringValueInput(
            "length_header", "", "Bit Length (mm)"
        )
    length_header.isReadOnly = True
        
    width_header = command_inputs.addStringValueInput(
            "width_header", "", "Bin Width"
        )
    width_header.isReadOnly = True
    width_header.isVisible = False
    
    depth_header = command_inputs.addStringValueInput(
            "depth_header", "", "Bin Depth"
        )
    depth_header.isReadOnly = True
    depth_header.isVisible = False

    table.addCommandInput(diameter_header, HEADER_ROW, 0)
    table.addCommandInput(length_header, HEADER_ROW, 1)
    table.addCommandInput(width_header, HEADER_ROW, 2)
    table.addCommandInput(depth_header, HEADER_ROW, 3)


def add_row(table, measurement_mm=0.0, optional_integer_mm=None, width = 2, depth = 2):
    """Append one editable row and select it."""
    global _next_row_id

    table_input = adsk.core.CommandInputs.cast(table.commandInputs)
    if table_input is None:
        raise RuntimeError("Unable to access the drill-table command inputs.")
    row_id = _next_row_id
    _next_row_id += 1

    diameter_input = table_input.addValueInput(
        "{}{}{}".format(DRILL_BIT_SPEC_PREFIX, "diameter", row_id),
        "",
        "mm",
        adsk.core.ValueInput.createByString(f"{measurement_mm:.1f} mm"),
    )
    if diameter_input is None:
        raise RuntimeError("Failed to create a drill diameter input.")
    diameter_input.tooltip = "Bit diameter in millimetres (one decimal place)"

    length_text = "" if optional_integer_mm is None else str(int(optional_integer_mm))
    length_input = table_input.addStringValueInput(
        "{}{}{}".format(DRILL_BIT_SPEC_PREFIX, "length", row_id),
        "",
        length_text,
    )
    if length_input is None:
        raise RuntimeError("Failed to create a drill length input.")
    length_input.tooltip = "Bit length in millimetres (default: blank/auto)"

    width_input = table_input.addIntegerSpinnerCommandInput(
        "{}{}{}".format(DRILL_BIT_SPEC_PREFIX, "width", row_id),
        "",
        1,
        5,
        1,
        width
    )
    if width_input is None:
        raise RuntimeError("Failed to create a drill bin width input.")
    width_input.tooltip = "Number of bits to fit in the width of the bin (default: 2)"
    width_input.isVisible = False

    depth_input = table_input.addIntegerSpinnerCommandInput(
        "{}{}{}".format(DRILL_BIT_SPEC_PREFIX, "depth", row_id),
        "",
        1,
        5,
        1,
        depth
    )
    if depth_input is None:
        raise RuntimeError("Failed to create a drill bin depth input.")
    depth_input.tooltip = "Number of bits to fit in the depth of the bin (default: 2)"
    depth_input.isVisible = False

    row = table.rowCount
    table.addCommandInput(diameter_input, row, 0)
    table.addCommandInput(length_input, row, 1)
    table.addCommandInput(width_input, row, 2)
    table.addCommandInput(depth_input, row, 3)
    table.selectedRow = row


def extended_properties_visible(table: adsk.core.TableCommandInput, visibility:bool):
    for row in range(0, table.rowCount):
        for col in range(2, 4):
            table.getInputAtPosition(row, col).isVisible = visibility
    if visibility:
        table.columnRatio = "5:4:3:3"
    else:
        table.columnRatio = "5:4:0:0"


def validate_rows(table):
    """Validate data rows while allowing completely empty placeholder rows."""
    all_valid = True

    for row in range(HEADER_ROW + 1, table.rowCount):
        diameter_input = adsk.core.ValueCommandInput.cast(
            table.getInputAtPosition(row, 0)
        )
        optional_input = adsk.core.StringValueCommandInput.cast(
            table.getInputAtPosition(row, 1)
        )
        if not diameter_input or not optional_input:
            all_valid = False
            continue

        diameter_is_valid = (
            diameter_input.isValidExpression and diameter_input.value >= 0
        )
        optional_is_valid = _is_optional_positive_integer_valid(optional_input.value)

        # A zero diameter represents an unused placeholder row. A supplied
        # length makes the row non-empty and therefore requires a diameter.
        row_is_empty = (
            diameter_is_valid
            and diameter_input.value == 0
            and not optional_input.value.strip()
        )
        row_is_valid = row_is_empty or (
            diameter_is_valid and diameter_input.value > 0 and optional_is_valid
        )
        diameter_input.isValueError = not row_is_valid
        optional_input.isValueError = not row_is_valid
        all_valid = all_valid and row_is_valid

    return all_valid


def read_rows(table):
    """Convert the UI rows to ordinary Python values."""
    rows = []

    for row in range(HEADER_ROW + 1, table.rowCount):
        diameter_input = adsk.core.ValueCommandInput.cast(
            table.getInputAtPosition(row, 0)
        )
        length_input = adsk.core.StringValueCommandInput.cast(
            table.getInputAtPosition(row, 1)
        )

        width_input = adsk.core.IntegerSpinnerCommandInput.cast(
            table.getInputAtPosition(row, 2)
        )

        depth_input = adsk.core.IntegerSpinnerCommandInput.cast(
            table.getInputAtPosition(row, 3)
        )

        if not diameter_input or not length_input or not width_input or not depth_input:
            raise RuntimeError(f"Drill-bit table row {row} is incomplete.")

        # ValueCommandInput.value is in Fusion's database length unit (cm).
        diameter_mm = internal_length_to_mm(diameter_input.value)

        length_text = length_input.value.strip()
        length_mm = int(length_text) if length_text else None

        width = width_input.value

        depth = depth_input.value

        # Zero is the sentinel used by the UI for an unused placeholder row.
        if diameter_mm == 0 and length_mm is None:
            continue

        rows.append(
            {
                "diameter_mm": diameter_mm,
                "optional_length_mm": length_mm,
                "width": width,
                "depth": depth,
            }
        )

    return rows


def _is_optional_positive_integer_valid(value):
    """Return True when value is blank or is a positive whole number."""
    text = value.strip()
    return not text or (bool(INTEGER_PATTERN.fullmatch(text)) and int(text) > 0)
