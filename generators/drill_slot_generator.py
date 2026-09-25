"""Drill-slot and label geometry generation."""

from __future__ import annotations

import math
from typing import Any

import adsk.core
import adsk.fusion

from ..lib import fusion360utils as futil
from ..model import DrillBit, GridfinityDrillBitBin
from ..utils.body_tools import (
    apply_chamfer_from_cutfeature,
    extrude_cut_operation,
    get_top_face,
)
from ..utils.fusion import mm_to_internal_length, require_healthy_entity


class DrillSlotGenerator:
    """Generate storage slots for the specified drill bits."""

    INNER_HEIGHT_REDUCTION_MM = 2.15
    SLOT_CUT_START_OFFSET_MM = 4.0
    BIN_PROFILE_TOP_OFFSET_MM = 8.8

    def __init__(self, design: Any) -> None:
        if design is None:
            raise ValueError("An active Fusion design is required.")
        self.design = design
        self.gridfinity_bin: GridfinityDrillBitBin | None = None
        self.slot_sketches: list[tuple[DrillBit, adsk.fusion.Sketch]] = []

    def generate(
        self,
        specification: GridfinityDrillBitBin,
        target_component: adsk.fusion.Component,
        target_body: adsk.fusion.BRepBody,
    ) -> None:
        """Cut drill slots and emboss labels into the supplied base bin."""
        if not isinstance(specification, GridfinityDrillBitBin):
            raise TypeError("specification must be a GridfinityDrillBitBin.")
        if not specification.is_valid:
            raise ValueError(" ".join(specification.validation_errors))

        self.gridfinity_bin = specification

        self.create_drill_slots(target_component, target_body)

    def reduce_inner_bin_height(
        self, target_body: adsk.fusion.BRepBody, target_component: adsk.fusion.Component
    ):
        top_face = get_top_face(target_body)
        if top_face is None:
            raise RuntimeError("Unable to find a horizontal top face on the bin body.")

        extrude_cut_operation(
            target_component, top_face, -self.INNER_HEIGHT_REDUCTION_MM
        )

    def create_bin_sketch(
        self,
        sketches: adsk.fusion.Sketches,
        front_plane: adsk.fusion.ConstructionPlane,
        left_offset_cm: float,
        bit: DrillBit,
    ) -> adsk.fusion.Sketch:
        sketch = sketches.add(front_plane)
        if sketch is None:
            raise RuntimeError(
                f"Failed to create slot sketch for {bit.diameter_mm} mm."
            )

        # Fusion otherwise recomputes the sketch after every added entity and
        # constraint. Re-enable computation before profiles are inspected.
        sketch.isComputeDeferred = True
        try:
            self._populate_bin_sketch(sketch, left_offset_cm, bit)
        finally:
            sketch.isComputeDeferred = False

        require_healthy_entity(sketch, f"Slot sketch for {bit.diameter_mm:g} mm")
        return sketch

    def _populate_bin_sketch(
        self,
        sketch: adsk.fusion.Sketch,
        left_offset_cm: float,
        bit: DrillBit,
    ) -> None:
        """Add the constrained cross-section for one drill slot."""
        sketch.name = f"Drill slot - {bit.diameter_mm:g} mm"
        sketch_lines = sketch.sketchCurves.sketchLines
        dimensions = sketch.sketchDimensions

        def dimension_label_point(sketch_point):
            geometry = sketch_point.geometry
            return adsk.core.Point3D.create(geometry.x - 1, geometry.y - 1, 0)

        # Seed geometry only establishes orientation. Driving dimensions below
        # define the final profile using Fusion's internal centimetre units.
        lower_half_width_line = sketch_lines.addByTwoPoints(
            adsk.core.Point3D.create(
                sketch.originPoint.geometry.x + 1, sketch.originPoint.geometry.y - 1, 0
            ),
            adsk.core.Point3D.create(
                sketch.originPoint.geometry.x + 3, sketch.originPoint.geometry.y - 1, 0
            ),
        )
        sketch.geometricConstraints.addHorizontal(lower_half_width_line)
        dimensions.addDistanceDimension(
            lower_half_width_line.startSketchPoint,
            sketch.originPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            dimension_label_point(lower_half_width_line.endSketchPoint),
        ).value = (
            mm_to_internal_length(self.gridfinity_bin.slot_gap_mm) + left_offset_cm
        )
        dimensions.addDistanceDimension(
            lower_half_width_line.startSketchPoint,
            lower_half_width_line.endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            dimension_label_point(lower_half_width_line.endSketchPoint),
        ).value = mm_to_internal_length(bit.slot_width_mm / 2)
        dimensions.addDistanceDimension(
            lower_half_width_line.startSketchPoint,
            sketch.originPoint,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            dimension_label_point(lower_half_width_line.endSketchPoint),
        ).value = mm_to_internal_length(
            self.gridfinity_bin.height_mm
            - self.BIN_PROFILE_TOP_OFFSET_MM
            - self.INNER_HEIGHT_REDUCTION_MM
        )

        outer_vertical_line = sketch_lines.addByTwoPoints(
            lower_half_width_line.startSketchPoint,
            adsk.core.Point3D.create(
                lower_half_width_line.startSketchPoint.geometry.x + 1,
                lower_half_width_line.startSketchPoint.geometry.y + 1,
                0,
            ),
        )
        sketch.geometricConstraints.addVertical(outer_vertical_line)

        lower_corner_arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
            adsk.core.Point3D.create(
                outer_vertical_line.endSketchPoint.geometry.x + 1,
                outer_vertical_line.endSketchPoint.geometry.y,
                0,
            ),
            outer_vertical_line.endSketchPoint,
            math.radians(-90),
        )

        sketch.geometricConstraints.addTangent(lower_corner_arc, outer_vertical_line)
        dimensions.addRadialDimension(
            lower_corner_arc,
            dimension_label_point(lower_corner_arc.startSketchPoint),
        ).value = mm_to_internal_length(max(2, bit.diameter_mm / 2))

        upper_half_width_line = sketch_lines.addByTwoPoints(
            lower_corner_arc.startSketchPoint,
            adsk.core.Point3D.create(
                lower_corner_arc.endSketchPoint.geometry.x + 1,
                lower_corner_arc.endSketchPoint.geometry.y,
                0,
            ),
        )
        sketch.geometricConstraints.addHorizontal(upper_half_width_line)
        sketch.geometricConstraints.addTangent(lower_corner_arc, upper_half_width_line)
        dimensions.addOffsetDimension(
            outer_vertical_line,
            upper_half_width_line.endSketchPoint,
            dimension_label_point(upper_half_width_line.startSketchPoint),
        ).value = mm_to_internal_length(bit.slot_width_mm / 2)
        dimensions.addOffsetDimension(
            upper_half_width_line,
            lower_half_width_line,
            dimension_label_point(upper_half_width_line.startSketchPoint),
        ).value = mm_to_internal_length(bit.required_depth_mm)

        inner_vertical_line = sketch_lines.addByTwoPoints(
            outer_vertical_line.endSketchPoint,
            adsk.core.Point3D.create(
                outer_vertical_line.endSketchPoint.geometry.x,
                outer_vertical_line.endSketchPoint.geometry.y + 1,
                0,
            ),
        )
        sketch.geometricConstraints.addVertical(inner_vertical_line)
        dimensions.addOffsetDimension(
            upper_half_width_line,
            inner_vertical_line.endSketchPoint,
            dimension_label_point(inner_vertical_line.startSketchPoint),
        ).value = mm_to_internal_length(self.gridfinity_bin.DEPRESSION_EXTRA_DEPTH_MM)

        top_half_width_line = sketch_lines.addByTwoPoints(
            inner_vertical_line.endSketchPoint,
            adsk.core.Point3D.create(
                inner_vertical_line.endSketchPoint.geometry.x + 1,
                inner_vertical_line.endSketchPoint.geometry.y,
                0,
            ),
        )
        sketch.geometricConstraints.addHorizontal(top_half_width_line)
        sketch.geometricConstraints.addVerticalPoints(
            top_half_width_line.endSketchPoint, upper_half_width_line.endSketchPoint
        )

        centre_line = sketch_lines.addByTwoPoints(
            top_half_width_line.endSketchPoint, lower_half_width_line.endSketchPoint
        )
        centre_line.isConstruction = True

        sketch.mirror(
            [
                lower_half_width_line,
                outer_vertical_line,
                upper_half_width_line,
                inner_vertical_line,
                top_half_width_line,
                lower_corner_arc,
            ],
            centre_line,
        )

    def create_sketches(self, target_component: adsk.fusion.Component):
        front_plane = target_component.xZConstructionPlane
        sketches = target_component.sketches

        self.slot_sketches.clear()
        left_offset = mm_to_internal_length(self.gridfinity_bin.CLEARANCE_MM)
        for idx, bit in enumerate(self.gridfinity_bin.drill_bits):
            sketch = self.create_bin_sketch(sketches, front_plane, left_offset, bit)
            self.slot_sketches.append((bit, sketch))
            left_offset += mm_to_internal_length(
                bit.slot_width_mm + self.gridfinity_bin.slot_gap_mm
            )

    def create_extrusions(
        self, target_body: adsk.fusion.BRepBody, target_component: adsk.fusion.Component
    ):
        long_profiles_by_length: dict[float, list[adsk.fusion.Profile]] = {}
        depression_profiles: list[adsk.fusion.Profile] = []

        for idx, (bit, sketch) in enumerate(self.slot_sketches):
            profiles = sketch.profiles
            
            if profiles.count == 0:
                raise RuntimeError(
                    f"Slot sketch for {bit.diameter_mm:g} mm has no closed profiles."
                )
            top_profile = max(
                (profiles.item(i) for i in range(profiles.count)),
                key=lambda profile: profile.areaProperties().centroid.z,
            )

            for i in range(profiles.count):
                profile = profiles.item(i)
                if profile == top_profile:
                    long_profiles_by_length.setdefault(
                        bit.required_length_mm, []
                    ).append(profile)
                else:
                    depression_profiles.append(profile)

        # Fusion accepts an ObjectCollection of coplanar profiles. Grouping
        # identical slot lengths avoids creating one cut feature per bit.
        for required_length_mm, profiles in long_profiles_by_length.items():
            cut_feature = extrude_cut_operation(
                target_component,
                self._profiles_input(profiles),
                required_length_mm,
                self.SLOT_CUT_START_OFFSET_MM,
            )
            top_face = get_top_face(target_body)
            apply_chamfer_from_cutfeature(
                cut_feature,
                target_component,
                top_face,
                self.gridfinity_bin.CHAMFER_SIZE_MM,
            )

        if depression_profiles:
            extrude_cut_operation(
                target_component,
                self._profiles_input(depression_profiles),
                self.gridfinity_bin.DEPRESSION_LENGTH_MM,
                self.SLOT_CUT_START_OFFSET_MM,
            )

    @staticmethod
    def _profiles_input(profiles: list[adsk.fusion.Profile]):
        """Return the Fusion profile input for one or many coplanar profiles."""
        if not profiles:
            raise ValueError("At least one profile is required for an extrusion.")
        if len(profiles) == 1:
            return profiles[0]

        collection = adsk.core.ObjectCollection.create()
        for profile in profiles:
            collection.add(profile)
        return collection

    def _group_timeline_features(self, start_index: int | None) -> None:
        """Group generated features without failing otherwise valid geometry."""
        if start_index is None:
            return

        try:
            timeline = self.design.timeline
            end_index = timeline.count - 1
            if end_index < start_index:
                return
            group = timeline.timelineGroups.add(start_index, end_index)
            if group is None:
                futil.log("Unable to create the drill-holder timeline group")
                return
            group.name = "Drill bit holder features"
        except RuntimeError as error:
            # Timeline grouping is presentation-only and should never discard
            # successfully generated geometry (for example in direct modelling).
            futil.log(f"Unable to group drill-holder timeline features: {error}")

    def create_text_profiles(
        self, target_body: adsk.fusion.BRepBody, target_component: adsk.fusion.Component
    ) -> adsk.fusion.ConstructionPlane:
        top_face = get_top_face(target_body)
        if top_face is None:
            raise RuntimeError("Unable to find a top face for the embossed labels.")

        label_plane = self._create_label_plane(target_component, top_face)
        sketches = target_component.sketches

        text_sketch = sketches.add(label_plane)
        if text_sketch is None:
            raise RuntimeError("Failed to create the label sketch.")
        text_sketch.name = "Drill-size labels"

        text_sketch.isComputeDeferred = True
        try:
            sketch_texts = self._populate_text_sketch(text_sketch)
        finally:
            text_sketch.isComputeDeferred = False

        require_healthy_entity(text_sketch, "Drill-size label sketch")

        emboss_features = target_component.features.embossFeatures

        emboss_input = emboss_features.createInput(
            sketch_texts,
            [top_face],
            adsk.core.ValueInput.createByReal(
                mm_to_internal_length(self.gridfinity_bin.LABEL_DEPTH_MM)
            ),
        )

        if not emboss_input:
            raise RuntimeError("Failed to create emboss input")

        emboss_feature = emboss_features.add(emboss_input)

        require_healthy_entity(emboss_feature, "Drill-size label emboss")
        return label_plane

    @staticmethod
    def _create_label_plane(
        target_component: adsk.fusion.Component,
        top_face: adsk.fusion.BRepFace,
    ) -> adsk.fusion.ConstructionPlane:
        """Create the common support for the label sketch and optional split."""
        construction_planes = target_component.constructionPlanes
        plane_input = construction_planes.createInput()
        if plane_input is None:
            raise RuntimeError("Failed to create label-plane input.")
        if not plane_input.setByOffset(
            top_face,
            adsk.core.ValueInput.createByReal(0),
        ):
            raise RuntimeError("Failed to define the label plane.")

        label_plane = construction_planes.add(plane_input)
        if label_plane is None:
            raise RuntimeError("Failed to create the label plane.")
        label_plane.name = "Label and multi-colour split plane"
        label_plane.isLightBulbOn = False
        return label_plane

    def split_body_for_multicolor(
        self,
        target_body: adsk.fusion.BRepBody,
        target_component: adsk.fusion.Component,
        label_plane: adsk.fusion.ConstructionPlane,
    ) -> adsk.fusion.SplitBodyFeature:
        """Separate raised labels from the holder for multi-colour printing."""
        split_features = target_component.features.splitBodyFeatures
        split_input = split_features.createInput(target_body, label_plane, True)
        if split_input is None:
            raise RuntimeError("Failed to create the multi-colour split input.")

        split_feature = split_features.add(split_input)
        require_healthy_entity(split_feature, "Multi-colour body split")
        split_feature.name = "Separate labels for multi-colour printing"

        result_bodies = [
            split_feature.bodies.item(index)
            for index in range(split_feature.bodies.count)
        ]
        if len(result_bodies) < 2:
            raise RuntimeError(
                "The label plane did not split the holder into separate bodies."
            )

        holder_body = max(result_bodies, key=lambda body: body.volume)
        holder_body.name = "Holder"
        label_bodies = sorted(
            (body for body in result_bodies if body != holder_body),
            key=self._body_sort_key,
        )
        for index, label_body in enumerate(label_bodies, start=1):
            suffix = "" if len(label_bodies) == 1 else f" - part {index}"
            label_body.name = f"Labels{suffix}"

        return split_feature

    @staticmethod
    def _body_sort_key(body: adsk.fusion.BRepBody) -> tuple[float, float, float]:
        """Return a stable browser ordering for split label bodies."""
        bounds = body.boundingBox
        return (
            bounds.minPoint.x,
            bounds.minPoint.y,
            bounds.minPoint.z,
        )

    def _populate_text_sketch(
        self, text_sketch: adsk.fusion.Sketch
    ) -> list[adsk.fusion.SketchText]:
        """Add positioned drill-size labels while sketch compute is deferred."""
        sketch_texts = []
        left_offset = mm_to_internal_length(self.gridfinity_bin.CLEARANCE_MM)
        for bit in self.gridfinity_bin.drill_bits:
            text_input = text_sketch.sketchTexts.createInput3(
                # Fusion text expressions require literal text in single quotes.
                f"'{bit.diameter_mm:.1f}'",
                adsk.core.ValueInput.createByString(
                    f"{self.gridfinity_bin.LABEL_FONT_HEIGHT_MM:g} mm"
                ),
            )
            if text_input is None:
                raise RuntimeError(
                    f"Failed to create text input for {bit.diameter_mm:g} mm."
                )
            corner1 = adsk.core.Point3D.create(
                left_offset + mm_to_internal_length(self.gridfinity_bin.slot_gap_mm),
                mm_to_internal_length(
                    bit.required_length_mm
                    + self.SLOT_CUT_START_OFFSET_MM
                    + self.gridfinity_bin.CHAMFER_SIZE_MM
                ),
                0,
            )

            corner2 = adsk.core.Point3D.create(
                corner1.x + mm_to_internal_length(bit.slot_width_mm),
                corner1.y
                + mm_to_internal_length(self.gridfinity_bin.LABEL_AREA_HEIGHT_MM),
                0,
            )

            if not text_input.setAsMultiLine(
                corner1,
                corner2,
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.TopVerticalAlignment,
                0,
            ):
                raise RuntimeError(
                    f"Failed to position text for {bit.diameter_mm:g} mm."
                )
            sketch_text = text_sketch.sketchTexts.add(text_input)
            if not sketch_text:
                raise RuntimeError(
                    f"Failed to create sketch text for {bit.diameter_mm}"
                )

            sketch_texts.append(sketch_text)

            left_offset += mm_to_internal_length(
                self.gridfinity_bin.slot_gap_mm + bit.slot_width_mm
            )
        return sketch_texts

    def create_drill_slots(
        self,
        target_component: adsk.fusion.Component,
        target_body: adsk.fusion.BRepBody,
    ) -> None:
        if target_component is None or not target_component.isValid:
            raise RuntimeError("The generated bin component is unavailable.")
        if target_body is None or not target_body.isValid:
            raise RuntimeError("The generated bin body is unavailable.")

        timeline = getattr(self.design, "timeline", None)
        timeline_start_index = timeline.count if timeline is not None else None

        self.reduce_inner_bin_height(target_body, target_component)

        self.create_sketches(target_component)

        self.create_extrusions(target_body, target_component)

        label_plane = self.create_text_profiles(target_body, target_component)

        if self.gridfinity_bin.split_for_multicolor:
            self.split_body_for_multicolor(
                target_body,
                target_component,
                label_plane,
            )

        self._group_timeline_features(timeline_start_index)

        futil.log("Finished creating Gridfinity drill holder")
