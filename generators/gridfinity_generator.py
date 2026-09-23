"""Direct Gridfinity base-bin generation using bundled upstream geometry."""

from __future__ import annotations

from typing import Any

import adsk.core
import adsk.fusion

from ..lib import fusion360utils as futil
from ..lib.gridfinityUtils import commonUtils, const, geometryUtils
from ..lib.gridfinityUtils.baseGenerator import (
    createBaseBodyPattern,
    cutBaseClearance,
)
from ..lib.gridfinityUtils.baseGeneratorInput import BaseGeneratorInput
from ..lib.gridfinityUtils.binBodyGenerator import createGridfinityBinBody
from ..lib.gridfinityUtils.binBodyGeneratorInput import BinBodyGeneratorInput
from ..model import GridfinityDrillBitBin
from ..utils.fusion import require_healthy_entity
from .drill_slot_generator import DrillSlotGenerator


class GridfinityGenerator:
    """Create a solid Gridfinity bin and add drill-specific geometry."""

    def __init__(self, design: Any) -> None:
        if design is None:
            raise ValueError("An active Fusion design is required.")
        self.design = design

    def generate(self, specification: GridfinityDrillBitBin) -> None:
        """Generate the complete holder synchronously in the active design."""
        if not isinstance(specification, GridfinityDrillBitBin):
            raise TypeError("specification must be a GridfinityDrillBitBin.")
        if not specification.is_valid:
            raise ValueError(" ".join(specification.validation_errors))
        if self.design.designType == adsk.fusion.DesignTypes.DirectDesignType:
            raise RuntimeError(
                "The Gridfinity generator requires design history to be enabled."
            )

        timeline = getattr(self.design, "timeline", None)
        timeline_start = timeline.count if timeline is not None else None
        target_component = self._create_target_component(specification)

        futil.log("Generating Gridfinity base bin")
        target_body = self._create_solid_bin(specification, target_component)
        self._group_timeline_features(
            timeline_start,
            self._bin_name(specification),
        )
        smallest_diameter = min(bit.diameter_mm for bit in specification.drill_bits)
        largest_diameter = max(bit.diameter_mm for bit in specification.drill_bits)
        diameter_range = f"{smallest_diameter:.1f}mm - {largest_diameter:.1f}mm"
        target_component.name = (
            f"{specification.u_width}x{specification.u_length}x"
            f"{specification.u_height} GF Bin "
            f"({specification.bit_type.value}, {diameter_range})"
        )
        target_body.name = "Holder"

        DrillSlotGenerator(self.design).generate(
            specification,
            target_component,
            target_body,
        )

    def _create_target_component(
        self, specification: GridfinityDrillBitBin
    ) -> adsk.fusion.Component:
        root = adsk.fusion.Component.cast(self.design.rootComponent)
        if root is None:
            raise RuntimeError("The active design has no root component.")

        # Fusion's Part design intent does not permit component occurrences.
        # This follows the current upstream generator behaviour for that mode.
        if (
            self.design.designIntent
            != adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        ):
            return root

        occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        if occurrence is None or occurrence.component is None:
            raise RuntimeError("Unable to create the Gridfinity bin component.")
        occurrence.component.name = self._bin_name(specification)
        if not occurrence.activate():
            raise RuntimeError("Unable to activate the Gridfinity bin component.")
        return occurrence.component

    def _create_solid_bin(
        self,
        specification: GridfinityDrillBitBin,
        target_component: adsk.fusion.Component,
    ) -> adsk.fusion.BRepBody:
        base_input = BaseGeneratorInput()
        base_input.originPoint = geometryUtils.createOffsetPoint(
            target_component.originConstructionPoint.geometry,
            byX=-const.BIN_XY_CLEARANCE,
            byY=-const.BIN_XY_CLEARANCE,
        )
        base_input.baseWidth = const.DIMENSION_DEFAULT_WIDTH_UNIT
        base_input.baseLength = const.DIMENSION_DEFAULT_WIDTH_UNIT
        base_input.xyClearance = const.BIN_XY_CLEARANCE
        base_input.hasScrewHoles = False
        base_input.hasMagnetCutouts = False

        base_bodies = createBaseBodyPattern(
            base_input,
            specification.u_width,
            specification.u_length,
            target_component,
        )

        body_input = BinBodyGeneratorInput()
        body_input.hasLip = True
        body_input.hasLipNotches = False
        body_input.binWidth = specification.u_width
        body_input.binLength = specification.u_length
        body_input.binHeight = specification.u_height
        body_input.baseWidth = const.DIMENSION_DEFAULT_WIDTH_UNIT
        body_input.baseLength = const.DIMENSION_DEFAULT_WIDTH_UNIT
        body_input.heightUnit = const.DIMENSION_DEFAULT_HEIGHT_UNIT
        body_input.xyClearance = const.BIN_XY_CLEARANCE
        body_input.binCornerFilletRadius = (
            const.BIN_CORNER_FILLET_RADIUS - const.BIN_XY_CLEARANCE
        )
        body_input.isSolid = True
        body_input.wallThickness = const.BIN_WALL_THICKNESS
        body_input.hasScoop = False
        body_input.hasTab = False

        bin_body = createGridfinityBinBody(body_input, target_component)
        cutBaseClearance(
            base_input,
            specification.u_width,
            specification.u_length,
            target_component,
        )

        combine_features = target_component.features.combineFeatures
        combine_input = combine_features.createInput(
            bin_body,
            commonUtils.objectCollectionFromList(base_bodies),
        )
        if combine_input is None:
            raise RuntimeError("Unable to create the Gridfinity body-join input.")
        combine_feature = combine_features.add(combine_input)
        require_healthy_entity(
            combine_feature,
            "Gridfinity base and bin body join",
        )

        bin_body.name = self._bin_name(specification)
        return bin_body

    def _group_timeline_features(
        self,
        start_index: int | None,
        name: str,
    ) -> None:
        if start_index is None:
            return
        try:
            end_index = self.design.timeline.count - 1
            if end_index < start_index:
                return
            group = self.design.timeline.timelineGroups.add(start_index, end_index)
            if group is not None:
                group.name = name
        except RuntimeError as error:
            # Grouping is presentation-only; valid generated geometry is kept.
            futil.log(f"Unable to group Gridfinity bin timeline features: {error}")

    @staticmethod
    def _bin_name(specification: GridfinityDrillBitBin) -> str:
        return (
            f"Gridfinity bin {specification.u_length}x"
            f"{specification.u_width}x{specification.u_height}"
        )
