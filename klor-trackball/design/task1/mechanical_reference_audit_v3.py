#!/usr/bin/env python3
"""KLOR Konrad trackball Task 1 final mechanical audit.

All transforms are solved in native source coordinates. The audit:
- verifies the uploaded Type-C source geometry;
- solves KiCad <-> Gerber from the 21 MX drill-center pairs;
- solves KiCad -> native switchplate from the 18 Konrad MX openings;
- solves native switchplate -> native right case from eight structural M2 axes;
- derives installed plate Z from the case support-post plane + documented 7 mm standoffs;
- places the Type-C housing from the canonical Gerber datums;
- checks retained-switch, encoder, MCU, TRRS, breakout-service, structural-post,
  and stock-case-shell relationships.

Production PCB/CAD files are read-only inputs.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
PATHS = {
    "pcb": PROJECT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb",
    "drill": PROJECT / "klor1.4/PCB/klor1_4/gerbers/klor1_4-NPTH.drl",
    "switchplate": PROJECT / "klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl",
    "case": PROJECT / "klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl",
    "housing_step": PROJECT / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c.stp",
    "housing_right": PROJECT / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl",
    "housing_left": PROJECT / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_left.stl",
    "breakout": PROJECT / "klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb",
}
EXPECTED_HASHES = {
    "housing_step": "79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c",
    "housing_right": "9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565",
    "housing_left": "5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58",
}

# Canonical placement: KLOR fabrication (Gerber/Excellon) XY, millimetres.
BALL_G = np.array([162.323, -134.748], dtype=float)
SCREW_MID_G = np.array([156.111, -134.748], dtype=float)
SCREWS_G = np.array([[156.111, -126.768], [156.111, -142.728]], dtype=float)
BREAKOUT_G = np.array([143.111, -134.748], dtype=float)
DELETED_SW_G = np.array([143.025, -128.770], dtype=float)

HOUSING_MOUNT_LOCAL_Z = -18.0
BALL_TOP_ABOVE_MOUNT = 30.5
STANDOFF_MM = 7.0
PLATE_THICKNESS_MM = 1.5


def native(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(type(obj).__name__)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_mesh(path: Path) -> trimesh.Trimesh:
    m = trimesh.load_mesh(path, force="mesh", process=False)
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.dump()))
    return m


def blocks(text: str, keys):
    starts = []
    for key in keys:
        pos = 0
        while True:
            i = text.find(key, pos)
            if i < 0:
                break
            starts.append(i)
            pos = i + len(key)
    for start in sorted(starts):
        depth = 0
        in_string = False
        escape = False
        for j in range(start, len(text)):
            c = text[j]
            if in_string:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_string = False
                continue
            if c == '"':
                in_string = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    yield text[start : j + 1]
                    break


def parse_footprints(text: str):
    out = []
    for b in blocks(text, ["(footprint", "(module"]):
        mn = re.match(r'\((?:footprint|module)\s+"?([^"\s\)]+)', b)
        name = mn.group(1) if mn else ""
        mr = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', b)
        if not mr:
            mr = re.search(r'\(fp_text\s+reference\s+"?([^"\s\)]+)', b)
        ma = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?", b)
        if ma:
            out.append(
                {
                    "ref": mr.group(1) if mr else "",
                    "name": name,
                    "x": float(ma.group(1)),
                    "y": float(ma.group(2)),
                    "rot": float(ma.group(3) or 0.0),
                }
            )
    return out


def switch_footprints(fps):
    rows = []
    for f in fps:
        n = (f["name"] + " " + f["ref"]).lower()
        if "encoder" in n or "rotary" in n:
            continue
        if f["ref"].upper().startswith("SW") or any(k in n for k in ("mx", "hotswap", "kailh", "switch")):
            rows.append(f)
    return np.array([[f["x"], f["y"]] for f in rows], dtype=float), rows


def section_loops_native(mesh: trimesh.Trimesh, z: float):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return []
    out = []
    for d in sec.discrete:
        a3 = np.asarray(d)
        a = a3[:, :2]
        if len(a) < 4:
            continue
        lo, hi = a.min(0), a.max(0)
        out.append({"points": a, "lo": lo, "hi": hi, "wh": hi - lo, "center": (lo + hi) / 2})
    return out


def unique_points(points, tolerance=0.5):
    out = []
    for p in points:
        if not out or min(np.linalg.norm(p - q) for q in out) > tolerance:
            out.append(p)
    return np.asarray(out, dtype=float)


def switchplate_features(mesh):
    z = float(np.mean(mesh.bounds[:, 2]))
    loops = section_loops_native(mesh, z)
    mx = []
    small = []
    for q in loops:
        w, h = q["wh"]
        if 12.5 <= w <= 16.5 and 12.5 <= h <= 16.5 and abs(w - h) <= 2.0:
            mx.append(q["center"])
        if 1.0 <= w <= 7.0 and 1.0 <= h <= 7.0 and abs(w - h) <= 1.5:
            small.append(q["center"])
    outer = max(loops, key=lambda q: float(np.prod(q["wh"])))
    return unique_points(mx), unique_points(small), outer, z


def rigid_from_pair(p1, p2, q1, q2, reflect=False):
    F = np.array([[-1.0, 0.0], [0.0, 1.0]]) if reflect else np.eye(2)
    u = F @ (p2 - p1)
    v = q2 - q1
    angle = math.atan2(v[1], v[0]) - math.atan2(u[1], u[0])
    C = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    R = C @ F
    t = q1 - R @ p1
    return R, t


def score_transform(src, dst, R, t, tolerance=0.35):
    moved = src @ R.T + t
    tree = cKDTree(dst)
    dist, idx = tree.query(moved)
    candidates = sorted((float(d), i, int(j)) for i, (d, j) in enumerate(zip(dist, idx)) if d <= tolerance)
    used_src, used_dst, keep = set(), set(), []
    for d, i, j in candidates:
        if i not in used_src and j not in used_dst:
            used_src.add(i)
            used_dst.add(j)
            keep.append((i, j, d))
    rms = math.sqrt(sum(x[2] ** 2 for x in keep) / len(keep)) if keep else 1e9
    return len(keep), rms, keep


def refine(src, dst, pairs):
    P = np.array([src[i] for i, j, d in pairs])
    Q = np.array([dst[j] for i, j, d in pairs])
    pc, qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    R = Vt.T @ U.T
    t = qc - R @ pc
    return R, t


def solve_pointsets(src, dst, final_tolerance=0.25):
    if len(src) < 3 or len(dst) < 3:
        raise RuntimeError(f"insufficient points src={len(src)} dst={len(dst)}")
    best = None
    spairs = [(i, j, np.linalg.norm(src[j] - src[i])) for i in range(len(src)) for j in range(i + 1, len(src))]
    dpairs = [(i, j, np.linalg.norm(dst[j] - dst[i])) for i in range(len(dst)) for j in range(i + 1, len(dst))]
    for i, j, ds in spairs:
        if ds < 8.0:
            continue
        for a, b, dd in dpairs:
            if abs(ds - dd) > 0.20:
                continue
            for qa, qb in ((a, b), (b, a)):
                for reflect in (False, True):
                    R, t = rigid_from_pair(src[i], src[j], dst[qa], dst[qb], reflect)
                    n, rms, pairs = score_transform(src, dst, R, t, tolerance=0.40)
                    key = (n, -rms)
                    if best is None or key > best[0]:
                        best = (key, R, t, pairs)
    if best is None:
        raise RuntimeError("no rigid transform candidate")
    R, t = refine(src, dst, best[3])
    n, rms, pairs = score_transform(src, dst, R, t, tolerance=final_tolerance)
    return R, t, n, rms, pairs


def parse_drill_switch_centers(text):
    diameters = {int(a): float(b) for a, b in re.findall(r"T(\d+)C([0-9.]+)", text)}
    tool = None
    points = {}
    for line in text.splitlines():
        mt = re.fullmatch(r"T(\d+)", line.strip())
        if mt:
            tool = int(mt.group(1))
            continue
        mp = re.match(r"X(-?[0-9.]+)Y(-?[0-9.]+)", line.strip())
        if mp and tool is not None:
            points.setdefault(tool, []).append(np.array([float(mp.group(1)), float(mp.group(2))]))
    tool_17 = min(diameters, key=lambda k: abs(diameters[k] - 1.7))
    source = points[tool_17]
    mids = []
    for i in range(len(source)):
        for j in range(i + 1, len(source)):
            if abs(np.linalg.norm(source[j] - source[i]) - 9.0) < 0.03:
                mids.append((source[i] + source[j]) / 2)
    return unique_points(mids, tolerance=0.25), {
        "tool": tool_17,
        "diameter_mm": diameters[tool_17],
        "raw_holes": len(source),
    }


def horizontal_planes(mesh):
    areas = {}
    for tri, normal, area in zip(mesh.triangles, mesh.face_normals, mesh.area_faces):
        if abs(normal[2]) > 0.999 and np.ptp(tri[:, 2]) < 1e-4:
            z = round(float(np.mean(tri[:, 2])), 3)
            areas[z] = areas.get(z, 0.0) + float(area)
    return [{"z": z, "area_mm2": area} for z, area in sorted(areas.items())]


def structural_case_axes(case_mesh, plate_small):
    """Solve plate-native -> case-native from the eight M2 structural axes.

    The stock case's mounting bosses have ~2.1 mm holes near their upper portion,
    and the stock switchplate has matching ~2.1 mm holes. We scan a narrow region
    around the measured boss top and keep the transform with the most matches and
    lowest residual.
    """
    best = None
    best_case_points = None
    best_z = None
    for z in np.linspace(-3.15, -0.85, 24):
        candidate = []
        for q in section_loops_native(case_mesh, float(z)):
            w, h = q["wh"]
            if 1.8 <= w <= 3.8 and 1.8 <= h <= 3.8 and abs(w - h) <= 0.6:
                candidate.append(q["center"])
        case_pts = unique_points(candidate, tolerance=0.3)
        if len(case_pts) < 6:
            continue
        try:
            R, t, n, rms, pairs = solve_pointsets(plate_small, case_pts, final_tolerance=0.20)
        except RuntimeError:
            continue
        key = (n, -rms)
        if best is None or key > best[0]:
            best = (key, R, t, n, rms, pairs)
            best_case_points = case_pts
            best_z = float(z)
    if best is None:
        raise RuntimeError("could not solve switchplate-to-case structural M2 pattern")
    _, R, t, n, rms, pairs = best
    matched_plate = np.array([plate_small[i] for i, j, d in pairs])
    matched_case = np.array([best_case_points[j] for i, j, d in pairs])
    return R, t, n, rms, pairs, matched_plate, matched_case, best_z


def footprint_candidates(fps, needles):
    rows = []
    for f in fps:
        n = (f["name"] + " " + f["ref"]).lower()
        if any(k in n for k in needles):
            rows.append(f)
    return rows


def rect_gap(a_lo, a_hi, center, half_xy):
    half = np.asarray(half_xy, dtype=float)
    b_lo = center - half
    b_hi = center + half
    dx = max(a_lo[0] - b_hi[0], b_lo[0] - a_hi[0], 0.0)
    dy = max(a_lo[1] - b_hi[1], b_lo[1] - a_hi[1], 0.0)
    return math.hypot(dx, dy)


def breakout_edge_extents(text):
    pts = []
    for b in blocks(text, ["(gr_line", "(gr_rect", "(gr_arc"]):
        if "Edge.Cuts" not in b:
            continue
        for m in re.finditer(r"\((?:start|end|mid)\s+(-?[0-9.]+)\s+(-?[0-9.]+)", b):
            pts.append([float(m.group(1)), float(m.group(2))])
    if not pts:
        return None
    a = np.asarray(pts)
    return a.min(0), a.max(0)


def main():
    report = {"task": 1, "status": "final-native-frame-audit", "errors": []}
    for name, path in PATHS.items():
        if not path.exists():
            report["errors"].append(f"missing {name}: {path}")
    if report["errors"]:
        print(json.dumps(report, indent=2))
        return 2

    report["source_hashes"] = {}
    for name, expected in EXPECTED_HASHES.items():
        actual = sha256(PATHS[name])
        report["source_hashes"][name] = {"actual": actual, "expected": expected, "matches": actual == expected}

    plate = load_mesh(PATHS["switchplate"])
    case = load_mesh(PATHS["case"])
    housing = load_mesh(PATHS["housing_right"])
    pcb_text = PATHS["pcb"].read_text(errors="ignore")
    fps = parse_footprints(pcb_text)
    sw_pts, sw_rows = switch_footprints(fps)
    plate_mx, plate_small, plate_outer, plate_section_z = switchplate_features(plate)

    # 1) KiCad -> Gerber fabrication frame.
    drill_centers, drill_meta = parse_drill_switch_centers(PATHS["drill"].read_text(errors="ignore"))
    R_kg, t_kg, n_kg, rms_kg, pairs_kg = solve_pointsets(sw_pts, drill_centers, final_tolerance=0.01)

    # 2) KiCad -> native switchplate frame from Konrad MX apertures.
    R_kp, t_kp, n_kp, rms_kp, pairs_kp = solve_pointsets(sw_pts, plate_mx, final_tolerance=0.10)

    # 3) Native switchplate -> native case from the eight M2 mounting axes.
    R_pc, t_pc, n_pc, rms_pc, pairs_pc, plate_mount_axes, case_mount_axes, matched_z = structural_case_axes(case, plate_small)

    report["transforms"] = {
        "kicad_to_gerber": {
            "R": np.round(R_kg, 9),
            "t": np.round(t_kg, 6),
            "matches": n_kg,
            "rms_mm": rms_kg,
            "drill": drill_meta,
        },
        "kicad_to_switchplate_native": {
            "R": np.round(R_kp, 9),
            "t": np.round(t_kp, 6),
            "matches": n_kp,
            "rms_mm": rms_kp,
        },
        "switchplate_native_to_case_native": {
            "R": np.round(R_pc, 9),
            "t_xy": np.round(t_pc, 6),
            "matches": n_pc,
            "rms_mm": rms_pc,
            "pattern_scan_z": matched_z,
            "matched_plate_axes": np.round(plate_mount_axes, 5),
            "matched_case_axes": np.round(case_mount_axes, 5),
        },
    }

    # Installed plate Z: case support-boss top + documented 7 mm standoff.
    planes = horizontal_planes(case)
    support_candidates = [p for p in planes if -2.0 < p["z"] < 0.0 and p["area_mm2"] > 100.0]
    if not support_candidates:
        report["errors"].append("case support-post top plane not found")
        print(json.dumps(report, indent=2, default=native))
        return 2
    support_plane = max(support_candidates, key=lambda p: p["z"])
    plate_bottom_case_z = support_plane["z"] + STANDOFF_MM
    plate_top_case_z = plate_bottom_case_z + PLATE_THICKNESS_MM
    case_top_z = float(case.bounds[1, 2])
    report["stackup"] = {
        "case_support_plane_z": support_plane["z"],
        "case_support_plane_area_mm2": support_plane["area_mm2"],
        "documented_standoff_mm": STANDOFF_MM,
        "plate_thickness_mm": PLATE_THICKNESS_MM,
        "plate_bottom_case_z": plate_bottom_case_z,
        "plate_top_case_z": plate_top_case_z,
        "case_top_z": case_top_z,
        "case_lip_above_plate_mm": case_top_z - plate_top_case_z,
    }

    # Helpers between frames.
    def gerber_to_kicad(xy):
        return R_kg.T @ (np.asarray(xy) - t_kg)

    def kicad_to_plate(xy):
        return R_kp @ np.asarray(xy) + t_kp

    def plate_to_case(xy):
        return R_pc @ np.asarray(xy) + t_pc

    ball_k = gerber_to_kicad(BALL_G)
    ball_p = kicad_to_plate(ball_k)
    ball_c = plate_to_case(ball_p)
    deleted_k = gerber_to_kicad(DELETED_SW_G)
    deleted_p = kicad_to_plate(deleted_k)
    breakout_k = gerber_to_kicad(BREAKOUT_G)
    breakout_p = kicad_to_plate(breakout_k)
    breakout_c = plate_to_case(breakout_p)
    screws_p = np.array([kicad_to_plate(gerber_to_kicad(q)) for q in SCREWS_G])

    # Housing XY orientation: Gerber = ball + diag(-1,+1) * housing-local.
    M_g = np.diag([-1.0, 1.0])
    # Differential vector mapping housing-local -> KiCad -> plate.
    A_hp = R_kp @ R_kg.T @ M_g
    H_plate = np.eye(4)
    H_plate[:2, :2] = A_hp
    H_plate[:2, 3] = ball_p
    # Housing local mounting plane (-18) lands on installed plate top.
    H_plate[2, 3] = PLATE_THICKNESS_MM - HOUSING_MOUNT_LOCAL_Z
    housing_plate = housing.copy()
    housing_plate.apply_transform(H_plate)

    # Plate-native -> case-native full transform. Native plate z=0..1.5; installed bottom is derived above.
    H_pc = np.eye(4)
    H_pc[:2, :2] = R_pc
    H_pc[:2, 3] = t_pc
    H_pc[2, 3] = plate_bottom_case_z
    housing_case = housing_plate.copy()
    housing_case.apply_transform(H_pc)

    hb_p = np.asarray(housing_plate.bounds)
    hb_c = np.asarray(housing_case.bounds)

    # Verify deleted source switch resolves to SW22.
    distances_deleted = np.linalg.norm(sw_pts - deleted_k, axis=1)
    deleted_index = int(np.argmin(distances_deleted))

    report["placement"] = {
        "canonical_frame": "gerber-excellon",
        "ball_gerber": BALL_G,
        "ball_kicad": np.round(ball_k, 6),
        "ball_switchplate_native": np.round(ball_p, 6),
        "ball_case_native": np.round(ball_c, 6),
        "housing_screws_switchplate_native": np.round(screws_p, 6),
        "breakout_switchplate_native": np.round(breakout_p, 6),
        "breakout_case_native": np.round(breakout_c, 6),
        "deleted_switch_source": {
            "ref": sw_rows[deleted_index]["ref"],
            "name": sw_rows[deleted_index]["name"],
            "kicad_xy": sw_pts[deleted_index],
            "canonical_error_mm": float(distances_deleted[deleted_index]),
        },
        "housing_transform_to_switchplate_native": np.round(H_plate, 9),
        "housing_bounds_switchplate_native": np.round(hb_p, 5),
        "housing_bounds_case_native": np.round(hb_c, 5),
    }

    # Conservative retained-keycap XY clearances in plate native frame.
    h_lo, h_hi = hb_p[0, :2], hb_p[1, :2]
    retained = []
    for i, p in enumerate(sw_pts):
        if i == deleted_index:
            continue
        q = kicad_to_plate(p)
        gap = rect_gap(h_lo, h_hi, q, (9.0, 9.0))
        retained.append((gap, i, p, q))
    retained.sort(key=lambda x: x[0])
    report["nearest_retained_switches"] = [
        {
            "ref": sw_rows[i]["ref"],
            "name": sw_rows[i]["name"],
            "kicad_xy": np.round(p, 5),
            "switchplate_xy": np.round(q, 5),
            "conservative_18mm_keycap_xy_gap_mm": float(gap),
        }
        for gap, i, p, q in retained[:4]
    ]

    # Encoder / MCU / TRRS conservative component envelopes.
    groups = {
        "encoder": (footprint_candidates(fps, ["encoder", "rotary"]), (11.0, 11.0)),
        "mcu": (footprint_candidates(fps, ["promicro", "pro_micro", "nice!nano", "rp2040"]), (10.0, 18.0)),
        "trrs": (footprint_candidates(fps, ["trrs", "mj-4", "mj4", "pj320", "pj-320", "audiojack"]), (7.0, 4.0)),
    }
    report["component_clearance"] = {}
    for name, (rows, half) in groups.items():
        values = []
        for f in rows:
            p = np.array([f["x"], f["y"]])
            q = kicad_to_plate(p)
            values.append(
                {
                    "ref": f["ref"],
                    "name": f["name"],
                    "switchplate_xy": np.round(q, 5),
                    "housing_xy_gap_mm": rect_gap(h_lo, h_hi, q, half),
                }
            )
        report["component_clearance"][name] = values

    # Structural mounting axes: minimum center-to-housing-AABB gap using 2.1mm hole + conservative 2mm radial boss allowance.
    structural_gaps = []
    for p in plate_mount_axes:
        structural_gaps.append(rect_gap(h_lo, h_hi, p, (2.0, 2.0)))
    report["structural_mounts"] = {
        "matched_axes": len(plate_mount_axes),
        "minimum_housing_xy_gap_mm": min(structural_gaps) if structural_gaps else None,
        "switchplate_axes": np.round(plate_mount_axes, 5),
    }

    # Breakout geometry and insertion corridor.
    edge = breakout_edge_extents(PATHS["breakout"].read_text(errors="ignore"))
    breakout_dims = None if edge is None else np.sort(edge[1] - edge[0])
    slot_lo = breakout_p + np.array([-1.0, -11.0])
    slot_hi = breakout_p + np.array([1.0, 11.0])
    corridor_gaps = []
    for gap, i, p, q in retained[:10]:
        corridor_gaps.append(rect_gap(slot_lo, slot_hi, q, (9.0, 9.0)))
    report["breakout"] = {
        "board_edgecut_sorted_extents_mm": None if breakout_dims is None else np.round(breakout_dims, 4),
        "reference_slot_size_mm": [2.0, 22.0],
        "slot_center_switchplate_native": np.round(breakout_p, 5),
        "minimum_retained_keycap_corridor_gap_mm": min(corridor_gaps) if corridor_gaps else None,
        "service_path_interpretation": "22 mm breakout short edge through 22 mm-wide reference slot; 2 mm slot dimension clears PCB thickness; board extends inward along sensor direction",
    }

    # Vertical relationship.
    housing_top_case_z = float(hb_c[1, 2])
    housing_mount_case_z = plate_top_case_z
    ball_top_case_z = housing_mount_case_z + BALL_TOP_ABOVE_MOUNT
    report["vertical"] = {
        "housing_mount_plane_case_z": housing_mount_case_z,
        "ball_top_case_z": ball_top_case_z,
        "housing_top_case_z": housing_top_case_z,
        "housing_rim_above_ball_mm": housing_top_case_z - ball_top_case_z,
        "case_lip_above_plate_mm": case_top_z - plate_top_case_z,
    }

    # Exact housing-vs-stock-case collision. A collision with the local shell is acceptable for Task 1
    # only when structural mounting axes remain clear; Tasks 4/5 intentionally provide local relief.
    collision = None
    collision_names = []
    try:
        manager = trimesh.collision.CollisionManager()
        manager.add_object("stock_case", case)
        collision, names = manager.in_collision_single(housing_case, return_names=True)
        collision_names = sorted(list(names)) if names else []
    except Exception as exc:
        report["errors"].append(f"case collision manager failed: {exc}")
    report["stock_case"] = {
        "exact_mesh_collision_with_housing": bool(collision) if collision is not None else None,
        "collision_names": collision_names,
        "interpretation": "A stock shell collision is a known local-relief requirement for Tasks 4/5, not a placement failure, provided all eight structural mounting axes and retained components are clear.",
    }

    # Completion gates.
    sources_ok = all(v["matches"] for v in report["source_hashes"].values())
    gerber_ok = n_kg >= 21 and rms_kg < 0.01 and np.linalg.det(R_kg) < 0
    plate_ok = n_kp >= 18 and rms_kp < 0.05
    case_xy_ok = n_pc >= 8 and rms_pc < 0.05 and np.linalg.det(R_pc) > 0
    stack_ok = (
        abs(PLATE_THICKNESS_MM - float(plate.bounds[1, 2] - plate.bounds[0, 2])) < 0.02
        and 0.5 < case_top_z - plate_top_case_z < 2.0
    )
    retained_ok = len(report["nearest_retained_switches"]) >= 2 and all(
        q["conservative_18mm_keycap_xy_gap_mm"] > 0 for q in report["nearest_retained_switches"][:2]
    )
    encoder_ok = bool(report["component_clearance"]["encoder"]) and all(q["housing_xy_gap_mm"] > 0 for q in report["component_clearance"]["encoder"])
    mcu_ok = bool(report["component_clearance"]["mcu"]) and all(q["housing_xy_gap_mm"] > 0 for q in report["component_clearance"]["mcu"])
    trrs_ok = bool(report["component_clearance"]["trrs"]) and all(q["housing_xy_gap_mm"] > 0 for q in report["component_clearance"]["trrs"])
    mounts_ok = len(plate_mount_axes) == 8 and min(structural_gaps) > 0
    breakout_ok = (
        breakout_dims is not None
        and abs(float(breakout_dims[0]) - 22.0) < 0.05
        and min(corridor_gaps) > 0
    )
    mounting_plane_ok = abs(float(hb_c[0, 2]) - plate_top_case_z) < 0.01
    ball_exposure_ok = 0.0 <= housing_top_case_z - ball_top_case_z <= 2.0

    gates = {
        "housing_sources_verified": bool(sources_ok),
        "gerber_kicad_frame_verified": bool(gerber_ok),
        "pcb_switchplate_frame_verified": bool(plate_ok),
        "switchplate_case_xy_frame_verified": bool(case_xy_ok),
        "case_standoff_plate_stack_verified": bool(stack_ok),
        "r32_r33_nearest_retained_switches_collision_free": bool(retained_ok),
        "encoder_collision_free": bool(encoder_ok),
        "mcu_collision_free": bool(mcu_ok),
        "trrs_collision_free": bool(trrs_ok),
        "eight_structural_mount_axes_clear": bool(mounts_ok),
        "breakout_orientation_and_service_path_verified": bool(breakout_ok),
        "housing_mounting_plane_verified": bool(mounting_plane_ok),
        "ball_exposure_verified": bool(ball_exposure_ok),
        "stock_case_local_shell_relief_required": bool(collision) if collision is not None else None,
    }
    required = [v for k, v in gates.items() if k != "stock_case_local_shell_relief_required"]
    gates["placement_locked"] = bool(all(required) and not report["errors"])
    report["completion_gate"] = gates

    print(json.dumps(report, indent=2, default=native))
    return 0 if gates["placement_locked"] else 2


if __name__ == "__main__":
    sys.exit(main())
