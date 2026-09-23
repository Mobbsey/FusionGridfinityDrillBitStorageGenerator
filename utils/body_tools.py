"""Defensive helpers around commonly used Fusion body operations."""

from __future__ import annotations

import adsk.core
import adsk.fusion

from .fusion import mm_to_internal_length, require_healthy_entity
from .geometry import require_positive_finite


def apply_chamfer_from_cutfeature(
    cut_feature: adsk.fusion.ExtrudeFeature,
    component: adsk.fusion.Component,
    top_face: adsk.fusion.BRepFace,
    distance_mm: float,
) -> adsk.fusion.ChamferFeature:
    """Chamfer top-face edges that border faces made by a cut feature."""
    if cut_feature is None or component is None or top_face is None:
        raise ValueError("A cut feature, component, and top face are required.")
    require_positive_finite(distance_mm, "Chamfer distance")

    chamfer_edges = adsk.core.ObjectCollection.create()
    for edge in top_face.edges:
        for index in range(edge.faces.count):
            adjacent_face = edge.faces.item(index)
            if adjacent_face != top_face and face_is_from_feature(
                adjacent_face, cut_feature
            ):
                chamfer_edges.add(edge)
                break

    if chamfer_edges.count == 0:
        raise RuntimeError("No cut edges were found for the drill-slot chamfer.")

    chamfer_input = component.features.chamferFeatures.createInput2()
    if chamfer_input is None:
        raise RuntimeError("Failed to create chamfer input.")
    chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        chamfer_edges,
        adsk.core.ValueInput.createByReal(mm_to_internal_length(distance_mm)),
        False,
    )
    chamfer = component.features.chamferFeatures.add(chamfer_input)
    if chamfer is None:
        raise RuntimeError("Failed to create drill-slot chamfer.")
    require_healthy_entity(chamfer, "Drill-slot chamfer")
    return chamfer


def face_is_from_feature(face, feature) -> bool:
    """Return whether a face belongs to a feature's result faces."""
    return any(
        feature.faces.item(index) == face for index in range(feature.faces.count)
    )


def get_face_normal(face):
    """Return the face normal at a representative point, when available."""
    success, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
    return normal if success else None


def get_top_face(
    body: adsk.fusion.BRepBody,
    *,
    normal_tolerance: float = 0.999,
) -> adsk.fusion.BRepFace | None:
    """Return the largest planar face whose normal points upward."""
    if body is None:
        return None

    candidates = []
    for face in body.faces:
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        normal = get_face_normal(face)
        if normal and normal.z > normal_tolerance:
            candidates.append(face)
    return max(candidates, key=lambda face: face.area) if candidates else None


def extrude_cut_operation(
    component: adsk.fusion.Component,
    profile_input: adsk.fusion.Profile | adsk.core.ObjectCollection,
    distance_mm: float,
    offset_mm: float = 0.0,
) -> adsk.fusion.ExtrudeFeature:
    """Create a one-sided cut using millimetre domain dimensions."""
    if component is None or profile_input is None:
        raise ValueError("A component and profile are required for an extrude cut.")
    if distance_mm == 0:
        raise ValueError("Extrude distance must be non-zero.")

    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(
        profile_input,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )
    if extrude_input is None:
        raise RuntimeError("Failed to create extrude-cut input.")

    distance = adsk.core.ValueInput.createByReal(mm_to_internal_length(distance_mm))
    distance_extent = adsk.fusion.DistanceExtentDefinition.create(distance)
    if distance_extent is None:
        raise RuntimeError("Failed to create extrude distance extent.")

    if offset_mm != 0:
        extrude_input.startExtent = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByReal(mm_to_internal_length(offset_mm))
        )
    extrude_input.setOneSideExtent(
        distance_extent,
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
        None,
    )
    feature = extrudes.add(extrude_input)
    if feature is None:
        raise RuntimeError("Failed to create extrude cut.")
    require_healthy_entity(feature, "Extrude cut")
    return feature
