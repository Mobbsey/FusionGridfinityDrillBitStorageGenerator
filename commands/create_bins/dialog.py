"""Command-input IDs and construction for the Create Drill Bit Bins dialog."""

from __future__ import annotations

import adsk.core

from ...model import DrillBitType, GridfinityDrillBitBin
from ...utils import tables

DRILL_BIT_GROUP_ID = "drill_bit_group"
DRILL_TYPE_INPUT_ID = "drill_type"
DRILL_BIT_TABLE_ID = "drill_bit_table"
DRILL_BIT_TABLE_ADD_ROW_ID = "add_drill_bit_row"
DRILL_BIT_TABLE_REMOVE_ROW_ID = "remove_drill_bit_row"
GRIDFINITY_BIN_GROUP_ID = "gridfinity_bin_group"
GRIDFINITY_BIN_WIDTH_ID = "gridfinity_bin_width"
GRIDFINITY_BIN_WIDTH_AUTO_ID = "gridfinity_bin_width_auto"
GRIDFINITY_BIN_WIDTH_SEPARATOR_ID = "gridfinity_bin_width_separator"
GRIDFINITY_BIN_LENGTH_ID = "gridfinity_bin_length"
GRIDFINITY_BIN_LENGTH_AUTO_ID = "gridfinity_bin_length_auto"
GRIDFINITY_BIN_LENGTH_SEPARATOR_ID = "gridfinity_bin_length_separator"
GRIDFINITY_BIN_HEIGHT_ID = "gridfinity_bin_height"
GRIDFINITY_BIN_HEIGHT_AUTO_ID = "gridfinity_bin_height_auto"
GRIDFINITY_BIN_OUTPUT_SEPARATOR_ID = "gridfinity_bin_output_separator"
GRIDFINITY_BIN_SPLIT_MULTICOLOR_ID = "gridfinity_bin_split_multicolor"
GRIDFINITY_UTILISATION_GROUP_ID = "gridfinity_util_group"
GRIDFINITY_UTILISATION_WIDTH_ID = "gridfinity_util_group_width"
GRIDFINITY_UTILISATION_LENGTH_ID = "gridfinity_util_group_length"
GRIDFINITY_UTILISATION_HEIGHT_ID = "gridfinity_util_group_height"


def build_dialog(
    command: adsk.core.Command,
    specification: GridfinityDrillBitBin,
) -> None:
    """Create all inputs for a new command instance."""
    inputs = command.commandInputs

    drill_bit_group = inputs.addGroupCommandInput(DRILL_BIT_GROUP_ID, "Drill Bits")
    drill_bit_group.isExpanded = True

    drill_type_input = drill_bit_group.children.addDropDownCommandInput(
        DRILL_TYPE_INPUT_ID,
        "Drill Type",
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    for index, drill_type in enumerate(DrillBitType):
        drill_type_input.listItems.add(drill_type.value, index == 0)

    drill_bit_table = drill_bit_group.children.addTableCommandInput(
        DRILL_BIT_TABLE_ID, "Drill Bits", 2, "1:1"
    )
    drill_bit_table.minimumVisibleRows = 3
    drill_bit_table.maximumVisibleRows = 10
    drill_bit_table.columnSpacing = 2
    drill_bit_table.rowSpacing = 2
    drill_bit_table.hasGrid = True
    drill_bit_table.tablePresentationStyle = (
        adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
    )
    tables.add_header(inputs, drill_bit_table)
    for _ in range(4):
        tables.add_row(drill_bit_table)

    add_button = inputs.addBoolValueInput(
        DRILL_BIT_TABLE_ADD_ROW_ID, "Add Row", False, "", False
    )
    add_button.text = "Add Row"
    drill_bit_table.addToolbarCommandInput(add_button)

    remove_button = inputs.addBoolValueInput(
        DRILL_BIT_TABLE_REMOVE_ROW_ID, "Remove Selected Row", False, "", False
    )
    remove_button.text = "Remove Selected Row"
    drill_bit_table.addToolbarCommandInput(remove_button)

    gridfinity_bin_group = inputs.addGroupCommandInput(
        GRIDFINITY_BIN_GROUP_ID, "Gridfinity Bin"
    )
    gridfinity_bin_group.isExpanded = True
    gridfinity_bin_group.children.addBoolValueInput(
        GRIDFINITY_BIN_WIDTH_AUTO_ID, "Auto Width", True, "", True
    )

    gridfinity_bin_width = gridfinity_bin_group.children.addIntegerSpinnerCommandInput(
        GRIDFINITY_BIN_WIDTH_ID, "Bin Width (U)", 1, 10, 1, specification.u_width
    )
    gridfinity_bin_width.isEnabled = False
    gridfinity_bin_width.tooltip = (
        "Automatically calculate width. Disable Auto Width to edit."
    )
    gridfinity_bin_group.children.addSeparatorCommandInput(
        GRIDFINITY_BIN_WIDTH_SEPARATOR_ID
    )

    gridfinity_bin_group.children.addBoolValueInput(
        GRIDFINITY_BIN_LENGTH_AUTO_ID, "Auto Length", True, "", True
    )
    gridfinity_bin_length = gridfinity_bin_group.children.addIntegerSpinnerCommandInput(
        GRIDFINITY_BIN_LENGTH_ID,
        "Bin Length (U)",
        1,
        10,
        1,
        specification.u_length,
    )
    gridfinity_bin_length.isEnabled = False
    gridfinity_bin_length.tooltip = (
        "Automatically calculate length. Disable Auto Length to edit."
    )
    gridfinity_bin_group.children.addSeparatorCommandInput(
        GRIDFINITY_BIN_LENGTH_SEPARATOR_ID
    )

    gridfinity_bin_group.children.addBoolValueInput(
        GRIDFINITY_BIN_HEIGHT_AUTO_ID, "Auto Height", True, "", True
    )
    gridfinity_bin_height = gridfinity_bin_group.children.addIntegerSpinnerCommandInput(
        GRIDFINITY_BIN_HEIGHT_ID,
        "Bin Height (U)",
        1,
        10,
        1,
        specification.u_height,
    )
    gridfinity_bin_height.isEnabled = False
    gridfinity_bin_height.tooltip = (
        "Automatically calculate height. Disable Auto Height to edit."
    )
    gridfinity_bin_group.children.addSeparatorCommandInput(
        GRIDFINITY_BIN_OUTPUT_SEPARATOR_ID
    )
    split_multicolor = gridfinity_bin_group.children.addBoolValueInput(
        GRIDFINITY_BIN_SPLIT_MULTICOLOR_ID,
        "Split Body",
        True,
        "",
        specification.split_for_multicolor,
    )
    split_multicolor.tooltip = (
        "Split the embossed labels from the holder so each can be printed "
        "in a different colour."
    )

    utilisation_group = inputs.addGroupCommandInput(
        GRIDFINITY_UTILISATION_GROUP_ID, "Gridfinity Bin Utilisation"
    )
    utilisation_group.isExpanded = True

    for input_id, label in (
        (GRIDFINITY_UTILISATION_WIDTH_ID, "Width"),
        (GRIDFINITY_UTILISATION_LENGTH_ID, "Length"),
        (GRIDFINITY_UTILISATION_HEIGHT_ID, "Height"),
    ):
        utilisation = utilisation_group.children.addStringValueInput(
            input_id, label, "0"
        )
        utilisation.isReadOnly = True
