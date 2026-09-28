#!/usr/bin/env python3
"""Task 2D geometry-freeze gate for KLOR trackball revision 4."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
FREEZE = ERGOGEN / "task2/task2d-freeze.yaml"
CONFIG = ERGOGEN / "config.yaml"
REQUIREMENTS = ERGOGEN.parent / "REQUIREMENTS.md"

TOL = 2e-6
HIST_TOL = 1e-4


def pxy(points, name):
    p = points[name]
    return (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))


def assert_close(name, actual, expected, tol=TOL):
    if len(actual) != len(expected) or any(abs(a-b) > tol for a,b in zip(actual, expected)):
        raise AssertionError(f"{name}: {actual} != {expected}")
    print(f"PASS {name}: {actual}")


def assert_delta(name, points, a, b, expected, tol=TOL):
    pa, pb = pxy(points, a), pxy(points, b)
    actual = (pa[0]-pb[0], pa[1]-pb[1])
    assert_close(name, actual, tuple(float(x) for x in expected), tol)


def selector_names(config, outline_name, generated):
    where = config["outlines"][outline_name][0]["where"]
    if not (isinstance(where, str) and where.startswith("/") and where.endswith("/")):
        raise AssertionError(f"{outline_name}: expected regex selector")
    rx = re.compile(where[1:-1])
    return sorted(name for name in generated if rx.fullmatch(name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", type=Path, required=True)
    args = ap.parse_args()

    required = [
        args.generated / "points/points.yaml",
        args.generated / "outlines/trackball_board.dxf",
        args.generated / "outlines/trackball_cavity.dxf",
        args.generated / "outlines/trackball_plate_service_opening.dxf",
        args.generated / "pcbs/task2c_trackball_reference.kicad_pcb",
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing/empty frozen output: {path}")
    print("PASS frozen Task-2 generated outputs exist")

    freeze = yaml.safe_load(FREEZE.read_text(encoding="utf-8"))
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    points = yaml.safe_load((args.generated / "points/points.yaml").read_text(encoding="utf-8"))
    req = REQUIREMENTS.read_text(encoding="utf-8")

    if freeze["status"] != "task2d_frozen" or freeze["revision"] != 4:
        raise AssertionError("Task 2D must remain frozen at revision 4")

    product = freeze["product_geometry"]
    if (product["left_keys"], product["right_keys"], product["total_keys"]) != (20,19,39):
        raise AssertionError("Task-2 key-count freeze changed")
    if product["right_thumb"]["retain"] != [
        {"logical":"R32","switch":"SW20"},
        {"logical":"R33","switch":"SW21"},
    ]:
        raise AssertionError("R32/R33 retention changed")
    if product["right_thumb"]["remove"] != [
        {"logical":"R34","switch":"SW22","diode":"D22"}
    ]:
        raise AssertionError("R34 removal changed")
    print("PASS product freeze = 20 left / 19 right / R32+R33 retained / R34 removed")

    if freeze["rgb"]["left_count"] != 20 or freeze["rgb"]["right_count"] != 19:
        raise AssertionError("RGB count freeze changed")
    if "TBD" in req or "TODO_DECISION" in req:
        raise AssertionError("requirements contain unresolved Task-2 decision markers")

    trackball = freeze["trackball"]
    assert_close(
        "revision-4 ball center",
        pxy(points, "ball_center")[:2],
        tuple(float(x) for x in trackball["ball_center_local"]),
        HIST_TOL,
    )
    assert_delta("housing center from ball", points, "housing_center", "ball_center", trackball["housing_center_from_ball"])
    assert_delta("housing screw midpoint from ball", points, "housing_screw_midpoint", "ball_center", trackball["housing_screw_midpoint_from_ball"])
    assert_delta("housing screw 1", points, "housing_screw_1", "housing_screw_midpoint", trackball["housing_screw_offsets_from_midpoint"][0])
    assert_delta("housing screw 2", points, "housing_screw_2", "housing_screw_midpoint", trackball["housing_screw_offsets_from_midpoint"][1])
    assert_delta("breakout center from ball", points, "breakout_center", "ball_center", freeze["breakout"]["center_from_ball"])

    header = freeze["pmw_header"]
    assert_close(
        "cabled keyboard PMW header center",
        pxy(points, "pmw_header_center")[:2],
        tuple(float(x) for x in header["center_local"]),
        HIST_TOL,
    )
    if header["connection_form"] != "short_7_conductor_cable":
        raise AssertionError("PMW connection must remain cabled")
    if freeze["breakout"]["connector_side"] != "positive_x":
        raise AssertionError("Kivipallur connector side changed")
    if pxy(points, "breakout_center")[0] <= pxy(points, "ball_center")[0]:
        raise AssertionError("Kivipallur connector is no longer on +X/right side")
    print("PASS real housing keeps right-side breakout while board header is cabled")

    expected_pin_order = {
        1:"CS", 2:"MISO", 3:"MOSI", 4:"SCK",
        5:"NC_MOTION", 6:"3V3", 7:"GND",
    }
    actual_pin_order = {int(k):v for k,v in header["physical_pin_order_positive_y_to_negative_y"].items()}
    if actual_pin_order != expected_pin_order:
        raise AssertionError(f"PMW physical pin order changed: {actual_pin_order}")
    if header["mating_rule"] != "cable_maps_breakout_pin_N_to_keyboard_pin_8_minus_N":
        raise AssertionError("revision-4 cable mating rule changed")
    print("PASS PMW electrical/physical pin contract unchanged")

    retained = selector_names(config, "trackball_konrad_switch_cutouts", points)
    expected_retained = sorted([*(f"sw{i}" for i in range(1,18)), "sw20", "sw21"])
    if retained != expected_retained:
        raise AssertionError(f"retained right key selector changed: {retained}")

    pcb = freeze["pcb_geometry"]
    actual_composition = [
        {"outline":part["name"], "operation":part.get("operation","add")}
        for part in config["outlines"]["trackball_board"]
    ]
    if actual_composition != pcb["composition"]:
        raise AssertionError(f"PCB composition changed: {actual_composition}")
    if actual_composition != [
        {"outline":"stock_board","operation":"add"},
        {"outline":"trackball_cavity","operation":"subtract"},
    ]:
        raise AssertionError("obsolete support tongue/service slot returned")
    print("PASS PCB freeze = stock board - real-housing/ball cavity")

    cavity_cfg = config["outlines"]["trackball_cavity"][0]
    actual_points = [
        [float(p["shift"][0]), float(p["shift"][1])]
        for p in cavity_cfg["points"]
    ]
    expected_points = [[float(x),float(y)] for x,y in pcb["cavity"]["points_from_ball"]]
    if len(actual_points) != len(expected_points):
        raise AssertionError("cavity vertex count changed")
    for a,e in zip(actual_points,expected_points):
        assert_close("cavity vertex", a, e, HIST_TOL)
    print("PASS actual Type-C housing/ball-derived cavity is frozen")

    plate = config["outlines"]["trackball_plate_service_opening"]
    if plate[0].get("where") != "sw22" or plate[1].get("name") != "trackball_cavity":
        raise AssertionError("switchplate preview no longer uses SW22 cable access + housing relief")
    print("PASS switchplate mechanical delta matches revision 4")

    placement = pcb["placement_adjustment"]
    prior = tuple(float(x) for x in placement["prior_ball_center_local"])
    shift = (
        pxy(points,"ball_center")[0]-prior[0],
        pxy(points,"ball_center")[1]-prior[1],
    )
    assert_close("Task2E-derived ball shift", shift, tuple(float(x) for x in placement["shift_xy"]), HIST_TOL)

    forbidden = set(freeze["task3_change_boundary"]["forbidden_without_reopening_task2"])
    must = {
        "move_any_retained_key_center_or_rotation",
        "restore_R34_or_remove_R32_or_R33",
        "move_any_structural_axis",
        "move_ball_housing_or_breakout",
        "change_actual_housing_derived_trackball_cavity",
        "move_keyboard_side_PMW_cable_header",
    }
    if not must.issubset(forbidden):
        raise AssertionError("revision-4 downstream geometry boundary is incomplete")
    print("PASS Task-3 forbidden-without-reopening boundary is explicit")

    print("Task 2D revision-4 canonical geometry freeze gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
