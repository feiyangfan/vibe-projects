#!/usr/bin/env python3
"""Task 2C regression gate for the minimal KLOR trackball geometry delta."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import yaml

from validate_task2b import (
    local_from_kicad,
    parse_footprints,
    top_edge_primitives,
)


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
KLOR = HERE.parents[2]
CONFIG = ERGOGEN / "config.yaml"
BASELINE = ERGOGEN / "task2/task2c-baseline.yaml"
STOCK_PCB = KLOR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"

TOL = 2e-6
HIST_TOL = 1e-4
MIN_HOUSING_KEY_GAP = 2.5
MIN_NOTCH_TO_MH8_EDGE_GAP = 0.5


def point(generated, name):
    p = generated[name]
    return (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))


def assert_xy(name, actual, expected, tol=TOL):
    d = math.dist(actual[:2], expected[:2])
    if d > tol:
        raise AssertionError(f"{name}: actual={actual[:2]} expected={expected[:2]} delta={d}")
    print(f"PASS {name:26s} x={actual[0]:10.6f} y={actual[1]:10.6f}")


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


def stock_lower_edge_y_at_x(pcb_text, origin, x):
    """Return the lowest stock Edge.Cuts line intersection at canonical X."""
    ys = []
    for prim in top_edge_primitives(pcb_text):
        if prim["type"] != "gr_line":
            continue
        (x1, y1), (x2, y2) = prim["pts"]
        a = local_from_kicad((x1, y1, 0.0), origin)
        b = local_from_kicad((x2, y2, 0.0), origin)
        if not (min(a[0], b[0]) - TOL <= x <= max(a[0], b[0]) + TOL):
            continue
        dx = b[0] - a[0]
        if abs(dx) <= TOL:
            continue
        t = (x - a[0]) / dx
        ys.append(a[1] + t * (b[1] - a[1]))
    if not ys:
        raise AssertionError(f"no stock Edge.Cuts line covers x={x}")
    return min(ys)


def rect_gap(a_lo, a_hi, center, half=9.0):
    b_lo = (center[0] - half, center[1] - half)
    b_hi = (center[0] + half, center[1] + half)
    dx = max(a_lo[0] - b_hi[0], b_lo[0] - a_hi[0], 0.0)
    dy = max(a_lo[1] - b_hi[1], b_lo[1] - a_hi[1], 0.0)
    return math.hypot(dx, dy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", type=Path, required=True)
    args = ap.parse_args()

    required = [
        args.generated / "points/points.yaml",
        args.generated / "outlines/trackball_board.dxf",
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
    pcb_text = STOCK_PCB.read_text(encoding="utf-8")
    fps = parse_footprints(pcb_text)
    origin = fps["SW13"]

    ball = point(generated, "ball_center")
    breakout = point(generated, "breakout_center")
    housing = point(generated, "housing_center")
    screw_mid = point(generated, "housing_screw_midpoint")
    screw_1 = point(generated, "housing_screw_1")
    screw_2 = point(generated, "housing_screw_2")
    header = point(generated, "pmw_header_center")
    tongue = point(generated, "pmw_support_tongue_center")

    expected_ball = tuple(float(x) for x in baseline["trackball"]["ball_center_local"])
    assert_xy("Task-2 rev2 ball placement", ball, expected_ball, HIST_TOL)

    prior_ball = tuple(float(x) for x in baseline["placement_adjustment"]["prior_ball_center_local"])
    expected_shift = float(baseline["placement_adjustment"]["inward_shift_x"])
    actual_shift = (ball[0] - prior_ball[0], ball[1] - prior_ball[1])
    assert_xy("connector-right inward placement shift", actual_shift, (expected_shift, 0.0), HIST_TOL)

    assert_delta(
        "housing center from ball",
        housing,
        ball,
        tuple(float(x) for x in baseline["trackball"]["housing_center_from_ball"]),
    )
    assert_delta(
        "housing screw midpoint from ball",
        screw_mid,
        ball,
        tuple(float(x) for x in baseline["housing_mount"]["midpoint_from_ball"]),
    )
    assert_delta("housing screw 1 from midpoint", screw_1, screw_mid, (0.0, 7.98))
    assert_delta("housing screw 2 from midpoint", screw_2, screw_mid, (0.0, -7.98))
    assert_delta(
        "breakout center from ball",
        breakout,
        ball,
        tuple(float(x) for x in baseline["breakout"]["center_from_ball"]),
    )
    assert_delta(
        "PMW header from breakout",
        header,
        breakout,
        tuple(float(x) for x in baseline["pmw_header_reference"]["center_from_breakout"]),
    )
    if not (housing[0] > ball[0] and breakout[0] > ball[0] and header[0] > ball[0]):
        raise AssertionError("connector-right orientation regressed: housing/breakout/header must be +X of ball")
    print("PASS KLORBall-35 handedness: connector assembly is on +X / right side of ball")
    if abs(math.dist(screw_1[:2], screw_2[:2]) - 15.96) > TOL:
        raise AssertionError("housing screw pair spacing changed")
    print("PASS housing screw spacing = 15.96 mm source geometry")

    retained = selector_names(config, "trackball_konrad_switch_cutouts", generated)
    expected_retained = [*(f"sw{i}" for i in range(1, 18)), "sw20", "sw21"]
    if retained != sorted(expected_retained):
        raise AssertionError(f"retained key selector mismatch: {retained}")
    if "sw22" in retained:
        raise AssertionError("SW22/R34 must be suppressed in Task 2C")
    print("PASS 19-key right-half target geometry suppresses SW22/R34 only")

    board_parts = config["outlines"]["trackball_board"]
    board_contract = [
        (board_parts[0].get("name"), board_parts[0].get("operation", "add")),
        (board_parts[1].get("name"), board_parts[1].get("operation", "add")),
        (board_parts[2].get("name"), board_parts[2].get("operation", "add")),
    ]
    expected_board_contract = [
        ("stock_board", "add"),
        ("pmw_support_tongue", "add"),
        ("breakout_service_slot", "subtract"),
    ]
    if board_contract != expected_board_contract:
        raise AssertionError(f"trackball board composition changed: {board_contract}")
    print("PASS board delta = stock + local support tongue - 2x22 service notch")

    plate_parts = config["outlines"]["trackball_plate_service_opening"]
    if plate_parts[0].get("where") != "sw22":
        raise AssertionError("plate service opening must reuse stock SW22 aperture")
    if plate_parts[1].get("name") != "breakout_service_slot":
        raise AssertionError("plate service opening must merge with breakout slot")
    print("PASS plate preserves R34 opening and adds connector-right 2x22 corridor")

    units = config["units"]
    if float(units["ball_diameter"]) != 25:
        raise AssertionError("ball diameter changed")
    if [float(units["breakout_slot_w"]), float(units["breakout_slot_h"])] != [2.0, 22.0]:
        raise AssertionError("breakout service envelope changed")

    edge_y = stock_lower_edge_y_at_x(pcb_text, origin, header[0])
    header_w = float(units["pmw_header_body_w"])
    header_h = float(units["pmw_header_body_h"])
    header_bottom = header[1] - header_h / 2
    overhang = edge_y - header_bottom
    expected_overhang = float(baseline["support_tongue"]["body_overhang_beyond_stock_edge"])
    if abs(overhang - expected_overhang) > HIST_TOL:
        raise AssertionError(f"header overhang regression changed: {overhang}")
    print(f"PASS connector-right PMW header overhangs stock edge by {overhang:.6f} mm")

    tongue_w = float(units["pmw_support_tongue_w"])
    tongue_h = float(units["pmw_support_tongue_h"])
    tongue_lo = (tongue[0] - tongue_w / 2, tongue[1] - tongue_h / 2)
    tongue_hi = (tongue[0] + tongue_w / 2, tongue[1] + tongue_h / 2)
    header_lo = (header[0] - header_w / 2, header[1] - header_h / 2)
    header_hi = (header[0] + header_w / 2, header[1] + header_h / 2)
    if tongue_lo[0] > header_lo[0] + TOL or tongue_hi[0] < header_hi[0] - TOL:
        raise AssertionError("support tongue does not cover PMW header width")
    if tongue_lo[1] > header_lo[1] + TOL:
        raise AssertionError("support tongue is not deep enough for PMW header")
    tongue_join_edge_y = stock_lower_edge_y_at_x(pcb_text, origin, tongue_lo[0])
    expected_join = float(baseline["support_tongue"]["stock_edge_y_at_tongue_inner_x"])
    if abs(tongue_join_edge_y - expected_join) > HIST_TOL:
        raise AssertionError("support-tongue stock-edge join regression changed")
    if abs(tongue_hi[1] - tongue_join_edge_y) > HIST_TOL:
        raise AssertionError(
            f"support tongue does not terminate at sloped stock edge: {tongue_hi[1]} vs {tongue_join_edge_y}"
        )
    slot_w = float(units["breakout_slot_w"])
    if abs(tongue_hi[0] - (breakout[0] - slot_w / 2)) > HIST_TOL:
        raise AssertionError("connector-right support tongue must terminate at negative-X slot edge")
    print("PASS re-derived connector-right support tongue joins stock edge and service notch")

    slot_h = float(units["breakout_slot_h"])
    slot_top = breakout[1] + slot_h / 2
    slot_bottom = breakout[1] - slot_h / 2
    breakout_edge_y = stock_lower_edge_y_at_x(pcb_text, origin, breakout[0])
    if not (slot_bottom < breakout_edge_y < slot_top):
        raise AssertionError("2x22 breakout slot no longer crosses the stock lower edge")

    mh8 = point(generated, "mh8")
    slot_lo_x = breakout[0] - slot_w / 2
    slot_hi_x = breakout[0] + slot_w / 2
    dx = max(slot_lo_x - mh8[0], mh8[0] - slot_hi_x, 0.0)
    dy = max(slot_bottom - mh8[1], mh8[1] - slot_top, 0.0)
    notch_to_mh8_edge = math.hypot(dx, dy) - float(units["pcb_m3_hole"]) / 2
    if notch_to_mh8_edge < MIN_NOTCH_TO_MH8_EDGE_GAP:
        raise AssertionError(f"connector-right notch/MH8 clearance too small: {notch_to_mh8_edge}")
    print(f"PASS stock MH8 retained with {notch_to_mh8_edge:.6f} mm notch-edge clearance")

    housing_w = float(units["housing_w"])
    housing_h = float(units["housing_h"])
    housing_lo = (housing[0] - housing_w / 2, housing[1] - housing_h / 2)
    housing_hi = (housing[0] + housing_w / 2, housing[1] + housing_h / 2)
    gaps = []
    for name in retained:
        p = point(generated, name)
        gaps.append((rect_gap(housing_lo, housing_hi, p), name))
    gaps.sort()
    min_gap, min_name = gaps[0]
    if min_gap < MIN_HOUSING_KEY_GAP:
        raise AssertionError(f"housing/key clearance regressed: {min_name} = {min_gap}")
    print(f"PASS conservative retained-key/housing gap: {min_name} = {min_gap:.6f} mm")

    if baseline["support_tongue"]["required"] is not True:
        raise AssertionError("Task 2C baseline no longer records support tongue as required")
    if baseline["variant"]["removed_right_thumb"] != ["R34"]:
        raise AssertionError("Task 2C right-thumb architecture changed")

    print("PASS Task 2B stock geometry remains a separately generated/validated source layer")
    print("Task 2C minimal trackball-delta regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
