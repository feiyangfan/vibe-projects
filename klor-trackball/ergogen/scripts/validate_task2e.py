#!/usr/bin/env python3
"""
Task 2E: put the correctly handed Type-C housing, 25 mm sphere, generated PCB,
stock Konrad switchplate, and stock Konrad right case in one 3D frame.

The script writes relieved plate/case STLs, a GLB assembly scene, and a JSON
qualification report. It intentionally fails if the real housing/ball still
intersects the PCB or relieved stock parts.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
import trimesh
import yaml
from shapely.geometry import LineString, MultiLineString, Point, MultiPoint, box
from shapely.ops import polygonize, unary_union
from shapely.affinity import translate as shp_translate

ERGOGEN = Path(__file__).resolve().parents[1]
KLOR = ERGOGEN.parent
CONTRACT = ERGOGEN / "task2" / "task2e-mechanical.yaml"
CONFIG = ERGOGEN / "config.yaml"

HOUSING = KLOR / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_left.stl"
SWITCHPLATE = KLOR / "klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl"
RIGHT_CASE = KLOR / "klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl"
STOCK_PCB = KLOR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"

# Source-validated Task-2B stock KiCad -> switchplate-native XY transform.
R_KP = np.array(
    [
        [0.999999991, 0.000131877],
        [0.000131877, -0.999999991],
    ],
    dtype=float,
)
T_KP = np.array([-80.655587, 153.995244], dtype=float)

EPS = 1e-6
INTERSECTION_VOLUME_TOL = 0.01


def balanced_blocks(text: str, token: str) -> list[str]:
    out: list[str] = []
    needle = "(" + token
    pos = 0
    while True:
        start = text.find(needle, pos)
        if start < 0:
            return out
        depth = 0
        quoted = False
        escaped = False
        end = None
        for i in range(start, len(text)):
            ch = text[i]
            if quoted:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    quoted = False
                continue
            if ch == '"':
                quoted = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            raise AssertionError(f"unterminated {token} block")
        out.append(text[start:end])
        pos = end


def stock_footprint_origin(text: str, ref: str) -> tuple[float, float, float]:
    for fp in balanced_blocks(text, "footprint") + balanced_blocks(text, "module"):
        rm = re.search(r'\(property "Reference" "([^"]+)"', fp)
        if not rm:
            rm = re.search(r'\(fp_text reference\s+"?([^"\s\)]+)"?', fp)
        if not rm or rm.group(1) != ref:
            continue
        at = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", fp)
        if not at:
            raise AssertionError(f"{ref}: footprint has no at()")
        return float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    raise AssertionError(f"stock footprint {ref} not found")


def local_from_source_kicad(x: np.ndarray, y: np.ndarray, origin: tuple[float, float, float]):
    return x - origin[0], origin[1] - y


def transform_switchplate_to_canonical(mesh: trimesh.Trimesh, origin):
    v = mesh.vertices.copy()
    q = v[:, :2] - T_KP
    # Inverse of orthonormal R_KP is its transpose.
    k = q @ R_KP
    cx, cy = local_from_source_kicad(k[:, 0], k[:, 1], origin)
    v[:, 0] = cx
    v[:, 1] = cy
    v[:, 2] -= v[:, 2].min()
    out = trimesh.Trimesh(vertices=v, faces=mesh.faces.copy(), process=True)
    return out


def transform_case_to_canonical(mesh: trimesh.Trimesh, origin, plate_top_z: float):
    v = mesh.vertices.copy()
    cx, cy = local_from_source_kicad(v[:, 0], v[:, 1], origin)
    v[:, 0] = cx
    v[:, 1] = cy
    # Align the stock case top with the stock switchplate top.
    v[:, 2] += plate_top_z - v[:, 2].max()
    return trimesh.Trimesh(vertices=v, faces=mesh.faces.copy(), process=True)


def circle_from_three(p1, p2, p3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return None
    ux = (
        (x1 * x1 + y1 * y1) * (y2 - y3)
        + (x2 * x2 + y2 * y2) * (y3 - y1)
        + (x3 * x3 + y3 * y3) * (y1 - y2)
    ) / d
    uy = (
        (x1 * x1 + y1 * y1) * (x3 - x2)
        + (x2 * x2 + y2 * y2) * (x1 - x3)
        + (x3 * x3 + y3 * y3) * (x2 - x1)
    ) / d
    return ux, uy, math.hypot(x1 - ux, y1 - uy)


def arc_points(start, mid, end, count=48):
    c = circle_from_three(start, mid, end)
    if c is None:
        return [start, end]
    cx, cy, r = c

    def angle(p):
        return math.atan2(p[1] - cy, p[0] - cx)

    a1, am, a2 = angle(start), angle(mid), angle(end)
    tw = 2 * math.pi
    ccw_total = (a2 - a1 + tw) % tw
    ccw_mid = (am - a1 + tw) % tw
    if ccw_mid <= ccw_total + 1e-9:
        angles = [a1 + ccw_total * i / (count - 1) for i in range(count)]
    else:
        cw_total = (a1 - a2 + tw) % tw
        angles = [a1 - cw_total * i / (count - 1) for i in range(count)]
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]


def kicad_edge_segments(text: str):
    segs: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for b in balanced_blocks(text, "gr_line"):
        if "Edge.Cuts" not in b:
            continue
        s = re.search(r"\(start\s+([-\d.]+)\s+([-\d.]+)\)", b)
        e = re.search(r"\(end\s+([-\d.]+)\s+([-\d.]+)\)", b)
        if s and e:
            # Generated Ergogen KiCad frame is canonical X with Y reflected.
            segs.append(
                (
                    (float(s.group(1)), -float(s.group(2))),
                    (float(e.group(1)), -float(e.group(2))),
                )
            )

    for b in balanced_blocks(text, "gr_arc"):
        if "Edge.Cuts" not in b:
            continue
        s = re.search(r"\(start\s+([-\d.]+)\s+([-\d.]+)\)", b)
        m = re.search(r"\(mid\s+([-\d.]+)\s+([-\d.]+)\)", b)
        e = re.search(r"\(end\s+([-\d.]+)\s+([-\d.]+)\)", b)
        if s and m and e:
            pts = arc_points(
                (float(s.group(1)), -float(s.group(2))),
                (float(m.group(1)), -float(m.group(2))),
                (float(e.group(1)), -float(e.group(2))),
            )
            segs.extend(zip(pts[:-1], pts[1:]))

    # Edge cuts can also be emitted inside footprints.
    for fp in balanced_blocks(text, "footprint") + balanced_blocks(text, "module"):
        at = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", fp)
        if not at:
            continue
        ox, oy, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        a = math.radians(rot)
        co, si = math.cos(a), math.sin(a)

        def tf(x, y):
            kx = ox + x * co - y * si
            ky = oy + x * si + y * co
            return kx, -ky

        for b in balanced_blocks(fp, "fp_line"):
            if "Edge.Cuts" not in b:
                continue
            s = re.search(r"\(start\s+([-\d.]+)\s+([-\d.]+)\)", b)
            e = re.search(r"\(end\s+([-\d.]+)\s+([-\d.]+)\)", b)
            if s and e:
                segs.append((tf(float(s.group(1)), float(s.group(2))),
                             tf(float(e.group(1)), float(e.group(2)))))

    if not segs:
        raise AssertionError("no generated PCB Edge.Cuts found")
    return segs


def board_polygon_from_kicad(text: str):
    # Ergogen/KiCad emits some source-Bezier joins with a few microns of
    # endpoint noise. Snap only the temporary 3D reconstruction to 0.01 mm;
    # the production PCB itself remains untouched and is separately validated.
    snapped = []
    for a, b in kicad_edge_segments(text):
        aa = (round(a[0], 2), round(a[1], 2))
        bb = (round(b[0], 2), round(b[1], 2))
        if aa != bb:
            snapped.append(LineString([aa, bb]))
    polys = list(polygonize(unary_union(snapped)))
    if not polys:
        raise AssertionError("generated PCB Edge.Cuts did not polygonize after 0.01 mm construction snap")
    outer = max(polys, key=lambda p: p.area)
    board = outer
    for p in sorted(polys, key=lambda q: q.area, reverse=True):
        if p.equals(outer):
            continue
        if outer.contains(p.representative_point()):
            board = board.difference(p)
    if board.is_empty:
        raise AssertionError("generated PCB solid is empty")
    return board


def extrude_board(poly, bottom_z: float, thickness: float):
    mesh = trimesh.creation.extrude_polygon(poly, height=thickness, engine="earcut")
    mesh.apply_translation([0, 0, bottom_z])
    return mesh


def mesh_volume(mesh) -> float:
    if mesh is None:
        return 0.0
    if isinstance(mesh, trimesh.Scene):
        vals = [abs(g.volume) for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        return float(sum(vals))
    if isinstance(mesh, (list, tuple)):
        return float(sum(abs(m.volume) for m in mesh if m is not None))
    return float(abs(mesh.volume))


def intersection_volume(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    inter = trimesh.boolean.intersection([a, b], engine="manifold", check_volume=False)
    return mesh_volume(inter)


def intersection_mesh(a: trimesh.Trimesh, b: trimesh.Trimesh):
    return trimesh.boolean.intersection([a, b], engine="manifold", check_volume=False)


def section_keepout(mesh: trimesh.Trimesh, z_values, buffer_xy: float):
    polys = []
    for z in z_values:
        section = mesh.section(
            plane_origin=[0.0, 0.0, float(z)],
            plane_normal=[0.0, 0.0, 1.0],
        )
        if section is None or len(section.vertices) < 3:
            continue
        pts = [tuple(map(float, p[:2])) for p in section.vertices]
        from shapely.geometry import MultiPoint
        hull = MultiPoint(pts).convex_hull
        if not hull.is_empty:
            polys.append(hull.buffer(buffer_xy))
    if not polys:
        return None
    from shapely.ops import unary_union as _uu
    return _uu(polys)


def subtract(base: trimesh.Trimesh, cutter: trimesh.Trimesh) -> trimesh.Trimesh:
    out = trimesh.boolean.difference([base, cutter], engine="manifold", check_volume=False)
    if out is None:
        return base.copy()
    if isinstance(out, trimesh.Scene):
        meshes = [g for g in out.geometry.values() if isinstance(g, trimesh.Trimesh)]
        return trimesh.util.concatenate(meshes)
    return out


def union_meshes(meshes) -> trimesh.Trimesh:
    out = trimesh.boolean.union(meshes, engine="manifold", check_volume=False)
    if out is None:
        raise AssertionError("mesh union failed")
    if isinstance(out, trimesh.Scene):
        parts = [g for g in out.geometry.values() if isinstance(g, trimesh.Trimesh)]
        return trimesh.util.concatenate(parts)
    return out


def translated_housing(base: trimesh.Trimesh, ball_xyz, scale_xyz=None):
    mesh = base.copy()
    if scale_xyz is not None:
        mat = np.eye(4)
        mat[0, 0], mat[1, 1], mat[2, 2] = scale_xyz
        mesh.apply_transform(mat)
    mesh.apply_translation(ball_xyz)
    return mesh


def support_fraction(mesh: trimesh.Trimesh, xy, z, radius: float, samples=24):
    pts = []
    for i in range(samples):
        a = 2 * math.pi * i / samples
        pts.append([xy[0] + radius * math.cos(a), xy[1] + radius * math.sin(a), z])
    inside = mesh.contains(np.array(pts))
    return float(np.count_nonzero(inside)) / samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("generated", type=Path)
    ap.add_argument("--output", type=Path, default=ERGOGEN / "task2e-output")
    args = ap.parse_args()

    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)

    board_file = args.generated / "pcbs/task3d_right_production.kicad_pcb"
    if not board_file.exists():
        raise AssertionError(f"missing generated Rev-3 PCB: {board_file}")

    stock_text = STOCK_PCB.read_text(encoding="utf-8")
    origin = stock_footprint_origin(stock_text, "SW13")

    plate_native = trimesh.load_mesh(SWITCHPLATE, process=True)
    case_native = trimesh.load_mesh(RIGHT_CASE, process=True)
    housing_local = trimesh.load_mesh(HOUSING, process=True)

    if not all(isinstance(m, trimesh.Trimesh) for m in [plate_native, case_native, housing_local]):
        raise AssertionError("one or more source STLs did not load as a single mesh")

    # Revision 5 handedness regression guard. For the right keyboard half we
    # intentionally use the source asset named "left": this mirrored housing
    # puts the ball-access opening toward the thumb cluster (-X) and the
    # connector/service side toward the outside edge (+X).
    expected_x = contract["handedness"]["expected_housing_local_x_bounds"]
    actual_x = [float(housing_local.bounds[0, 0]), float(housing_local.bounds[1, 0])]
    if not np.allclose(actual_x, expected_x, atol=0.03):
        raise AssertionError(
            f"wrong Type-C housing handedness/source: X bounds {actual_x}, "
            f"expected {expected_x}"
        )

    plate = transform_switchplate_to_canonical(plate_native, origin)
    plate_bottom = float(contract["z_stack"]["switchplate_bottom_z"])
    plate.apply_translation([0, 0, plate_bottom - plate.bounds[0, 2]])
    plate_top = float(plate.bounds[1, 2])

    case = transform_case_to_canonical(case_native, origin, plate_top)

    board_poly = board_polygon_from_kicad(board_file.read_text(encoding="utf-8"))
    pcb_top = plate_top - float(contract["z_stack"]["plate_top_to_pcb_top"])
    pcb_thickness = float(contract["z_stack"]["pcb_thickness"])
    pcb = extrude_board(board_poly, pcb_top - pcb_thickness, pcb_thickness)

    ball_x, ball_y = map(float, contract["trackball"]["ball_xy"])
    radius = float(contract["trackball"]["ball_diameter"]) / 2
    min_clearance = float(contract["trackball"]["minimum_pcb_clearance"])

    ball_pt = Point(ball_x, ball_y)
    dxy = float(ball_pt.distance(board_poly))
    target_r = radius + min_clearance
    if dxy >= target_r:
        dz_required = 0.0
    else:
        dz_required = math.sqrt(max(0.0, target_r * target_r - dxy * dxy))

    ball_z = pcb_top + dz_required

    # The sphere-derived Z is the lowest mechanically useful candidate. Measure
    # the real housing there before changing Z: if it intersects PCB material,
    # that is a PCB-relief defect rather than something to hide by lifting the
    # whole trackball assembly.
    housing = translated_housing(housing_local, [ball_x, ball_y, ball_z])
    housing_intersection = intersection_mesh(housing, pcb)
    housing_pcb_volume = mesh_volume(housing_intersection)

    pcb_slice_keepout = section_keepout(
        housing,
        [pcb_top - pcb_thickness, pcb_top - pcb_thickness / 2.0, pcb_top],
        float(contract["clearance"]["housing_xy"]),
    )
    required_relief = (
        board_poly.intersection(pcb_slice_keepout)
        if pcb_slice_keepout is not None
        else None
    )

    z_scan = []
    for scan_z in np.arange(-12.0, 15.01, 1.0):
        scan_housing = translated_housing(
            housing_local, [ball_x, ball_y, float(scan_z)]
        )
        v = intersection_volume(scan_housing, pcb)
        z_scan.append(
            {
                "ball_z_mm": float(scan_z),
                "housing_vs_pcb_mm3": float(v),
                "ball_exposure_mm": float(scan_z + radius - plate_top),
            }
        )
    z_scan_best = sorted(z_scan, key=lambda row: row["housing_vs_pcb_mm3"])[:8]
    print("TASK2E_Z_SCAN " + json.dumps(z_scan_best, sort_keys=True))

    # Search small nearby XY changes for a cavity derived from the real housing
    # section while preserving all retained keys and stock PCB holes.
    relative_section = (
        shp_translate(pcb_slice_keepout, xoff=-ball_x, yoff=-ball_y)
        if pcb_slice_keepout is not None
        else None
    )
    sphere_slice_r = 0.0
    nearest_z = min(
        [pcb_top - pcb_thickness, pcb_top],
        key=lambda z: abs(z - ball_z),
    )
    dz_sphere = abs(nearest_z - ball_z)
    sphere_keep_r = radius + float(contract["clearance"]["ball_radial"])
    if dz_sphere < sphere_keep_r:
        sphere_slice_r = math.sqrt(sphere_keep_r**2 - dz_sphere**2)
    relative_relief = (
        relative_section.union(Point(0.0, 0.0).buffer(sphere_slice_r))
        if relative_section is not None
        else Point(0.0, 0.0).buffer(sphere_slice_r)
    )

    housing_projection_rel = MultiPoint(
        [tuple(map(float, p[:2])) for p in housing_local.vertices]
    ).convex_hull.buffer(float(contract["clearance"]["housing_xy"]))

    retained_names = [*(f"sw{i}" for i in range(1, 18)), "sw20", "sw21"]
    key_keepouts = []
    for name in retained_names:
        sx, sy = map(float, cfg["points"]["zones"][name]["anchor"]["shift"])
        key_keepouts.append((name, box(sx - 9.5, sy - 9.5, sx + 9.5, sy + 9.5)))

    hole_keepouts = []
    for i in range(1, 10):
        hx, hy = map(float, cfg["points"]["zones"][f"mh{i}"]["anchor"]["shift"])
        hole_keepouts.append(
            (
                f"mh{i}",
                Point(hx, hy).buffer(
                    float(cfg["units"]["pcb_m3_hole"]) / 2.0 + 0.5
                ),
            )
        )

    candidates = []
    for dx in np.arange(-8.0, 4.01, 0.5):
        for dy in np.arange(-10.0, 0.01, 0.5):
            cx, cy = ball_x + float(dx), ball_y + float(dy)
            relief = shp_translate(relative_relief, xoff=cx, yoff=cy)
            housing_proj = shp_translate(housing_projection_rel, xoff=cx, yoff=cy)
            key_hits = [
                name for name, keep in key_keepouts
                if relief.intersects(keep) or housing_proj.intersects(keep)
            ]
            hole_hits = [name for name, keep in hole_keepouts if relief.intersects(keep)]
            if key_hits or hole_hits:
                continue
            nearest_key = min(
                math.hypot(
                    float(cfg["points"]["zones"][name]["anchor"]["shift"][0]) - cx,
                    float(cfg["points"]["zones"][name]["anchor"]["shift"][1]) - cy,
                )
                for name in retained_names
            )
            candidates.append(
                {
                    "ball_xy": [cx, cy],
                    "shift_xy": [float(dx), float(dy)],
                    "shift_norm": math.hypot(dx, dy),
                    "nearest_key_center_mm": nearest_key,
                    "relief_bounds": list(map(float, relief.bounds)),
                }
            )
    candidates.sort(key=lambda row: (row["shift_norm"], -row["nearest_key_center_mm"]))
    print("TASK2E_XY_CANDIDATES " + json.dumps(candidates[:12], sort_keys=True))

    if candidates:
        best = candidates[0]
        best_relief = shp_translate(
            relative_relief,
            xoff=best["ball_xy"][0],
            yoff=best["ball_xy"][1],
        )
        simplified = best_relief.simplify(0.35, preserve_topology=True)
        if simplified.geom_type == "Polygon":
            coords = [
                [float(x), float(y)]
                for x, y in list(simplified.exterior.coords)[:-1]
            ]
            rel_coords = [
                [x - best["ball_xy"][0], y - best["ball_xy"][1]]
                for x, y in coords
            ]
            print(
                "TASK2E_BEST_RELIEF "
                + json.dumps(
                    {
                        "ball_xy": best["ball_xy"],
                        "absolute_polygon": coords,
                        "ball_relative_polygon": rel_coords,
                    },
                    sort_keys=True,
                )
            )

    print(
        "TASK2E_DIAGNOSTIC "
        + json.dumps(
            {
                "sphere_derived_ball_z_mm": ball_z,
                "sphere_derived_exposure_mm": ball_z + radius - plate_top,
                "housing_vs_pcb_mm3": housing_pcb_volume,
                "housing_pcb_intersection_bounds_mm": (
                    housing_intersection.bounds.tolist()
                    if isinstance(housing_intersection, trimesh.Trimesh)
                    and not housing_intersection.is_empty
                    else None
                ),
                "required_xy_relief_area_mm2": (
                    float(required_relief.area)
                    if required_relief is not None and not required_relief.is_empty
                    else 0.0
                ),
                "required_xy_relief_bounds_mm": (
                    list(map(float, required_relief.bounds))
                    if required_relief is not None and not required_relief.is_empty
                    else None
                ),
            },
            sort_keys=True,
        )
    )

    if housing_pcb_volume > INTERSECTION_VOLUME_TOL:
        raise AssertionError(
            "actual Type-C housing intersects Rev-3 PCB at the sphere-derived "
            "installation height; PCB cavity must be revised from the measured "
            "Task-2E housing section"
        )

    sphere = trimesh.creation.icosphere(subdivisions=4, radius=radius)
    sphere.apply_translation([ball_x, ball_y, ball_z])

    sphere_pcb_volume = intersection_volume(sphere, pcb)
    if sphere_pcb_volume > INTERSECTION_VOLUME_TOL:
        raise AssertionError(f"25 mm sphere still intersects PCB: {sphere_pcb_volume} mm^3")

    # Build a manufacturing keepout by expanding the actual housing about the
    # ball-centered local origin. This is intentionally conservative.
    hxy = float(contract["clearance"]["housing_xy"])
    hz = float(contract["clearance"]["housing_z"])
    max_abs = np.max(np.abs(housing_local.vertices), axis=0)
    scale_xyz = (
        1.0 + hxy / max_abs[0],
        1.0 + hxy / max_abs[1],
        1.0 + hz / max_abs[2],
    )
    housing_keepout = translated_housing(
        housing_local, [ball_x, ball_y, ball_z], scale_xyz=scale_xyz
    )
    sphere_keepout = trimesh.creation.icosphere(
        subdivisions=4, radius=radius + float(contract["clearance"]["ball_radial"])
    )
    sphere_keepout.apply_translation([ball_x, ball_y, ball_z])

    # Subtract the authoritative housing first. The radially scaled copy is
    # an additional clearance shell, but for a concave mesh it is not
    # guaranteed to contain every original surface.
    relieved_plate = subtract(plate, housing)
    relieved_plate = subtract(relieved_plate, housing_keepout)
    relieved_plate = subtract(relieved_plate, sphere_keepout)

    # Revision 4 mounting: the required housing relief consumes the old
    # switchplate support around both native screw axes. Mount the housing from
    # below with a local case pod instead of pretending plate material remains.
    screw_mid_x = ball_x + float(contract["mounting"]["screw_midpoint_from_ball"][0])
    screw_mid_y = ball_y + float(contract["mounting"]["screw_midpoint_from_ball"][1])
    screw_r = float(contract["mounting"]["screw_hole_diameter"]) / 2
    screw_axes = [
        (screw_mid_x, screw_mid_y + float(dy))
        for dy in contract["mounting"]["screw_y_offsets"]
    ]

    # Start from a collision-free stock-case relief.
    relieved_case = subtract(case, housing)
    relieved_case = subtract(relieved_case, housing_keepout)
    relieved_case = subtract(relieved_case, sphere_keepout)

    # The usable ball height places the real housing below the stock case
    # bottom. Build a local downward pod from the real housing + sphere XY
    # projection, with a deliberate floor and overlap into the stock shell.
    wall = float(contract["case_pod"]["wall_thickness"])
    floor = float(contract["case_pod"]["floor_thickness"])
    overlap = float(contract["case_pod"]["overlap_into_stock_case"])

    housing_xy = MultiPoint(
        [tuple(map(float, p[:2])) for p in housing.vertices]
    ).convex_hull
    ball_xy_shape = Point(ball_x, ball_y).buffer(radius + float(contract["clearance"]["ball_radial"]))
    pod_outer_poly = unary_union([housing_xy, ball_xy_shape]).convex_hull.buffer(wall)

    inner_bottom = min(float(housing.bounds[0, 2]), float(sphere.bounds[0, 2]))
    pod_bottom = inner_bottom - floor
    pod_top = float(case.bounds[0, 2]) + overlap
    if pod_top <= pod_bottom:
        raise AssertionError("invalid case-pod Z span")

    pod = trimesh.creation.extrude_polygon(
        pod_outer_poly,
        height=pod_top - pod_bottom,
        engine="earcut",
    )
    pod.apply_translation([0.0, 0.0, pod_bottom])

    # Union the pod with the relieved stock case, then hollow it with the same
    # authoritative housing/sphere keepouts.
    relieved_case = union_meshes([relieved_case, pod])
    relieved_case = subtract(relieved_case, housing)
    relieved_case = subtract(relieved_case, housing_keepout)
    relieved_case = subtract(relieved_case, sphere_keepout)

    # Add two annular bosses from the pod floor to just below the flat housing
    # bottom. They intentionally contact the mounting interface rather than
    # obey the general housing-clearance shell.
    boss_outer = float(contract["mounting"]["boss_outer_radius"])
    boss_gap = float(contract["mounting"]["boss_contact_gap"])
    boss_top = float(housing.bounds[0, 2]) - boss_gap
    boss_bottom = pod_bottom
    if boss_top <= boss_bottom:
        raise AssertionError("housing mounting boss has no positive height")

    bosses = []
    for sx, sy in screw_axes:
        outer = trimesh.creation.cylinder(
            radius=boss_outer,
            height=boss_top - boss_bottom,
            sections=64,
        )
        outer.apply_translation([sx, sy, (boss_top + boss_bottom) / 2])
        bosses.append(outer)
    relieved_case = union_meshes([relieved_case, *bosses])

    # Drill the two M2 through-holes through pod floor/bosses.
    hole_height = pod_top - pod_bottom + 2.0
    for sx, sy in screw_axes:
        hole = trimesh.creation.cylinder(
            radius=screw_r,
            height=hole_height,
            sections=64,
        )
        hole.apply_translation([sx, sy, (pod_top + pod_bottom) / 2])
        relieved_case = subtract(relieved_case, hole)

    checks = {
        "sphere_vs_pcb_mm3": sphere_pcb_volume,
        "housing_vs_pcb_mm3": float(housing_pcb_volume),
        "housing_vs_relief_plate_mm3": intersection_volume(housing, relieved_plate),
        "sphere_vs_relief_plate_mm3": intersection_volume(sphere, relieved_plate),
        "housing_vs_relief_case_mm3": intersection_volume(housing, relieved_case),
        "sphere_vs_relief_case_mm3": intersection_volume(sphere, relieved_case),
    }
    bad = {k: v for k, v in checks.items() if v > INTERSECTION_VOLUME_TOL}
    if bad:
        raise AssertionError(f"residual 3D intersections remain: {bad}")

    # Verify the two case-pod mounting bosses actually retain annular material
    # around the M2 hole near their top contact plane.
    support_z = boss_top - min(0.25, (boss_top - boss_bottom) / 4)
    support_radius = float(contract["mounting"]["boss_support_check_radius"])
    support = [
        support_fraction(relieved_case, axis, support_z, support_radius)
        for axis in screw_axes
    ]
    if min(support) < 0.75:
        raise AssertionError(
            f"case-pod mounting boss support too small: fractions={support}"
        )

    case_components = relieved_case.split(only_watertight=False)
    if len(case_components) > 1:
        largest = max(abs(m.volume) for m in case_components)
        total = sum(abs(m.volume) for m in case_components)
        if total > EPS and largest / total < 0.98:
            raise AssertionError(
                f"relieved case/pod fragmented: {len(case_components)} components, "
                f"largest fraction={largest/total:.6f}"
            )

    components = relieved_plate.split(only_watertight=False)
    if len(components) > 1:
        largest = max(abs(m.volume) for m in components)
        total = sum(abs(m.volume) for m in components)
        if total > EPS and largest / total < 0.98:
            raise AssertionError(
                f"relieved switchplate fragmented: {len(components)} components, "
                f"largest fraction={largest/total:.6f}"
            )

    ball_exposure = ball_z + radius - plate_top

    # Quantify retained key reach in canonical XY.
    retained = []
    zones = cfg["points"]["zones"]
    for name in [*(f"sw{i}" for i in range(1, 18)), "sw20", "sw21"]:
        shift = zones[name]["anchor"]["shift"]
        retained.append(
            {
                "key": name,
                "center_distance_mm": math.hypot(
                    float(shift[0]) - ball_x, float(shift[1]) - ball_y
                ),
            }
        )
    retained.sort(key=lambda x: x["center_distance_mm"])

    # Visual scene.
    pcb.visual.face_colors = [50, 110, 65, 220]
    relieved_plate.visual.face_colors = [145, 145, 150, 180]
    relieved_case.visual.face_colors = [90, 90, 95, 120]
    housing.visual.face_colors = [60, 110, 190, 230]
    sphere.visual.face_colors = [210, 210, 215, 220]

    scene = trimesh.Scene()
    scene.add_geometry(relieved_case, geom_name="right_case_relief")
    scene.add_geometry(relieved_plate, geom_name="switchplate_relief")
    scene.add_geometry(pcb, geom_name="rev4_pcb")
    scene.add_geometry(housing, geom_name="type_c_housing")
    scene.add_geometry(sphere, geom_name="25mm_ball")

    plate_out = args.output / contract["outputs"]["relieved_switchplate"]
    case_out = args.output / contract["outputs"]["relieved_right_case"]
    scene_out = args.output / contract["outputs"]["assembly_scene"]
    json_out = args.output / contract["outputs"]["result_json"]

    relieved_plate.export(plate_out)
    relieved_case.export(case_out)
    scene.export(scene_out)

    result = {
        "status": "pass",
        "frame": {
            "origin_stock_ref": "SW13",
            "origin_source_kicad": list(origin),
            "plate_bottom_z_mm": plate_bottom,
            "plate_top_z_mm": plate_top,
            "case_top_z_mm": float(case.bounds[1, 2]),
            "pcb_top_z_mm": pcb_top,
            "pcb_bottom_z_mm": pcb_top - pcb_thickness,
        },
        "source_meshes": {
            "housing_watertight": bool(housing_local.is_watertight),
            "switchplate_watertight": bool(plate_native.is_watertight),
            "right_case_watertight": bool(case_native.is_watertight),
            "housing_local_bounds_mm": housing_local.bounds.tolist(),
            "switchplate_canonical_bounds_mm": plate.bounds.tolist(),
            "right_case_canonical_bounds_mm": case.bounds.tolist(),
        },
        "trackball": {
            "ball_center_xyz_mm": [ball_x, ball_y, ball_z],
            "ball_radius_mm": radius,
            "ball_exposure_above_plate_top_mm": ball_exposure,
            "pcb_xy_material_distance_from_ball_center_mm": dxy,
            "minimum_requested_pcb_clearance_mm": min_clearance,
            "housing_keepout_scale_xyz": list(scale_xyz),
        },
        "intersections_mm3": checks,
        "mounting": {
            "form": contract["mounting"]["form"],
            "screw_axes_xy_mm": [list(p) for p in screw_axes],
            "boss_outer_radius_mm": boss_outer,
            "boss_top_z_mm": boss_top,
            "boss_bottom_z_mm": boss_bottom,
            "support_radius_mm": support_radius,
            "support_fraction_at_radius": support,
        },
        "case_pod": {
            "stock_case_bottom_z_mm": float(case.bounds[0, 2]),
            "pod_bottom_z_mm": pod_bottom,
            "pod_top_z_mm": pod_top,
            "downward_extension_below_stock_case_mm": float(case.bounds[0, 2]) - pod_bottom,
            "wall_thickness_mm": wall,
            "floor_thickness_mm": floor,
        },
        "ergonomic_geometry": {
            "nearest_retained_keys": retained[:6],
            "note": "geometric access only; subjective comfort requires a physical mock-up",
        },
        "assumptions": {
            "pcb_top_z": contract["z_stack"]["pcb_top_source_status"],
            "plate_top_to_pcb_top_mm": float(contract["z_stack"]["plate_top_to_pcb_top"]),
            "case_z_alignment": "source case top aligned to switchplate top",
        },
        "outputs": {
            "relieved_switchplate": str(plate_out),
            "relieved_right_case": str(case_out),
            "assembly_scene": str(scene_out),
        },
    }
    json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2))
    print("PASS Task 2E common-frame 3D mechanical integration")


if __name__ == "__main__":
    main()
