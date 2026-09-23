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


def add_header(command_inputs, table):
    """Add the fixed drill-table header row."""
    measurement_header = command_inputs.addStringValueInput(
        "measurement_header", "", "Bit Diameter (mm)"
    )
    measurement_header.isReadOnly = True

    optional_header = command_inputs.addStringValueInput(
        "optional_integer_header", "", "Bit Length (mm)"
    )
    optional_header.isReadOnly = True

    table.addCommandInput(measurement_header, HEADER_ROW, 0)
    table.addCommandInput(optional_header, HEADER_ROW, 1)


def add_row(table, measurement_mm=0.0, optional_integer_mm=None):
    """Append one editable row and select it."""
    global _next_row_id

    command_inputs = adsk.core.CommandInputs.cast(table.commandInputs)
    if command_inputs is None:
        raise RuntimeError("Unable to access the drill-table command inputs.")
    row_id = _next_row_id
    _next_row_id += 1

    measurement = command_inputs.addValueInput(
        "{}{}{}".format(DRILL_BIT_SPEC_PREFIX, "diameter", row_id),
        "",
        "mm",
        adsk.core.ValueInput.createByString(f"{measurement_mm:.1f} mm"),
    )
    if measurement is None:
        raise RuntimeError("Failed to create a drill diameter input.")
    measurement.tooltip = "Bit diameter in millimetres (one decimal place)"

    optional_text = "" if optional_integer_mm is None else str(int(optional_integer_mm))
    optional_integer = command_inputs.addStringValueInput(
        "{}{}{}".format(DRILL_BIT_SPEC_PREFIX, "length", row_id),
        "",
        optional_text,
    )
    if optional_integer is None:
        raise RuntimeError("Failed to create a drill length input.")
    optional_integer.tooltip = "Bit length in millimetres (optional)"

    row = table.rowCount
    table.addCommandInput(measurement, row, 0)
    table.addCommandInput(optional_integer, row, 1)
    table.selectedRow = row


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
        optional_input = adsk.core.StringValueCommandInput.cast(
            table.getInputAtPosition(row, 1)
        )

        if not diameter_input or not optional_input:
            raise RuntimeError(f"Drill-bit table row {row} is incomplete.")

        # ValueCommandInput.value is in Fusion's database length unit (cm).
        diameter_mm = internal_length_to_mm(diameter_input.value)

        optional_text = optional_input.value.strip()
        optional_length_mm = int(optional_text) if optional_text else None

        # Zero is the sentinel used by the UI for an unused placeholder row.
        if diameter_mm == 0 and optional_length_mm is None:
            continue

        rows.append(
            {
                "diameter_mm": diameter_mm,
                "optional_length_mm": optional_length_mm,
            }
        )

    return rows


def _is_optional_positive_integer_valid(value):
    """Return True when value is blank or is a positive whole number."""
    text = value.strip()
    return not text or (bool(INTEGER_PATTERN.fullmatch(text)) and int(text) > 0)
