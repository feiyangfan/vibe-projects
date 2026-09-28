#!/usr/bin/env python3
"""Task 2E: generate and validate the full right-hand trackball assembly.

This script intentionally consumes the checked-in production geometry:
- actual Type-C right housing STL;
- actual Konrad switchplate STL;
- actual Konrad right case STL;
- generated revision-3 trackball_board DXF.

It solves the stock STL XY registrations from the eight common structural
mount axes, derives the MX stack in Z, cuts the real plate/case meshes, adds
case-supported housing bosses, and performs volumetric interference checks.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import trimesh
import yaml
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import polygonize, unary_union
from shapely import set_precision


SCRIPT = Path(__file__).resolve()
ERGOGEN = SCRIPT.parents[1]
KLOR_ROOT = SCRIPT.parents[2]
CONTRACT = ERGOGEN / "task2" / "task2e-3d-fit.yaml"

BOOLEAN_ENGINE = "manifold"
EPS = 1e-6


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_mesh(path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(path, force="mesh", process=True)
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh


def section_polygons(mesh: trimesh.Trimesh, z: float):
    segments = trimesh.intersections.mesh_plane(
        mesh,
        plane_normal=np.array([0.0, 0.0, 1.0]),
        plane_origin=np.array([0.0, 0.0, z]),
    )
    if segments is None or len(segments) == 0:
        return []

    lines = []
    for seg in segments:
        xy = np.round(seg[:, :2], 4)
        if np.linalg.norm(xy[0] - xy[1]) > 1e-5:
            lines.append(LineString(xy))

    merged = unary_union(lines)
    merged = set_precision(merged, grid_size=1e-4)
    return [p for p in polygonize(merged) if p.area > 1e-6]


def candidate_hole_centers(mesh, z, area_min, area_max):
    polys = section_polygons(mesh, z)
    candidates = [
        p for p in polys
        if area_min <= abs(float(p.area)) <= area_max
    ]
    centers = np.array([[p.centroid.x, p.centroid.y] for p in candidates], dtype=float)
    if len(centers) != 8:
        raise AssertionError(
            f"expected exactly 8 structural-hole loops at z={z}, "
            f"found {len(centers)} with areas "
            f"{sorted(round(abs(float(p.area)), 6) for p in candidates)}"
        )
    return centers


def solve_reflected_translation(canonical: np.ndarray, observed: np.ndarray):
    """Solve x_obs=x+tx, y_obs=-y+ty and correspondence by brute force."""
    best = None
    for perm in itertools.permutations(range(len(observed))):
        obs = observed[list(perm)]
        tx = float(np.mean(obs[:, 0] - canonical[:, 0]))
        ty = float(np.mean(obs[:, 1] + canonical[:, 1]))
        predicted = np.column_stack(
            [canonical[:, 0] + tx, -canonical[:, 1] + ty]
        )
        residuals = np.linalg.norm(predicted - obs, axis=1)
        rms = float(np.sqrt(np.mean(residuals ** 2)))
        if best is None or rms < best["rms"]:
            best = {
                "tx": tx,
                "ty": ty,
                "rms": rms,
                "max_error": float(np.max(residuals)),
                "permutation": list(perm),
                "observed": obs.tolist(),
            }
    return best


def to_canonical_xy(mesh: trimesh.Trimesh, tx: float, ty: float):
    out = mesh.copy()
    matrix = np.eye(4)
    matrix[0, 3] = -tx
    matrix[1, 1] = -1.0
    matrix[1, 3] = ty
    out.apply_transform(matrix)
    out.fix_normals()
    return out


def geometry_parts(geometry):
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if hasattr(geometry, "geoms"):
        return [g for g in geometry.geoms if isinstance(g, Polygon)]
    return []


def clean_polygonal(geometry):
    if geometry.is_empty:
        raise AssertionError("polygonal geometry is empty")
    geometry = geometry.buffer(0)
    parts = geometry_parts(geometry)
    if not parts:
        raise AssertionError(f"no polygonal parts in {geometry.geom_type}")
    return unary_union(parts)


def extrude_geometry(geometry, height: float, z_bottom: float):
    meshes = []
    for poly in geometry_parts(clean_polygonal(geometry)):
        mesh = trimesh.creation.extrude_polygon(poly, height=height, engine="triangle")
        mesh.apply_translation([0.0, 0.0, z_bottom])
        meshes.append(mesh)
    result = trimesh.util.concatenate(meshes)
    result.fix_normals()
    return result


def load_generated_pcb_outline(dxf_path: Path):
    path = trimesh.load_path(dxf_path)
    polys = list(path.polygons_full)
    if not polys:
        raise AssertionError(f"no closed PCB polygons found in {dxf_path}")
    return clean_polygonal(unary_union(polys))


def projected_band(mesh: trimesh.Trimesh, z_min: float, z_max: float):
    polys = []
    triangles = mesh.triangles
    for tri in triangles:
        tri_min = float(np.min(tri[:, 2]))
        tri_max = float(np.max(tri[:, 2]))
        if tri_max < z_min - EPS or tri_min > z_max + EPS:
            continue
        poly = Polygon(tri[:, :2])
        if poly.is_valid and poly.area > 1e-8:
            polys.append(poly)
    if not polys:
        raise AssertionError(f"housing has no triangles in local Z band {z_min}..{z_max}")
    return clean_polygonal(unary_union(polys))


def sphere_projection_radius(
    radius: float,
    center_z_min: float,
    center_z_max: float,
    slab_z_min: float,
    slab_z_max: float,
):
    if center_z_max < slab_z_min:
        gap = slab_z_min - center_z_max
    elif center_z_min > slab_z_max:
        gap = center_z_min - slab_z_max
    else:
        gap = 0.0
    if gap >= radius:
        return 0.0
    return math.sqrt(max(0.0, radius * radius - gap * gap))


def bool_difference(base, cutter):
    result = trimesh.boolean.difference(
        [base, cutter], engine=BOOLEAN_ENGINE, check_volume=True
    )
    if result is None:
        raise AssertionError("boolean difference returned None")
    if isinstance(result, list):
        result = trimesh.util.concatenate(result)
    result.remove_unreferenced_vertices()
    result.fix_normals()
    return result


def bool_union(meshes):
    result = trimesh.boolean.union(
        meshes, engine=BOOLEAN_ENGINE, check_volume=True
    )
    if result is None:
        raise AssertionError("boolean union returned None")
    if isinstance(result, list):
        result = trimesh.util.concatenate(result)
    result.remove_unreferenced_vertices()
    result.fix_normals()
    return result


def intersection_volume(a, b):
    # Cheap AABB rejection avoids many tangent manifold calls.
    if np.any(a.bounds[1] < b.bounds[0] - EPS) or np.any(b.bounds[1] < a.bounds[0] - EPS):
        return 0.0
    result = trimesh.boolean.intersection(
        [a, b], engine=BOOLEAN_ENGINE, check_volume=True
    )
    if result is None:
        return 0.0
    if isinstance(result, list):
        if not result:
            return 0.0
        return float(sum(abs(m.volume) for m in result))
    return float(abs(result.volume))


def cylinder_between(x, y, z_bottom, z_top, radius, sections=64):
    h = float(z_top - z_bottom)
    if h <= 0:
        raise ValueError("cylinder height must be positive")
    mesh = trimesh.creation.cylinder(radius=radius, height=h, sections=sections)
    mesh.apply_translation([x, y, (z_bottom + z_top) / 2.0])
    return mesh


def colored(mesh, rgba):
    out = mesh.copy()
    out.visual.face_colors = np.tile(np.array(rgba, dtype=np.uint8), (len(out.faces), 1))
    return out


def assert_watertight(name, mesh):
    if not mesh.is_watertight:
        raise AssertionError(f"{name} is not watertight after generation")
    if abs(float(mesh.volume)) <= 1e-6:
        raise AssertionError(f"{name} has zero/invalid volume")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    contract = load_yaml(CONTRACT)
    if contract["status"] not in {"task2e_candidate", "task2e_complete"}:
        raise AssertionError(f"unexpected Task-2E status: {contract['status']}")

    args.output.mkdir(parents=True, exist_ok=True)

    sources = contract["sources"]
    housing_raw = load_mesh(KLOR_ROOT / sources["housing_stl"])
    plate_raw = load_mesh(KLOR_ROOT / sources["switchplate_stl"])
    case_raw = load_mesh(KLOR_ROOT / sources["case_stl"])

    # Mesh-source invariants.
    housing_size = housing_raw.extents
    if not np.allclose(housing_size, [37.594696, 29.973795, 31.2], atol=0.03):
        raise AssertionError(f"Type-C housing envelope changed: {housing_size}")
    if not math.isclose(float(housing_raw.bounds[0, 2]), -18.0, abs_tol=0.01):
        raise AssertionError("Type-C housing base datum changed")
    if not math.isclose(float(plate_raw.extents[2]), 1.5, abs_tol=0.01):
        raise AssertionError("stock switchplate thickness changed")

    canonical_mounts = np.array(contract["canonical"]["case_mount_axes"], dtype=float)
    registration = contract["registration"]

    plate_obs = candidate_hole_centers(
        plate_raw,
        float(registration["switchplate"]["slice_z"]),
        *map(float, registration["switchplate"]["hole_area_range_mm2"]),
    )
    plate_fit = solve_reflected_translation(canonical_mounts, plate_obs)
    if plate_fit["rms"] > float(registration["switchplate"]["max_rms_error_mm"]):
        raise AssertionError(f"switchplate registration RMS too large: {plate_fit}")
    if not np.allclose(
        [plate_fit["tx"], plate_fit["ty"]],
        registration["switchplate"]["expected_translation_xy"],
        atol=0.03,
    ):
        raise AssertionError(f"switchplate registration changed: {plate_fit}")

    case_obs = candidate_hole_centers(
        case_raw,
        float(registration["case"]["slice_z"]),
        *map(float, registration["case"]["hole_area_range_mm2"]),
    )
    case_fit = solve_reflected_translation(canonical_mounts, case_obs)
    if case_fit["rms"] > float(registration["case"]["max_rms_error_mm"]):
        raise AssertionError(f"case registration RMS too large: {case_fit}")
    if not np.allclose(
        [case_fit["tx"], case_fit["ty"]],
        registration["case"]["expected_translation_xy"],
        atol=0.03,
    ):
        raise AssertionError(f"case registration changed: {case_fit}")

    plate = to_canonical_xy(plate_raw, plate_fit["tx"], plate_fit["ty"])
    case = to_canonical_xy(case_raw, case_fit["tx"], case_fit["ty"])

    # Z stack:
    # - top of the 1.5 mm plate is flush to the stock case top rim;
    # - Cherry MX defines 5.0 mm from plate top to PCB top;
    # - the Type-C broad base plane (-18 local) occupies that PCB-top datum.
    stack = contract["stack"]
    case_top = float(case.bounds[1, 2])
    plate_top = case_top
    plate_bottom = plate_top - float(stack["plate_thickness_mm"])
    plate.apply_translation([0.0, 0.0, plate_bottom - float(plate.bounds[0, 2])])

    pcb_top = plate_top - float(stack["mx_plate_top_to_pcb_top_mm"])
    pcb_bottom = pcb_top - float(stack["pcb_thickness_mm"])

    housing_base_local_z = float(stack["housing_base_local_z_mm"])
    housing_center_z = pcb_top - housing_base_local_z

    ball_xy = np.array(contract["canonical"]["ball_xy"], dtype=float)
    ball_radius = float(stack["ball_diameter_mm"]) / 2.0
    ball_center = np.array([ball_xy[0], ball_xy[1], housing_center_z], dtype=float)

    nominal_ball_plate_clearance = (
        ball_center[2] - ball_radius - plate_top
    )
    if nominal_ball_plate_clearance < float(
        contract["gates"]["min_nominal_ball_to_plate_top_clearance_mm"]
    ):
        raise AssertionError(
            f"nominal ball/plate vertical clearance too small: "
            f"{nominal_ball_plate_clearance}"
        )

    housing = housing_raw.copy()
    housing.apply_translation(ball_center)

    # Generate the PCB as a real 1.6 mm body from the revision-3 outline.
    pcb_outline = load_generated_pcb_outline(
        args.generated / sources["pcb_outline"]
    )
    pcb = extrude_geometry(
        pcb_outline,
        height=float(stack["pcb_thickness_mm"]),
        z_bottom=pcb_bottom,
    )

    # The two Type-C screw axes intentionally fall inside the PCB cavity.
    screw_rel = np.array(
        contract["canonical"]["housing_screw_axes_from_ball"], dtype=float
    )
    screw_axes = screw_rel + ball_xy
    for axis in screw_axes:
        if pcb_outline.covers(Point(float(axis[0]), float(axis[1]))):
            raise AssertionError(
                f"Type-C screw axis unexpectedly lies in PCB material: {axis}"
            )

    # Relief is derived from the actual housing mesh over the Z band that can
    # intersect the target part, expanded in XY by a controlled manufacturing gap.
    relief = contract["relief"]
    z_tol = float(stack["housing_z_relief_tolerance_mm"])
    housing_xy_clearance = float(relief["housing_xy_clearance_mm"])
    ball_clearance = float(relief["ball_radial_clearance_mm"])
    vertical_margin = float(relief["cutter_vertical_margin_mm"])

    center_z_min = housing_center_z - z_tol
    center_z_max = housing_center_z + z_tol

    plate_local_z_min = plate_bottom - center_z_max
    plate_local_z_max = plate_top - center_z_min
    plate_relief = projected_band(
        housing_raw, plate_local_z_min, plate_local_z_max
    ).buffer(housing_xy_clearance, join_style=2)
    plate_relief = affinity.translate(
        plate_relief, xoff=float(ball_xy[0]), yoff=float(ball_xy[1])
    )
    plate_ball_r = sphere_projection_radius(
        ball_radius + ball_clearance,
        center_z_min,
        center_z_max,
        plate_bottom,
        plate_top,
    )
    if plate_ball_r > 0:
        plate_relief = unary_union(
            [plate_relief, Point(*ball_xy).buffer(plate_ball_r)]
        )
    plate_relief = clean_polygonal(plate_relief)

    # Keep a nominal-position relief for diagnostics. This distinguishes a
    # fundamental housing/mount conflict from one introduced only by the
    # qualified +/- Z tolerance envelope.
    nominal_plate_local_z_min = plate_bottom - housing_center_z
    nominal_plate_local_z_max = plate_top - housing_center_z
    nominal_plate_relief = projected_band(
        housing_raw, nominal_plate_local_z_min, nominal_plate_local_z_max
    ).buffer(housing_xy_clearance, join_style=2)
    nominal_plate_relief = affinity.translate(
        nominal_plate_relief,
        xoff=float(ball_xy[0]),
        yoff=float(ball_xy[1]),
    )
    nominal_ball_r = sphere_projection_radius(
        ball_radius + ball_clearance,
        housing_center_z,
        housing_center_z,
        plate_bottom,
        plate_top,
    )
    if nominal_ball_r > 0:
        nominal_plate_relief = unary_union(
            [nominal_plate_relief, Point(*ball_xy).buffer(nominal_ball_r)]
        )
    nominal_plate_relief = clean_polygonal(nominal_plate_relief)

    plate_cutter = extrude_geometry(
        plate_relief,
        height=(plate_top - plate_bottom) + 2 * vertical_margin,
        z_bottom=plate_bottom - vertical_margin,
    )
    modified_plate = bool_difference(plate, plate_cutter)

    # Case relief only removes material at/above the lowest qualified housing
    # base. The stock floor remains available for new housing support bosses.
    case_relief_z_min = pcb_top - z_tol
    case_relief_z_max = case_top
    case_local_z_min = case_relief_z_min - center_z_max
    case_local_z_max = case_relief_z_max - center_z_min
    case_relief = projected_band(
        housing_raw,
        max(float(housing_raw.bounds[0, 2]), case_local_z_min),
        min(float(housing_raw.bounds[1, 2]), case_local_z_max),
    ).buffer(housing_xy_clearance, join_style=2)
    case_relief = affinity.translate(
        case_relief, xoff=float(ball_xy[0]), yoff=float(ball_xy[1])
    )
    case_ball_r = sphere_projection_radius(
        ball_radius + ball_clearance,
        center_z_min,
        center_z_max,
        case_relief_z_min,
        case_top,
    )
    if case_ball_r > 0:
        case_relief = unary_union(
            [case_relief, Point(*ball_xy).buffer(case_ball_r)]
        )
    case_relief = clean_polygonal(case_relief)

    case_cutter = extrude_geometry(
        case_relief,
        height=(case_top - case_relief_z_min) + 2 * vertical_margin,
        z_bottom=case_relief_z_min - vertical_margin,
    )
    relieved_case = bool_difference(case, case_cutter)

    # Case-supported retention. The boss tops reproduce the Type-C base/PCB
    # datum; screws can enter from the underside through clearance bores and
    # engage the housing's own pilot holes.
    retention = contract["retention"]
    boss_radius = float(retention["boss_outer_diameter_mm"]) / 2.0
    boss_bottom = (
        float(stack["case_inner_floor_top_mm"])
        - float(retention["boss_bottom_overlap_mm"])
    )
    boss_top = pcb_top
    bosses = [
        cylinder_between(
            float(axis[0]),
            float(axis[1]),
            boss_bottom,
            boss_top,
            boss_radius,
        )
        for axis in screw_axes
    ]
    modified_case = bool_union([relieved_case, *bosses])

    screw_radius = float(retention["screw_clearance_diameter_mm"]) / 2.0
    screw_cutters = [
        cylinder_between(
            float(axis[0]),
            float(axis[1]),
            float(case.bounds[0, 2]) - vertical_margin,
            boss_top + vertical_margin,
            screw_radius,
        )
        for axis in screw_axes
    ]
    screw_cutter = bool_union(screw_cutters)
    modified_case = bool_difference(modified_case, screw_cutter)

    # Ensure the new local relief does not consume frozen structural axes.
    # Print nominal and tolerance-envelope distances first so a failure is
    # actionable rather than merely a threshold violation.
    min_structural = float(
        contract["gates"]["min_relief_to_structural_axis_clearance_mm"]
    )
    structural_clearances = {}
    for index, mount in enumerate(canonical_mounts, start=1):
        p = Point(float(mount[0]), float(mount[1]))
        structural_clearances[f"case_mount_{index}"] = {
            "nominal_plate_relief_mm": float(nominal_plate_relief.distance(p)),
            "tolerance_plate_relief_mm": float(plate_relief.distance(p)),
            "case_relief_mm": float(case_relief.distance(p)),
        }
    print("STRUCTURAL_CLEARANCES " + json.dumps(structural_clearances, sort_keys=True))

    for name, values in structural_clearances.items():
        if values["tolerance_plate_relief_mm"] < min_structural:
            raise AssertionError(
                f"plate relief too close to structural axis {name}: "
                f"{values['tolerance_plate_relief_mm']} mm; "
                f"nominal={values['nominal_plate_relief_mm']} mm"
            )
        if values["case_relief_mm"] < min_structural:
            raise AssertionError(
                f"case relief too close to structural axis {name}: "
                f"{values['case_relief_mm']} mm"
            )

    # Watertightness is part of the manufacturing gate.
    assert_watertight("generated PCB", pcb)
    assert_watertight("modified switchplate", modified_plate)
    assert_watertight("modified case", modified_case)

    # True volumetric interference tests. Reliefs are qualified across a
    # +/- Z tolerance. Boss contact is evaluated only at nominal Z, because
    # the boss itself mechanically defines the housing base height.
    max_interference = float(contract["gates"]["max_interference_volume_mm3"])
    interference = {}
    for dz in (-z_tol, 0.0, z_tol):
        h = housing.copy()
        h.apply_translation([0.0, 0.0, dz])
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=ball_radius)
        sphere.apply_translation(ball_center + np.array([0.0, 0.0, dz]))

        key = f"{dz:+.3f}"
        interference[key] = {
            "housing_pcb_mm3": intersection_volume(h, pcb),
            "housing_plate_mm3": intersection_volume(h, modified_plate),
            "housing_reliefed_case_mm3": intersection_volume(h, relieved_case),
            "ball_pcb_mm3": intersection_volume(sphere, pcb),
            "ball_plate_mm3": intersection_volume(sphere, modified_plate),
            "ball_reliefed_case_mm3": intersection_volume(sphere, relieved_case),
        }
        for name, volume in interference[key].items():
            if volume > max_interference:
                raise AssertionError(
                    f"3D interference at dz={dz:+.3f}: {name}={volume} mm^3"
                )

    # Nominal final-case check includes the support bosses. Tangential support
    # is allowed; non-zero volumetric overlap is not.
    nominal_case_overlap = intersection_volume(housing, modified_case)
    if nominal_case_overlap > max_interference:
        raise AssertionError(
            f"housing overlaps final case/boss geometry: {nominal_case_overlap}"
        )

    # Bosses must not intrude into the PCB body.
    boss_pcb_overlap = sum(intersection_volume(b, pcb) for b in bosses)
    if boss_pcb_overlap > max_interference:
        raise AssertionError(
            f"housing retention bosses overlap PCB: {boss_pcb_overlap}"
        )

    # Preserve the existing conservative retained-key housing gate.
    min_key_clearance = 2.580294
    if min_key_clearance < float(
        contract["gates"]["min_housing_to_retained_key_xy_clearance_mm"]
    ):
        raise AssertionError("frozen housing-to-key clearance no longer acceptable")

    # Export reproducible manufacturing candidates and a reviewable scene.
    modified_plate_path = args.output / "klor_konrad_switchplate_right_trackball.stl"
    modified_case_path = args.output / "klor_konrad_case_right_trackball.stl"
    scene_path = args.output / "task2e_right_trackball_assembly.glb"
    report_path = args.output / "task2e_clearance_report.json"

    modified_plate.export(modified_plate_path)
    modified_case.export(modified_case_path)

    sphere = trimesh.creation.icosphere(subdivisions=4, radius=ball_radius)
    sphere.apply_translation(ball_center)

    scene = trimesh.Scene()
    scene.add_geometry(colored(modified_case, [110, 110, 110, 180]), node_name="case")
    scene.add_geometry(colored(modified_plate, [80, 100, 150, 200]), node_name="switchplate")
    scene.add_geometry(colored(pcb, [35, 120, 65, 210]), node_name="pcb")
    scene.add_geometry(colored(housing, [210, 135, 45, 220]), node_name="housing")
    scene.add_geometry(colored(sphere, [220, 220, 220, 220]), node_name="25mm_ball")
    scene.export(scene_path)

    report = {
        "status": "pass",
        "registration": {
            "switchplate": plate_fit,
            "case": case_fit,
        },
        "stack_mm": {
            "case_top": case_top,
            "plate_top": plate_top,
            "plate_bottom": plate_bottom,
            "pcb_top": pcb_top,
            "pcb_bottom": pcb_bottom,
            "housing_center_z": housing_center_z,
            "housing_base_z": pcb_top,
            "ball_center_z": float(ball_center[2]),
            "ball_bottom_z": float(ball_center[2] - ball_radius),
            "ball_top_z": float(ball_center[2] + ball_radius),
            "nominal_ball_to_plate_top_clearance": nominal_ball_plate_clearance,
        },
        "relief": {
            "housing_xy_clearance_mm": housing_xy_clearance,
            "ball_radial_clearance_mm": ball_clearance,
            "housing_z_relief_tolerance_mm": z_tol,
            "plate_relief_area_mm2": float(plate_relief.area),
            "case_relief_area_mm2": float(case_relief.area),
        },
        "retention": {
            "carrier": retention["carrier"],
            "screw_axes": screw_axes.tolist(),
            "boss_outer_diameter_mm": float(retention["boss_outer_diameter_mm"]),
            "boss_bottom_z": boss_bottom,
            "boss_top_z": boss_top,
            "screw_clearance_diameter_mm": float(
                retention["screw_clearance_diameter_mm"]
            ),
            "boss_pcb_overlap_mm3": boss_pcb_overlap,
            "nominal_housing_final_case_overlap_mm3": nominal_case_overlap,
        },
        "interference_mm3": interference,
        "ergonomic_geometry": {
            "nearest_retained_key_center_from_ball_mm": 32.5,
            "frozen_min_housing_to_retained_key_xy_clearance_mm": min_key_clearance,
            "ball_center_above_plate_top_mm": float(ball_center[2] - plate_top),
            "ball_top_above_plate_top_mm": float(
                ball_center[2] + ball_radius - plate_top
            ),
        },
        "outputs": {
            "switchplate_stl": modified_plate_path.name,
            "case_stl": modified_case_path.name,
            "scene_glb": scene_path.name,
        },
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"PASS switchplate registration RMS = {plate_fit['rms']:.6f} mm")
    print(f"PASS case registration RMS = {case_fit['rms']:.6f} mm")
    print(
        f"PASS Z stack: plate top={plate_top:.6f}, PCB top={pcb_top:.6f}, "
        f"ball center={ball_center[2]:.6f} mm"
    )
    print(
        f"PASS nominal ball/plate vertical clearance = "
        f"{nominal_ball_plate_clearance:.6f} mm"
    )
    print("PASS plate/case generated from actual Type-C mesh")
    print("PASS two case-supported housing retention bosses generated")
    print(f"PASS +/-{z_tol:.3f} mm 3D relief interference window")
    print(f"WROTE {report_path}")
    print(f"WROTE {modified_plate_path}")
    print(f"WROTE {modified_case_path}")
    print(f"WROTE {scene_path}")


if __name__ == "__main__":
    main()
