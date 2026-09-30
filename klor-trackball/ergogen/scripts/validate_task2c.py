#!/usr/bin/env python3
"""Task 2C regression gate for the frozen KLOR trackball mechanical delta."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
CONFIG = ERGOGEN / "config.yaml"
BASELINE = ERGOGEN / "task2/task2c-baseline.yaml"

TOL = 2e-6
HIST_TOL = 1e-4
MIN_HOUSING_KEY_GAP = 2.5


def point(generated, name):
    p = generated[name]
    return (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))


def assert_xy(name, actual, expected, tol=TOL):
    d = math.dist(actual[:2], expected[:2])
    if d > tol:
        raise AssertionError(f"{name}: actual={actual[:2]} expected={expected[:2]} delta={d}")
    print(f"PASS {name:34s} x={actual[0]:10.6f} y={actual[1]:10.6f}")


def assert_delta(name, a, b, expected, tol=TOL):
    actual = (a[0] - b[0], a[1] - b[1])
    if math.dist(actual, expected) > tol:
        raise AssertionError(f"{name}: actual={actual}, expected={expected}")
    print(f"PASS {name}: {actual}")


def selector_names(config, outline_name, generated):
    where = config["outlines"][outline_name][0]["where"]
    if not (isinstance(where, str) and where.startswith("/") and where.endswith("/")):
        raise AssertionError(f"{outline_name}: expected regex selector, got {where!r}")
    rx = re.compile(where[1:-1])
    return sorted(name for name in generated if rx.fullmatch(name))


def rect_gap(a_lo, a_hi, center, half=9.0):
    b_lo = (center[0] - half, center[1] - half)
    b_hi = (center[0] + half, center[1] + half)
    dx = max(a_lo[0] - b_hi[0], b_lo[0] - a_hi[0], 0.0)
    dy = max(a_lo[1] - b_hi[1], b_lo[1] - a_hi[1], 0.0)
    return math.hypot(dx, dy)


def point_in_polygon(point_xy, polygon):
    x, y = point_xy
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def segment_distance(point_xy, a, b):
    px, py = point_xy
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    denom = vx * vx + vy * vy
    if denom <= TOL:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / denom))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def polygon_edge_distance(point_xy, polygon):
    return min(
        segment_distance(point_xy, polygon[i], polygon[(i + 1) % len(polygon)])
        for i in range(len(polygon))
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", type=Path, required=True)
    args = ap.parse_args()

    required = [
        args.generated / "points/points.yaml",
        args.generated / "outlines/trackball_board.dxf",
        args.generated / "outlines/trackball_cavity.dxf",
        args.generated / "outlines/trackball_plate_service_opening.dxf",
        args.generated / "outlines/trackball_housing_envelope.dxf",
        args.generated / "outlines/pmw_header_envelope.dxf",
        args.generated / "outlines/task2c_preview.dxf",
        args.generated / "pcbs/task2c_trackball_reference.kicad_pcb",
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing/empty generated output: {path}")

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    baseline = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    generated = yaml.safe_load(
        (args.generated / "points/points.yaml").read_text(encoding="utf-8")
    )

    if baseline["revision"] != 5:
        raise AssertionError("Task 2C must remain at mechanical revision 5")

    ball = point(generated, "ball_center")
    breakout = point(generated, "breakout_center")
    housing = point(generated, "housing_center")
    screw_mid = point(generated, "housing_screw_midpoint")
    screw_1 = point(generated, "housing_screw_1")
    screw_2 = point(generated, "housing_screw_2")
    header = point(generated, "pmw_header_center")

    expected_ball = tuple(float(x) for x in baseline["trackball"]["ball_center_local"])
    assert_xy("Task-2 rev5 ball placement", ball, expected_ball, HIST_TOL)

    prior_ball = tuple(float(x) for x in baseline["placement_adjustment"]["prior_ball_center_local"])
    expected_shift = tuple(float(x) for x in baseline["placement_adjustment"]["shift_xy"])
    actual_shift = (ball[0] - prior_ball[0], ball[1] - prior_ball[1])
    assert_xy("real-housing placement correction", actual_shift, expected_shift, HIST_TOL)

    assert_delta(
        "housing center from ball", housing, ball,
        tuple(float(x) for x in baseline["trackball"]["housing_center_from_ball"]),
    )
    assert_delta(
        "housing screw midpoint from ball", screw_mid, ball,
        tuple(float(x) for x in baseline["housing_mount"]["midpoint_from_ball"]),
    )
    assert_delta("housing screw 1 from midpoint", screw_1, screw_mid, (0.0, 7.98))
    assert_delta("housing screw 2 from midpoint", screw_2, screw_mid, (0.0, -7.98))
    assert_delta(
        "breakout center from ball", breakout, ball,
        tuple(float(x) for x in baseline["breakout"]["center_from_ball"]),
    )
    assert_xy(
        "cabled keyboard PMW header",
        header,
        tuple(float(x) for x in baseline["pmw_header_reference"]["board_center_local"]),
    )

    if not (housing[0] < ball[0] and breakout[0] > ball[0]):
        raise AssertionError("Rev5 housing/opening/connector handedness regressed")
    handed = baseline["handedness"]
    if handed["housing_source_variant"] != "left" or handed["opening_side"] != "negative_x" or handed["connector_side"] != "positive_x":
        raise AssertionError("Rev5 physical housing handedness contract changed")
    header_contract = baseline["pmw_header_reference"]
    if header_contract["connection_form"] != "short_7_conductor_cable":
        raise AssertionError("Rev5 cabled PMW interface changed")
    if header_contract["row_axis"] != "x" or int(header_contract["canonical_rotation"]) != 90:
        raise AssertionError("Rev5 rotated PMW board-header geometry changed")
    if header_contract["pin_1_end"] != "negative_canonical_x" or header_contract["pin_7_end"] != "positive_canonical_x":
        raise AssertionError("Rev5 PMW header endpoint orientation changed")
    print("PASS opening faces -X/thumb side; connector faces +X/outward; board header is rotated/cabled")

    if abs(math.dist(screw_1[:2], screw_2[:2]) - 15.96) > TOL:
        raise AssertionError("housing screw pair spacing changed")
    print("PASS housing screw spacing = 15.96 mm source geometry")

    retained = selector_names(config, "trackball_konrad_switch_cutouts", generated)
    expected_retained = sorted([*(f"sw{i}" for i in range(1, 18)), "sw20", "sw21"])
    if retained != expected_retained:
        raise AssertionError(f"retained key selector mismatch: {retained}")
    print("PASS exactly 19 right keys retained; SW22/R34 remains absent")

    board_contract = [
        (part.get("name"), part.get("operation", "add"))
        for part in config["outlines"]["trackball_board"]
    ]
    if board_contract != [("stock_board", "add"), ("trackball_cavity", "subtract")]:
        raise AssertionError(f"revision-5 board composition changed: {board_contract}")
    print("PASS board delta = stock board - actual-housing/ball cavity")

    plate_parts = config["outlines"]["trackball_plate_service_opening"]
    if plate_parts[0].get("where") != "sw22":
        raise AssertionError("plate must preserve SW22 aperture for cable/header access")
    if plate_parts[1].get("name") != "trackball_cavity":
        raise AssertionError("plate preview must include real-housing cavity")
    print("PASS plate delta uses SW22 cable access plus actual-housing relief")

    if float(config["units"]["ball_diameter"]) != 25:
        raise AssertionError("ball diameter changed")

    cavity_spec = baseline["pcb_cavity"]
    cavity_cfg = config["outlines"]["trackball_cavity"]
    if len(cavity_cfg) != 1 or cavity_cfg[0].get("what") != "polygon":
        raise AssertionError("trackball cavity must be one explicit polygon")
    actual_points = [
        (float(p["shift"][0]), float(p["shift"][1]))
        for p in cavity_cfg[0]["points"]
    ]
    expected_points = [
        (float(p[0]), float(p[1])) for p in cavity_spec["points_from_ball"]
    ]
    if len(actual_points) != len(expected_points):
        raise AssertionError("trackball cavity vertex count changed")
    for actual, expected in zip(actual_points, expected_points):
        assert_xy("real-housing cavity vertex", actual, expected, HIST_TOL)

    if not point_in_polygon((0.0, 0.0), actual_points):
        raise AssertionError("ball center must lie inside PCB cavity")
    clearance = polygon_edge_distance((0.0, 0.0), actual_points)
    print(f"PASS real-housing/ball cavity surrounds ball; nearest boundary={clearance:.6f} mm")

    # Header body and every retained datum must stay out of the cavity.
    header_w = float(config["units"]["pmw_header_body_w"])
    header_h = float(config["units"]["pmw_header_body_h"])
    header_corners = [
        (header[0] + sx * header_w / 2, header[1] + sy * header_h / 2)
        for sx in (-1, 1) for sy in (-1, 1)
    ]
    for corner in header_corners:
        rel = (corner[0] - ball[0], corner[1] - ball[1])
        if point_in_polygon(rel, actual_points):
            raise AssertionError(f"cabled PMW header overlaps actual-housing cavity: {corner}")

    for name in [*(f"sw{i}" for i in range(1, 18)), "sw20", "sw21", *(f"mh{i}" for i in range(1, 10))]:
        p = point(generated, name)
        rel = (p[0] - ball[0], p[1] - ball[1])
        if point_in_polygon(rel, actual_points):
            raise AssertionError(f"retained datum {name} lies inside revision-5 cavity")
    print("PASS cabled PMW header, 19 keys and 9 PCB holes remain outside cavity")

    housing_w = float(config["units"]["housing_w"])
    housing_h = float(config["units"]["housing_h"])
    housing_lo = (housing[0] - housing_w / 2, housing[1] - housing_h / 2)
    housing_hi = (housing[0] + housing_w / 2, housing[1] + housing_h / 2)
    gaps = []
    for name in retained:
        p = point(generated, name)
        gaps.append((rect_gap(housing_lo, housing_hi, p), name))
    gaps.sort()
    min_gap, min_name = gaps[0]
    if min_gap < MIN_HOUSING_KEY_GAP:
        raise AssertionError(f"housing/key clearance regressed: {min_name}={min_gap}")
    print(f"PASS conservative retained-key/housing gap: {min_name}={min_gap:.6f} mm")

    if baseline["support_tongue"]["required"] is not False:
        raise AssertionError("obsolete rigid PMW support tongue returned")
    if baseline["variant"]["removed_right_thumb"] != ["R34"]:
        raise AssertionError("Task 2C right-thumb architecture changed")

    print("PASS Task 2B stock geometry remains a separately generated/validated source layer")
    print("Task 2C revision-5 correctly-handed real-housing geometry regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
