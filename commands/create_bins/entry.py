"""Fusion UI controller for the Create Drill Bit Bins command."""

from __future__ import annotations

import os
from collections.abc import Callable

import adsk.core
import adsk.fusion

from ... import config
from ...generators import GridfinityGenerator
from ...lib import fusion360utils as futil
from ...model import (
    DrillBitType,
    GridfinityDrillBitBin,
)
from ...utils import fusion as fusion_utils
from ...utils import tables
from .dialog import (
    DRILL_BIT_TABLE_ADD_ROW_ID,
    DRILL_BIT_TABLE_ID,
    DRILL_BIT_TABLE_REMOVE_ROW_ID,
    DRILL_TYPE_INPUT_ID,
    GRIDFINITY_BIN_HEIGHT_AUTO_ID,
    GRIDFINITY_BIN_HEIGHT_ID,
    GRIDFINITY_BIN_LENGTH_AUTO_ID,
    GRIDFINITY_BIN_LENGTH_ID,
    GRIDFINITY_BIN_SPLIT_MULTICOLOR_ID,
    GRIDFINITY_BIN_WIDTH_AUTO_ID,
    GRIDFINITY_BIN_WIDTH_ID,
    GRIDFINITY_UTILISATION_HEIGHT_ID,
    GRIDFINITY_UTILISATION_LENGTH_ID,
    GRIDFINITY_UTILISATION_WIDTH_ID,
    build_dialog,
)

_definition_handlers = []
_command_handlers = []
_gridfinity_bin = GridfinityDrillBitBin()


def start() -> None:
    """Create the command definition and add its toolbar control."""
    app = adsk.core.Application.get()
    if app is None:
        raise RuntimeError("Fusion is not available.")
    ui = app.userInterface
    if ui is None:
        raise RuntimeError("Fusion's user interface is not available.")

    # Development reloads can leave UI objects behind if an earlier stop failed.
    futil.clear_handlers(_definition_handlers)
    futil.clear_handlers(_command_handlers)
    _delete_ui_objects(ui)
    panel = _toolbar_panel(ui)

    try:
        resource_dir = _available_resource_directory()
        if resource_dir:
            command_definition = ui.commandDefinitions.addButtonDefinition(
                config.CREATE_BINS_COMMAND_ID,
                config.CREATE_BINS_COMMAND_NAME,
                config.CREATE_BINS_COMMAND_DESCRIPTION,
                resource_dir,
            )
        else:
            command_definition = ui.commandDefinitions.addButtonDefinition(
                config.CREATE_BINS_COMMAND_ID,
                config.CREATE_BINS_COMMAND_NAME,
                config.CREATE_BINS_COMMAND_DESCRIPTION,
            )
        if command_definition is None:
            raise RuntimeError("Failed to create the Fusion command definition.")

        futil.add_handler(
            command_definition.commandCreated,
            command_created,
            local_handlers=_definition_handlers,
        )

        insert_after = panel.controls.itemById(config.CREATE_BINS_INSERT_AFTER_ID)
        if insert_after:
            control = panel.controls.addCommand(
                command_definition,
                config.CREATE_BINS_INSERT_AFTER_ID,
                False,
            )
        else:
            control = panel.controls.addCommand(command_definition)
        if control is None:
            raise RuntimeError("Failed to add the command to the Fusion toolbar.")
        control.isPromotedByDefault = True
        control.isPromoted = True
    except Exception:
        futil.clear_handlers(_definition_handlers)
        _delete_ui_objects(ui)
        raise

    futil.log(f"Registered command: {config.CREATE_BINS_COMMAND_NAME}")


def stop() -> None:
    """Remove command UI and release all retained event handlers."""
    futil.clear_handlers(_command_handlers)
    futil.clear_handlers(_definition_handlers)

    app = adsk.core.Application.get()
    if app:
        _delete_ui_objects(app.userInterface)


def command_created(args: adsk.core.CommandCreatedEventArgs) -> None:
    """Build the command dialog and connect command-lifetime events."""
    global _gridfinity_bin

    futil.clear_handlers(_command_handlers)
    _gridfinity_bin = GridfinityDrillBitBin()
    tables.reset_row_ids()

    command = args.command
    build_dialog(command, _gridfinity_bin)

    futil.add_handler(
        command.execute, command_execute, local_handlers=_command_handlers
    )
    futil.add_handler(
        command.inputChanged,
        command_input_changed,
        local_handlers=_command_handlers,
    )
    futil.add_handler(
        command.validateInputs,
        command_validate_inputs,
        local_handlers=_command_handlers,
    )
    futil.add_handler(
        command.destroy, command_destroy, local_handlers=_command_handlers
    )


def command_input_changed(args: adsk.core.InputChangedEventArgs) -> None:
    """Synchronise the domain model and dependent UI values."""
    changed_id = args.input.id
    sending_command = args.firingEvent.sender
    inputs = sending_command.commandInputs

    if changed_id == DRILL_TYPE_INPUT_ID:
        bit_type = _typed_input(
            inputs,
            DRILL_TYPE_INPUT_ID,
            adsk.core.DropDownCommandInput.cast,
            "Drill Bit Type Selection",
        )
        selected_bit_type = DrillBitType.from_display_name(bit_type.selectedItem.name)
        _gridfinity_bin.set_bit_type(selected_bit_type)
        update_bin_from_inputs(inputs)

    elif changed_id == DRILL_BIT_TABLE_ADD_ROW_ID:
        table = _typed_input(
            inputs,
            DRILL_BIT_TABLE_ID,
            adsk.core.TableCommandInput.cast,
            "Drill Bit Table",
        )
        tables.add_row(table)

    elif changed_id == DRILL_BIT_TABLE_REMOVE_ROW_ID:
        table = _typed_input(
            inputs,
            DRILL_BIT_TABLE_ID,
            adsk.core.TableCommandInput.cast,
            "Drill Bit Table",
        )
        selected_row = table.selectedRow
        if selected_row <= 0:
            return

        table.deleteRow(selected_row)
        if table.rowCount > tables.HEADER_ROW + 1:
            table.selectedRow = min(selected_row, table.rowCount - 1)
        else:
            table.selectedRow = -1
        update_bin_from_inputs(inputs)
        return

    elif changed_id in {GRIDFINITY_BIN_WIDTH_ID, GRIDFINITY_BIN_WIDTH_AUTO_ID}:
        _gridfinity_bin.explicit_u_width = auto_property_handler(
            inputs,
            GRIDFINITY_BIN_WIDTH_AUTO_ID,
            GRIDFINITY_BIN_WIDTH_ID,
            _gridfinity_bin.calculated_u_width,
        )
        update_utilisation(inputs)

    elif changed_id in {GRIDFINITY_BIN_LENGTH_ID, GRIDFINITY_BIN_LENGTH_AUTO_ID}:
        _gridfinity_bin.explicit_u_length = auto_property_handler(
            inputs,
            GRIDFINITY_BIN_LENGTH_AUTO_ID,
            GRIDFINITY_BIN_LENGTH_ID,
            _gridfinity_bin.calculated_u_length,
        )
        update_utilisation(inputs)

    elif changed_id in {GRIDFINITY_BIN_HEIGHT_ID, GRIDFINITY_BIN_HEIGHT_AUTO_ID}:
        _gridfinity_bin.explicit_u_height = auto_property_handler(
            inputs,
            GRIDFINITY_BIN_HEIGHT_AUTO_ID,
            GRIDFINITY_BIN_HEIGHT_ID,
            _gridfinity_bin.calculated_u_height,
        )
        update_utilisation(inputs)

    elif changed_id.startswith(tables.DRILL_BIT_SPEC_PREFIX):
        update_bin_from_inputs(inputs)


def auto_property_handler(
    inputs: adsk.core.CommandInputs,
    auto_control_id: str,
    value_control_id: str,
    calculated_value: int,
) -> int | None:
    """Enable a manual U field or refresh its automatically calculated value."""
    auto_input = _typed_input(
        inputs, auto_control_id, adsk.core.BoolValueCommandInput.cast, "boolean"
    )
    value_input = _typed_input(
        inputs, value_control_id, adsk.core.IntegerSpinnerCommandInput.cast, "length"
    )
    value_input.isEnabled = not auto_input.value

    if auto_input.value:
        value_input.value = calculated_value
        return None

    return value_input.value


def update_bin_from_inputs(inputs: adsk.core.CommandInputs) -> None:
    """Rebuild the specification from the current dialog state."""
    split_multicolor = _typed_input(
        inputs,
        GRIDFINITY_BIN_SPLIT_MULTICOLOR_ID,
        adsk.core.BoolValueCommandInput.cast,
        "multi-colour split",
    )
    _gridfinity_bin.split_for_multicolor = split_multicolor.value

    bit_type = _typed_input(
        inputs,
        DRILL_TYPE_INPUT_ID,
        adsk.core.DropDownCommandInput.cast,
        "Drill Bit Type Selection",
    )

    selected_bit_type = DrillBitType.from_display_name(bit_type.selectedItem.name)

    _gridfinity_bin.set_bit_type(selected_bit_type)
    _gridfinity_bin.clear_bits()

    drill_bit_table = _typed_input(
        inputs, DRILL_BIT_TABLE_ID, adsk.core.TableCommandInput.cast, "Drill Bit Table"
    )

    if not tables.validate_rows(drill_bit_table):
        update_utilisation(inputs)
        return

    drill_bit_rows = tables.read_rows(drill_bit_table)

    for drill_bit in drill_bit_rows:
        _gridfinity_bin.add_bit(
            drill_bit["diameter_mm"], drill_bit["optional_length_mm"]
        )

    _gridfinity_bin.explicit_u_width = auto_property_handler(
        inputs,
        GRIDFINITY_BIN_WIDTH_AUTO_ID,
        GRIDFINITY_BIN_WIDTH_ID,
        _gridfinity_bin.calculated_u_width,
    )

    _gridfinity_bin.explicit_u_length = auto_property_handler(
        inputs,
        GRIDFINITY_BIN_LENGTH_AUTO_ID,
        GRIDFINITY_BIN_LENGTH_ID,
        _gridfinity_bin.calculated_u_length,
    )

    _gridfinity_bin.explicit_u_height = auto_property_handler(
        inputs,
        GRIDFINITY_BIN_HEIGHT_AUTO_ID,
        GRIDFINITY_BIN_HEIGHT_ID,
        _gridfinity_bin.calculated_u_height,
    )

    update_utilisation(inputs)


def update_utilisation(inputs: adsk.core.CommandInputs) -> None:
    _typed_input(
        inputs,
        GRIDFINITY_UTILISATION_WIDTH_ID,
        adsk.core.StringValueCommandInput.cast,
        "Width Utilisation",
    ).value = f"{_gridfinity_bin.width_utilisation} %"

    _typed_input(
        inputs,
        GRIDFINITY_UTILISATION_LENGTH_ID,
        adsk.core.StringValueCommandInput.cast,
        "Length Utilisation",
    ).value = f"{_gridfinity_bin.length_utilisation} %"

    _typed_input(
        inputs,
        GRIDFINITY_UTILISATION_HEIGHT_ID,
        adsk.core.StringValueCommandInput.cast,
        "Height Utilisation",
    ).value = f"{_gridfinity_bin.height_utilisation} %"


def command_validate_inputs(args: adsk.core.ValidateInputsEventArgs) -> None:
    """Set Fusion's normal OK-button validation state."""
    try:
        inputs = args.inputs

        drill_bit_table = _typed_input(
            inputs,
            DRILL_BIT_TABLE_ID,
            adsk.core.TableCommandInput.cast,
            "Drill Bit Table",
        )
        if not tables.validate_rows(drill_bit_table):
            args.areInputsValid = False
            return

        if validate_utilisation(
            inputs,
            GRIDFINITY_UTILISATION_WIDTH_ID,
            _gridfinity_bin.width_utilisation_exact,
        ):
            args.areInputsValid = False
            return

        if validate_utilisation(
            inputs,
            GRIDFINITY_UTILISATION_LENGTH_ID,
            _gridfinity_bin.length_utilisation_exact,
        ):
            args.areInputsValid = False
            return

        if validate_utilisation(
            inputs,
            GRIDFINITY_UTILISATION_HEIGHT_ID,
            _gridfinity_bin.height_utilisation_exact,
        ):
            args.areInputsValid = False
            return

        args.areInputsValid = _gridfinity_bin.is_valid

    except Exception:
        args.areInputsValid = False
        raise


def validate_utilisation(
    inputs: adsk.core.CommandInputs, control_id: str, utilisation_value: float
) -> bool:
    control = _typed_input(
        inputs,
        control_id,
        adsk.core.StringValueCommandInput.cast,
        "Utilisation Validation",
    )
    is_error = utilisation_value > 100
    control.isValueError = is_error
    return is_error


def command_execute(args: adsk.core.CommandEventArgs) -> None:
    """Execute safely and tell Fusion to abort the transaction on failure."""
    futil.log("Executing command")
    try:
        _execute(args)
    except Exception as error:
        args.executeFailed = True
        args.executeFailedMessage = str(error)
        raise


def _execute(args: adsk.core.CommandEventArgs) -> None:
    """Translate UI values to domain models and invoke the bin generator."""
    inputs = args.command.commandInputs
    update_bin_from_inputs(inputs)
    if not _gridfinity_bin.is_valid:
        raise ValueError(" ".join(_gridfinity_bin.validation_errors))

    design = fusion_utils.get_active_design()
    futil.log("Generating Gridfinity bin")
    GridfinityGenerator(design).generate(_gridfinity_bin)


def command_destroy(args: adsk.core.CommandEventArgs) -> None:
    """Release command-lifetime handlers after OK, Cancel, or interruption."""
    futil.clear_handlers(_command_handlers)


def _find_input(inputs: adsk.core.CommandInputs, input_id: str):
    """Find an input recursively so later groups/tabs remain safe to introduce."""

    direct = inputs.itemById(input_id)
    if direct:
        return direct

    for index in range(inputs.count):
        command_input = inputs.item(index)
        children = getattr(command_input, "children", None)
        if children:
            found = _find_input(children, input_id)
            if found:
                return found
    return None


def _typed_input(inputs, input_id: str, cast: Callable, description: str):
    command_input = _find_input(inputs, input_id)
    typed_input = cast(command_input) if command_input else None
    if typed_input is None:
        raise RuntimeError(f"Missing or invalid {description} input: {input_id}")
    return typed_input


def _toolbar_panel(ui):
    workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
    if workspace is None:
        raise RuntimeError(f"Fusion workspace not found: {config.WORKSPACE_ID}")
    panel = workspace.toolbarPanels.itemById(config.PANEL_ID)
    if panel is None:
        raise RuntimeError(f"Fusion toolbar panel not found: {config.PANEL_ID}")
    return panel


def _delete_ui_objects(ui) -> None:
    """Best-effort deletion that tolerates partially deleted Fusion UI state."""
    workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
    if workspace:
        panel_ids = (config.PANEL_ID, *config.LEGACY_PANEL_IDS)
        for panel_id in panel_ids:
            panel = workspace.toolbarPanels.itemById(panel_id)
            if panel:
                control = panel.controls.itemById(config.CREATE_BINS_COMMAND_ID)
                if control and control.isValid:
                    control.deleteMe()

    command_definition = ui.commandDefinitions.itemById(config.CREATE_BINS_COMMAND_ID)
    if command_definition and command_definition.isValid:
        command_definition.deleteMe()


def _available_resource_directory() -> str | None:
    """Return the icon directory only when it contains a supported PNG icon."""
    candidates = ("16x16.png", "32x32.png", "64x64.png")
    if any(
        os.path.isfile(os.path.join(config.CREATE_BINS_RESOURCE_DIR, filename))
        for filename in candidates
    ):
        return config.CREATE_BINS_RESOURCE_DIR
    return None
