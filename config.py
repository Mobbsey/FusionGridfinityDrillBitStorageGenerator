"""Shared configuration for the Drill Bit Gridfinity add-in."""

from __future__ import annotations

import os

ADDIN_DISPLAY_NAME = "Gridfinity Drill Bit Holder Generator"
DEBUG = False

# Stable IDs belonging to Fusion's Design workspace.
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidCreatePanel"
LEGACY_PANEL_IDS = ("SolidScriptsAddinsPanel",)
CREATE_BINS_INSERT_AFTER_ID = "ScriptsManagerCommand"

CREATE_BINS_COMMAND_ID = "DrillBitGridfinity_CreateBins"
CREATE_BINS_COMMAND_NAME = "Create Drill Bit Bins"
CREATE_BINS_COMMAND_DESCRIPTION = (
    "Create Gridfinity-compatible storage bins with drill slots and labels."
)

ADDIN_ROOT = os.path.dirname(os.path.abspath(__file__))
CREATE_BINS_RESOURCE_DIR = os.path.join(
    ADDIN_ROOT, "commands", "create_bins", "resources"
)
