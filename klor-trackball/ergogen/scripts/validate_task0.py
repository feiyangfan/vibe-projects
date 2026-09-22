#!/usr/bin/env python3
"""Task 0 Ergogen feasibility regression gate.

The generated Ergogen points are compared against geometry derived directly from
stock KLOR 1.4 KiCad. This intentionally avoids treating hand-copied Task 0
coordinates as the reference oracle.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve()
ERGOGEN_DIR = SCRIPT.parents[1]
KLOR_DIR = SCRIPT.parents[2]
STOCK_PCB = KLOR_DIR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
REFERENCE = ERGOGEN_DIR / "reference-baseline.yaml"

STOCK_POINT_MAP = {
    "sw13": "SW13",
    "sw14": "SW14",
    "sw15": "SW15",
    "sw21": "SW21",
    "sw22": "SW22",
    "mcu_ref": "U1",
    "trrs_ref": "J1",
    "encoder_ref": "SW18",
    "mh5": "MH5",
    "mh7": "MH7",
    "mh8": "MH8",
}

POS_TOL_MM = 1e-6
ROT_TOL_DEG = 1e-6


def balanced_blocks(text: str, token: str) -> list[str]:
    result: list[str] = []
    needle = "(" + token
    pos = 0
    while True:
        start = text.find(needle, pos)
        if start < 0:
            return result
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
            raise ValueError(f"unbalanced KiCad {token} block")
        result.append(text[start:end])
        pos = end


def stock_footprints() -> dict[str, tuple[float, float, float]]:
    text = STOCK_PCB.read_text(encoding="utf-8")
    found: dict[str, tuple[float, float, float]] = {}
    for block in balanced_blocks(text, "footprint"):
        ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if not ref_match:
            ref_match = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', block)
        if not ref_match:
            continue
        at_match = re.search(
            r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)",
            block,
        )
        if not at_match:
            continue
        found[ref_match.group(1)] = (
            float(at_match.group(1)),
            float(at_match.group(2)),
            float(at_match.group(3) or 0.0),
        )
    return found


def canonical_from_stock(
    p: tuple[float, float, float],
    origin: tuple[float, float, float],
) -> tuple[float, float, float]:
    # KiCad board coordinates have +Y downward. Ergogen uses a Cartesian +Y-up
    # design frame for this migration, so both Y and angle are reflected.
    return (p[0] - origin[0], origin[1] - p[1], -p[2])


def get_point(data: dict, name: str) -> tuple[float, float, float]:
    if name not in data:
        raise AssertionError(f"generated point missing: {name}")
    point = data[name]
    return (float(point["x"]), float(point["y"]), float(point.get("r", 0.0)))


def assert_close(name: str, actual, expected) -> None:
    dx = abs(actual[0] - expected[0])
    dy = abs(actual[1] - expected[1])
    dr = abs(actual[2] - expected[2])
    if dx > POS_TOL_MM or dy > POS_TOL_MM or dr > ROT_TOL_DEG:
        raise AssertionError(
            f"{name}: generated={actual}, expected={expected}, "
            f"delta=({dx:.9f}, {dy:.9f}, {dr:.9f})"
        )
    print(
        f"PASS {name:12s} "
        f"x={actual[0]:10.6f} y={actual[1]:10.6f} r={actual[2]:8.3f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=Path, required=True)
    args = parser.parse_args()

    points_file = args.generated / "points/points.yaml"
    pcb_file = args.generated / "pcbs/task0_prototype.kicad_pcb"
    plate_file = args.generated / "outlines/prototype_plate.dxf"
    preview_file = args.generated / "outlines/preview.dxf"

    for path in (points_file, pcb_file, plate_file, preview_file):
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"required generated output missing/empty: {path}")

    points = yaml.safe_load(points_file.read_text(encoding="utf-8"))
    stock = stock_footprints()
    origin = stock["SW13"]

    for point_name, stock_ref in STOCK_POINT_MAP.items():
        assert_close(
            point_name,
            get_point(points, point_name),
            canonical_from_stock(stock[stock_ref], origin),
        )

    baseline = yaml.safe_load(REFERENCE.read_text(encoding="utf-8"))
    hist = baseline["trackball_reference"]["previous_kicad_frame_datums_mm"]
    for point_name, source_name in (
        ("trackball_ref", "ball_center"),
        ("breakout_ref", "breakout_slot_center"),
    ):
        xy = hist[source_name]
        expected = (float(xy[0]) - origin[0], origin[1] - float(xy[1]), 0.0)
        assert_close(point_name, get_point(points, point_name), expected)

    pcb = pcb_file.read_text(encoding="utf-8")
    required_tokens = (
        "MX",
        "WS2812B",
        "SW13_FROM",
        "SW13_TO",
        "RGB_IN",
        "RGB_OUT",
    )
    missing = [token for token in required_tokens if token not in pcb]
    if missing:
        raise AssertionError(f"generated PCB missing expected MX/RGB tokens: {missing}")

    print("PASS generated KiCad PCB contains MX + RGB prototype footprints/nets")
    print("PASS generated plate and preview DXF outputs exist")
    print("Task 0 Ergogen feasibility regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
