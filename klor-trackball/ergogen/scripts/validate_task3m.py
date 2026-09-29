#!/usr/bin/env python3
"""Task 3M: build and validate the right-trackball mechanical stack in one 3D frame."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import trimesh
import yaml
from shapely import affinity
from shapely.geometry import MultiPoint, Point, box
from shapely.ops import unary_union


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
KLOR = HERE.parents[2]

HOUSING_STL = (
    KLOR
    / "Keyball 25mm Trackball Case Type C - 6719828/files/"
    "keyball_trackball_case_25mm_type_c_right.stl"
)
PLATE_STL = (
    KLOR
    / "klor1.4/case/3DP/konrad/switchplate/"
    "KLOR_konrad_3DP_switchplate.stl"
)
CASE_STL = KLOR / "klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl"

BALL_XY = np.array([16.5, -28.000147])
BALL_RADIUS = 12.5
BALL_WORLD_Z = 18.0
PCB_TOP_Z = 0.0
PCB_THICKNESS = 1.6
PLATE_TOP_Z = 5.0
PLATE_THICKNESS = 1.5
PLATE_BOTTOM_Z = PLATE_TOP_Z - PLATE_THICKNESS

# Source-derived switchplate registration.
PLATE_X_SHIFT = -59.42579979401374
PLATE_Y_INTERCEPT = 57.73375011440802

# The source housing flat mounting face is local z=-18.
HOUSING_MOUNT_Z = -18.0

PLATE_HOUSING_CLEARANCE = 0.75
CASE_HOUSING_CLEARANCE = 1.00
BALL_APERTURE_RADIUS = 13.25

INTERSECTION_VOLUME_TOL = 0.02
KEY_RELIEF_GAP_MIN = 0.50
AXIS_RELIEF_GAP_MIN = 0.50


def load_mesh(path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise AssertionError(f"{path}: expected one mesh")
    if mesh.is_empty:
        raise AssertionError(f"{path}: empty mesh")
    return mesh.copy()


def plate_transform() -> np.ndarray:
    # x_c = x_s + shift; y_c = -y_s + intercept.
    return np.array(
        [
            [1.0, 0.0, 0.0, PLATE_X_SHIFT],
            [0.0, -1.0, 0.0, PLATE_Y_INTERCEPT],
            [0.0, 0.0, 1.0, PLATE_BOTTOM_Z],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )


def transform_plate(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh.apply_transform(plate_transform())
    return mesh


def transform_case(mesh: trimesh.Trimesh, plate_source: trimesh.Trimesh) -> trimesh.Trimesh:
    # The stock case and plate were exported from the same CAD design but with
    # different XY origins. Align their source XY envelope centers first.
    plate_center = plate_source.bounds.mean(axis=0)
    case_center = mesh.bounds.mean(axis=0)
    local_xy = plate_center[:2] - case_center[:2]

    m = np.eye(4)
    m[0, 3] = local_xy[0]
    m[1, 3] = local_xy[1]
    mesh.apply_transform(m)

    # Apply the same canonical XY registration/mirror as the plate.
    xy = np.array(
        [
            [1.0, 0.0, 0.0, PLATE_X_SHIFT],
            [0.0, -1.0, 0.0, PLATE_Y_INTERCEPT],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    mesh.apply_transform(xy)

    # Stock case top rim is the plate-top plane.
    mesh.apply_translation([0.0, 0.0, PLATE_TOP_Z - mesh.bounds[1, 2]])
    return mesh


def transform_housing(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    # Local ball center is the housing STL origin. Put its z=-18 mounting face
    # on PCB top, therefore ball center becomes world z=+18.
    mesh.apply_translation([BALL_XY[0], BALL_XY[1], -HOUSING_MOUNT_Z])
    return mesh


def housing_profile(source_housing: trimesh.Trimesh, z0: float, z1: float):
    triangles = source_housing.triangles
    zmin = triangles[:, :, 2].min(axis=1)
    zmax = triangles[:, :, 2].max(axis=1)
    mask = (zmax >= z0) & (zmin <= z1)
    points = triangles[mask, :, :2].reshape(-1, 2)
    if len(points) < 3:
        raise AssertionError("housing profile band produced fewer than three points")
    return MultiPoint(points).convex_hull


def prism(poly, z0: float, z1: float) -> trimesh.Trimesh:
    if z1 <= z0:
        raise ValueError("invalid extrusion interval")
    mesh = trimesh.creation.extrude_polygon(poly, z1 - z0, engine="earcut")
    mesh.apply_translation([0.0, 0.0, z0])
    return mesh


def boolean_difference(mesh: trimesh.Trimesh, cutter: trimesh.Trimesh) -> trimesh.Trimesh:
    out = trimesh.boolean.difference(
        [mesh, cutter], engine="manifold", check_volume=False
    )
    if out is None:
        raise AssertionError("boolean difference returned no result")
    if isinstance(out, list):
        out = trimesh.util.concatenate(out)
    return out


def intersection_volume(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    out = trimesh.boolean.intersection(
        [a, b], engine="manifold", check_volume=False
    )
    if out is None:
        return 0.0
    if isinstance(out, list):
        return float(sum(abs(x.volume) for x in out))
    return float(abs(out.volume))


def generated_points(generated: Path):
    return yaml.safe_load((generated / "points/points.yaml").read_text(encoding="utf-8"))


def pxy(points, name):
    p = points[name]
    return (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))


def rotated_key_cutout(x, y, r):
    poly = box(-7.0, -7.0, 7.0, 7.0)
    poly = affinity.rotate(poly, r, origin=(0, 0), use_radians=False)
    return affinity.translate(poly, xoff=x, yoff=y)


def board_solid(generated: Path) -> trimesh.Trimesh:
    dxf = generated / "outlines/trackball_board.dxf"
    path = trimesh.load_path(dxf)
    polygons = list(path.polygons_full)
    if not polygons:
        raise AssertionError("trackball_board.dxf produced no closed polygons")
    board_poly = max(polygons, key=lambda p: p.area)
    board = prism(board_poly, -PCB_THICKNESS, PCB_TOP_Z)
    return board


def color(mesh, rgba):
    mesh = mesh.copy()
    mesh.visual.face_colors = np.tile(np.array(rgba, dtype=np.uint8), (len(mesh.faces), 1))
    return mesh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    points = generated_points(args.generated)

    source_housing = load_mesh(HOUSING_STL)
    source_plate = load_mesh(PLATE_STL)
    source_case = load_mesh(CASE_STL)

    # Source-model sanity checks.
    hs = source_housing.extents
    if np.linalg.norm(hs - np.array([37.594696, 29.973795, 31.199999])) > 0.05:
        raise AssertionError(f"Type-C housing source dimensions changed: {hs}")
    if abs(source_plate.extents[2] - 1.5) > 0.01:
        raise AssertionError(f"stock switchplate thickness changed: {source_plate.extents[2]}")
    if abs(source_housing.bounds[0, 2] - HOUSING_MOUNT_Z) > 0.01:
        raise AssertionError("housing mounting-face Z changed")

    housing = transform_housing(source_housing.copy())
    plate = transform_plate(source_plate.copy())
    case = transform_case(source_case.copy(), source_plate)
    pcb = board_solid(args.generated)
    ball = trimesh.creation.icosphere(subdivisions=4, radius=BALL_RADIUS)
    ball.apply_translation([BALL_XY[0], BALL_XY[1], BALL_WORLD_Z])

    # Lower housing profile at the physical plate/case stack.
    plate_local_z0 = PLATE_BOTTOM_Z - BALL_WORLD_Z
    plate_local_z1 = PLATE_TOP_Z - BALL_WORLD_Z
    profile = housing_profile(source_housing, plate_local_z0, plate_local_z1)
    profile = affinity.translate(profile, xoff=BALL_XY[0], yoff=BALL_XY[1])

    plate_relief = unary_union(
        [
            profile.buffer(PLATE_HOUSING_CLEARANCE),
            Point(*BALL_XY).buffer(BALL_APERTURE_RADIUS, resolution=96),
        ]
    )
    case_relief = unary_union(
        [
            profile.buffer(CASE_HOUSING_CLEARANCE),
            Point(*BALL_XY).buffer(BALL_APERTURE_RADIUS, resolution=96),
        ]
    )

    # Mechanical preservation gate: don't consume retained key apertures.
    retained = [f"sw{i}" for i in range(1, 18)] + ["sw20", "sw21"]
    key_gaps = {}
    for name in retained:
        x, y, r = pxy(points, name)
        cutout = rotated_key_cutout(x, y, r)
        gap = plate_relief.distance(cutout)
        if plate_relief.intersects(cutout) or gap < KEY_RELIEF_GAP_MIN:
            raise AssertionError(f"plate relief too close to retained {name}: {gap:.3f} mm")
        key_gaps[name] = gap

    axis_gaps = {}
    for name in [f"mh{i}" for i in range(1, 10)] + [f"case_mount_{i}" for i in range(1, 9)]:
        x, y, _ = pxy(points, name)
        axis = Point(x, y).buffer(1.0)
        gap = case_relief.distance(axis)
        if case_relief.intersects(axis) or gap < AXIS_RELIEF_GAP_MIN:
            raise AssertionError(f"case relief too close to structural axis {name}: {gap:.3f} mm")
        axis_gaps[name] = gap

    # Cut stock plate and case with actual mesh-derived relief.
    plate_cutter = prism(plate_relief, PLATE_BOTTOM_Z - 1.0, PLATE_TOP_Z + 1.0)
    case_cutter = prism(case_relief, -0.1, PLATE_TOP_Z + 1.0)
    cut_plate = boolean_difference(plate, plate_cutter)
    cut_case = boolean_difference(case, case_cutter)

    # Check the stock geometry really needed relief, then prove the cut parts fit.
    stock_plate_housing = intersection_volume(plate, housing)
    stock_case_housing = intersection_volume(case, housing)
    cut_plate_housing = intersection_volume(cut_plate, housing)
    cut_case_housing = intersection_volume(cut_case, housing)
    cut_plate_ball = intersection_volume(cut_plate, ball)
    cut_case_ball = intersection_volume(cut_case, ball)
    pcb_housing = intersection_volume(pcb, housing)
    pcb_ball = intersection_volume(pcb, ball)

    if stock_plate_housing <= INTERSECTION_VOLUME_TOL:
        raise AssertionError("stock plate unexpectedly does not intersect the Type-C housing")
    if stock_case_housing <= INTERSECTION_VOLUME_TOL:
        raise AssertionError("stock case unexpectedly does not intersect the Type-C housing")

    checks = {
        "cut_plate_vs_housing": cut_plate_housing,
        "cut_case_vs_housing": cut_case_housing,
        "cut_plate_vs_ball": cut_plate_ball,
        "cut_case_vs_ball": cut_case_ball,
        "pcb_vs_housing": pcb_housing,
        "pcb_vs_ball": pcb_ball,
    }
    for name, volume in checks.items():
        if volume > INTERSECTION_VOLUME_TOL:
            raise AssertionError(f"{name} collision volume {volume:.6f} mm^3")

    # Vertical stack sanity.
    ball_bottom = BALL_WORLD_Z - BALL_RADIUS
    nominal_ball_to_plate = ball_bottom - PLATE_TOP_Z
    if nominal_ball_to_plate < 0.49:
        raise AssertionError(f"ball/plate nominal Z clearance too small: {nominal_ball_to_plate}")

    # Export modified mechanical parts and one common-frame assembly.
    plate_out = args.output / "task3m_konrad_switchplate_right.stl"
    case_out = args.output / "task3m_konrad_case_right.stl"
    assembly_out = args.output / "task3m_common_frame.glb"
    report_out = args.output / "task3m_fit_report.json"

    cut_plate.export(plate_out)
    cut_case.export(case_out)

    scene = trimesh.Scene()
    scene.add_geometry(color(pcb, [40, 120, 55, 180]), node_name="pcb")
    scene.add_geometry(color(cut_plate, [90, 90, 95, 180]), node_name="switchplate")
    scene.add_geometry(color(cut_case, [70, 70, 75, 90]), node_name="case")
    scene.add_geometry(color(housing, [210, 135, 35, 210]), node_name="trackball_housing")
    scene.add_geometry(color(ball, [55, 95, 190, 230]), node_name="25mm_ball")
    scene.export(assembly_out)

    report = {
        "status": "pass",
        "frame": {
            "pcb_top_z_mm": PCB_TOP_Z,
            "plate_bottom_z_mm": PLATE_BOTTOM_Z,
            "plate_top_z_mm": PLATE_TOP_Z,
            "ball_center": [float(BALL_XY[0]), float(BALL_XY[1]), BALL_WORLD_Z],
            "ball_radius_mm": BALL_RADIUS,
            "housing_mount_face_world_z_mm": 0.0,
            "plate_stl_transform": {
                "x": "x_stl - 59.42579979401374",
                "y": "-y_stl + 57.73375011440802",
                "z": f"z_stl + {PLATE_BOTTOM_Z}",
            },
        },
        "clearance": {
            "nominal_ball_bottom_to_plate_top_mm": nominal_ball_to_plate,
            "ball_aperture_radial_margin_mm": BALL_APERTURE_RADIUS - BALL_RADIUS,
            "plate_housing_relief_mm": PLATE_HOUSING_CLEARANCE,
            "case_housing_relief_mm": CASE_HOUSING_CLEARANCE,
            "minimum_retained_key_to_plate_relief_mm": min(key_gaps.values()),
            "minimum_structural_axis_to_case_relief_mm": min(axis_gaps.values()),
        },
        "intersection_volume_mm3": {
            "stock_plate_vs_housing": stock_plate_housing,
            "stock_case_vs_housing": stock_case_housing,
            **checks,
        },
        "source_extents_mm": {
            "housing": source_housing.extents.tolist(),
            "switchplate": source_plate.extents.tolist(),
            "case": source_case.extents.tolist(),
        },
        "outputs": {
            "switchplate": plate_out.name,
            "case": case_out.name,
            "assembly": assembly_out.name,
        },
    }
    report_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"PASS common-frame Z stack: ball bottom {ball_bottom:.3f} mm, plate top {PLATE_TOP_Z:.3f} mm")
    print(f"PASS nominal ball/plate Z gap = {nominal_ball_to_plate:.3f} mm; full ball aperture removes rubbing risk")
    print(f"PASS stock plate housing collision volume = {stock_plate_housing:.3f} mm^3")
    print(f"PASS stock case housing collision volume = {stock_case_housing:.3f} mm^3")
    print("PASS modified plate/case, PCB and ball/housing collision volumes are below tolerance")
    print(f"PASS minimum retained-key relief gap = {min(key_gaps.values()):.3f} mm")
    print(f"PASS minimum structural-axis relief gap = {min(axis_gaps.values()):.3f} mm")
    print(f"WROTE {plate_out}")
    print(f"WROTE {case_out}")
    print(f"WROTE {assembly_out}")
    print(f"WROTE {report_out}")


if __name__ == "__main__":
    main()
