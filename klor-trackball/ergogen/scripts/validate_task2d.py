#!/usr/bin/env python3
"""Task 2D freeze gate for the canonical KLOR trackball geometry contract."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
KLOR = HERE.parents[2]
CONFIG = ERGOGEN / "config.yaml"
FREEZE = ERGOGEN / "task2/task2d-freeze.yaml"
REQUIREMENTS = KLOR / "REQUIREMENTS.md"

TOL = 2e-6


def pxy(points, name):
    p = points[name]
    return (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))


def assert_close(name, actual, expected, tol=TOL):
    if len(actual) != len(expected):
        raise AssertionError(f"{name}: dimensionality changed")
    delta = math.dist(tuple(actual), tuple(expected))
    if delta > tol:
        raise AssertionError(f"{name}: actual={actual} expected={expected} delta={delta}")
    print(f"PASS {name}: {actual}")


def assert_delta(name, points, child, parent, expected):
    a = pxy(points, child)
    b = pxy(points, parent)
    actual = (a[0] - b[0], a[1] - b[1])
    assert_close(name, actual, tuple(float(x) for x in expected))


def selector_names(config, outline_name, generated):
    where = config["outlines"][outline_name][0]["where"]
    if not (isinstance(where, str) and where.startswith("/") and where.endswith("/")):
        raise AssertionError(f"{outline_name}: expected regex selector, got {where!r}")
    rx = re.compile(where[1:-1])
    return sorted(name for name in generated if rx.fullmatch(name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", type=Path, required=True)
    args = ap.parse_args()

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    freeze = yaml.safe_load(FREEZE.read_text(encoding="utf-8"))
    requirements = REQUIREMENTS.read_text(encoding="utf-8")
    points = yaml.safe_load(
        (args.generated / "points/points.yaml").read_text(encoding="utf-8")
    )

    required_outputs = [
        args.generated / "outlines/trackball_board.dxf",
        args.generated / "outlines/trackball_plate_service_opening.dxf",
        args.generated / "outlines/task2c_preview.dxf",
        args.generated / "pcbs/task2c_trackball_reference.kicad_pcb",
    ]
    for path in required_outputs:
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing/empty frozen geometry output: {path}")
    print("PASS frozen Task-2 generated outputs exist")

    if freeze["revision"] != 1:
        raise AssertionError("Task 2D freeze revision changed")
    if freeze["status"] not in {"task2d_frozen_candidate", "task2d_frozen"}:
        raise AssertionError(f"unexpected freeze status: {freeze['status']}")

    product = freeze["product_geometry"]
    expected_counts = (20, 19, 39)
    actual_counts = (
        int(product["left_keys"]),
        int(product["right_keys"]),
        int(product["total_keys"]),
    )
    if actual_counts != expected_counts:
        raise AssertionError(f"key-count contract changed: {actual_counts}")
    print("PASS Rev-1 key-count freeze = 20 left / 19 right / 39 total")

    retain = product["right_thumb"]["retain"]
    remove = product["right_thumb"]["remove"]
    if retain != [
        {"logical": "R32", "switch": "SW20"},
        {"logical": "R33", "switch": "SW21"},
    ]:
        raise AssertionError(f"right-thumb retained set changed: {retain}")
    if remove != [{"logical": "R34", "switch": "SW22", "diode": "D22"}]:
        raise AssertionError(f"right-thumb removed set changed: {remove}")
    if product["encoders"]["right"] != {
        "state": "retained",
        "reference": "SW18",
        "location": "stock",
    }:
        raise AssertionError("right encoder freeze changed")
    print("PASS Rev-1 right-thumb and right-encoder architecture frozen")

    rgb = freeze["rgb"]
    if (rgb["left_count"], rgb["right_count"], rgb["total_count"]) != (20, 19, 39):
        raise AssertionError("RGB count freeze changed")
    if not rgb["no_rgb_at_removed_R34"]:
        raise AssertionError("removed R34 unexpectedly owns RGB")
    print("PASS RGB freeze = 20 left / 19 right / no R34 RGB")

    unresolved = [
        "To be locked in Task 2",
        "geometry candidates; exact retained/removed set is not yet frozen",
        "optional pending Task 2 geometry evaluation",
    ]
    for phrase in unresolved:
        if phrase in requirements:
            raise AssertionError(f"requirements still contain unresolved Task-2 decision: {phrase}")
    required_phrases = [
        "REV 1 PRODUCT + TASK 2 GEOMETRY",
        "| Right key count | **19** |",
        "**Retain R32 / SW20 and R33 / SW21; remove R34 / SW22 / D22**",
        "The **right EC11-class encoder is retained in its stock location** for Rev 1.",
        "- **19 LEDs on the right**;",
        "Frozen keyboard-side physical pin order entering Task 3:",
    ]
    for phrase in required_phrases:
        if phrase not in requirements:
            raise AssertionError(f"requirements freeze text missing: {phrase}")
    print("PASS REQUIREMENTS.md contains no unresolved Task-2 decisions")

    units = config["units"]
    trackball = freeze["trackball"]
    breakout = freeze["breakout"]
    header = freeze["pmw_header"]
    pcb = freeze["pcb_geometry"]

    numeric_unit_contract = {
        "ball_diameter": trackball["ball_diameter"],
        "housing_w": trackball["housing_envelope"][0],
        "housing_h": trackball["housing_envelope"][1],
        "breakout_slot_w": breakout["service_slot"][0],
        "breakout_slot_h": breakout["service_slot"][1],
        "pmw_header_pitch": header["pitch"],
        "pmw_header_body_w": header["body_reference_envelope"][0],
        "pmw_header_body_h": header["body_reference_envelope"][1],
        "pmw_support_tongue_w": pcb["support_tongue"]["size"][0],
        "pmw_support_tongue_h": pcb["support_tongue"]["size"][1],
    }
    for name, expected in numeric_unit_contract.items():
        if abs(float(units[name]) - float(expected)) > TOL:
            raise AssertionError(f"{name}: config={units[name]} freeze={expected}")
    print("PASS frozen Task-2 dimensions match Ergogen units")

    assert_close(
        "ball center",
        pxy(points, "ball_center")[:2],
        tuple(float(x) for x in trackball["ball_center_local"]),
    )
    assert_delta(
        "housing center from ball",
        points,
        "housing_center",
        "ball_center",
        trackball["housing_center_from_ball"],
    )
    assert_delta(
        "housing screw midpoint from ball",
        points,
        "housing_screw_midpoint",
        "ball_center",
        trackball["housing_screw_midpoint_from_ball"],
    )
    screw_offsets = trackball["housing_screw_offsets_from_midpoint"]
    assert_delta(
        "housing screw 1 from midpoint",
        points,
        "housing_screw_1",
        "housing_screw_midpoint",
        screw_offsets[0],
    )
    assert_delta(
        "housing screw 2 from midpoint",
        points,
        "housing_screw_2",
        "housing_screw_midpoint",
        screw_offsets[1],
    )
    assert_delta(
        "breakout center from ball",
        points,
        "breakout_center",
        "ball_center",
        breakout["center_from_ball"],
    )
    assert_delta(
        "PMW header from breakout",
        points,
        "pmw_header_center",
        "breakout_center",
        header["center_from_breakout"],
    )
    assert_delta(
        "support tongue from breakout",
        points,
        "pmw_support_tongue_center",
        "breakout_center",
        pcb["support_tongue"]["center_from_breakout"],
    )

    screw_spacing = math.dist(
        pxy(points, "housing_screw_1")[:2],
        pxy(points, "housing_screw_2")[:2],
    )
    if abs(screw_spacing - float(trackball["housing_screw_spacing"])) > TOL:
        raise AssertionError(f"housing screw spacing changed: {screw_spacing}")
    print(f"PASS housing screw spacing frozen at {screw_spacing:.6f} mm")

    retained = selector_names(config, "trackball_konrad_switch_cutouts", points)
    expected_retained = sorted([*(f"sw{i}" for i in range(1, 18)), "sw20", "sw21"])
    if retained != expected_retained:
        raise AssertionError(f"target key selector drifted: {retained}")
    if "sw22" in retained:
        raise AssertionError("SW22/R34 returned to the Rev-1 target")
    print("PASS target selector remains exactly 19 right-half keys")

    board_parts = config["outlines"]["trackball_board"]
    actual_board = [
        {
            "outline": part["name"],
            "operation": part.get("operation", "add"),
        }
        for part in board_parts
    ]
    if actual_board != pcb["composition"]:
        raise AssertionError(f"frozen PCB composition changed: {actual_board}")
    print("PASS PCB outline composition matches Task-2D freeze")

    plate = config["outlines"]["trackball_plate_service_opening"]
    if plate[0].get("where") != "sw22" or plate[0].get("size") != ["mx_cutout", "mx_cutout"]:
        raise AssertionError("plate no longer reuses the stock R34 aperture")
    if plate[1].get("name") != "breakout_service_slot" or plate[1].get("operation") != "add":
        raise AssertionError("plate service corridor composition changed")
    print("PASS switchplate service delta remains R34 aperture + 2x22 corridor")

    if header["keyboard_side"] != "F.Cu":
        raise AssertionError("PMW keyboard-side connector side changed")
    if header["row_axis"] != "y":
        raise AssertionError("PMW connector row axis changed")
    expected_pin_order = {
        1: "CS",
        2: "MISO",
        3: "MOSI",
        4: "SCK",
        5: "NC_MOTION",
        6: "3V3",
        7: "GND",
    }
    actual_pin_order = {int(k): v for k, v in header["physical_pin_order_negative_y_to_positive_y"].items()}
    if actual_pin_order != expected_pin_order:
        raise AssertionError(f"PMW physical pin order changed: {actual_pin_order}")
    if header["mating_rule"] != "breakout_pin_N_to_keyboard_pin_8_minus_N":
        raise AssertionError("PMW mating rule changed")
    print("PASS PMW physical connector contract frozen")

    forbidden = set(freeze["task3_change_boundary"]["forbidden_without_reopening_task2"])
    must_forbid = {
        "move_any_retained_key_center_or_rotation",
        "restore_R34_or_remove_R32_or_R33",
        "move_or_remove_right_encoder",
        "move_any_structural_axis",
        "move_ball_housing_breakout_or_pmw_header_reference",
        "change_pmw_header_side_row_axis_or_physical_pin_order",
    }
    if not must_forbid.issubset(forbidden):
        raise AssertionError("Task-3 geometry change boundary is incomplete")
    print("PASS Task-3 forbidden-without-reopening boundary is explicit")

    if trackball["housing_screw_final_hole_diameter"] != "deferred_to_task5":
        raise AssertionError("housing drill diameter should remain a Task-5 fabrication detail")
    if freeze["case_geometry_contract"]["right_case"]["exact_clearance_margin"] != "deferred_to_task6":
        raise AssertionError("case clearance margin should remain a Task-6 detail")
    print("PASS downstream implementation details remain deferred without reopening geometry")

    print("Task 2D canonical geometry freeze gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
