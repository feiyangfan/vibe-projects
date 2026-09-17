#!/usr/bin/env python3
"""Task 2C: audit the Kivipallur connector and Klorball35 mating reference.

Read-only source audit. It compares the PMW3360 breakout connector to the
Klorball35 right-hand connector and records the mechanical pass-through slot.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
BREAKOUT_PCB = ROOT / "klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb"
RIGHT_PCB = ROOT / "klorball35/kicad/klorball35_right/klorball35_right.kicad_pcb"
RIGHT_SCH = ROOT / "klorball35/kicad/klorball35_right/klorball35_right.kicad_sch"
ERGOGEN = ROOT / "klorball35/config.yml"

EXPECTED_ORDER = {
    "1": "GND",
    "2": "+3V3",
    "3": "/MOTION",
    "4": "/SCK",
    "5": "/MOSI",
    "6": "/MISO",
    "7": "/CS",
}
EXPECTED_RIGHT_ORDER = {
    "1": "GND",
    "2": "+3V3",
    "3": None,
    "4": "SCK",
    "5": "MOSI",
    "6": "MISO",
    "7": "CS",
}
EXPECTED_FOOTPRINT = "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"


def balanced(text: str, start: int) -> str:
    depth = 0
    quoted = False
    escaped = False
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
                return text[start:i + 1]
    raise ValueError(f"unterminated S-expression at {start}")


def blocks(text: str, token: str) -> Iterable[str]:
    pat = re.compile(r"\(" + re.escape(token) + r"(?=\s|\()")
    pos = 0
    while True:
        match = pat.search(text, pos)
        if not match:
            return
        block = balanced(text, match.start())
        yield block
        pos = match.start() + len(block)


def qprop(block: str, name: str) -> str | None:
    m = re.search(r'\(property\s+"' + re.escape(name) + r'"\s+"([^"]*)"', block)
    return m.group(1) if m else None


def atom(block: str, name: str) -> str | None:
    m = re.search(r"\(" + re.escape(name) + r'\s+(?:"([^"]*)"|([^\s()]+))', block)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def first_at(block: str) -> list[float] | None:
    m = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?\)", block)
    return [float(v) for v in m.groups() if v is not None] if m else None


def xy(block: str, token: str) -> list[float] | None:
    m = re.search(r"\(" + re.escape(token) + r"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)", block)
    return [float(m.group(1)), float(m.group(2))] if m else None


def parse_pads(fp: str) -> list[dict]:
    out = []
    for pb in blocks(fp, "pad"):
        h = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pb)
        if not h:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pb)
        pinfunction = re.search(r'\(pinfunction\s+"([^"]*)"\)', pb)
        out.append({
            "number": h.group(1),
            "type": h.group(2),
            "shape": h.group(3),
            "at": first_at(pb),
            "net_id": int(net.group(1)) if net else None,
            "net": net.group(2) if net else None,
            "pinfunction": pinfunction.group(1) if pinfunction else None,
        })
    return out


def footprints(text: str) -> list[dict]:
    out = []
    for fb in blocks(text, "footprint"):
        ref = qprop(fb, "Reference")
        if not ref:
            continue
        head = re.match(r'\(footprint\s+"([^"]*)"', fb)
        out.append({
            "ref": ref,
            "value": qprop(fb, "Value"),
            "footprint": head.group(1) if head else None,
            "layer": atom(fb, "layer"),
            "at": first_at(fb),
            "pads": parse_pads(fb),
        })
    return out


def fp_by_ref(text: str, ref: str) -> dict:
    matches = [fp for fp in footprints(text) if fp["ref"] == ref]
    if len(matches) != 1:
        raise ValueError(f"expected one {ref}, found {len(matches)}")
    return matches[0]


def pad_map(fp: dict) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for p in fp["pads"]:
        if p["number"] and p["number"] not in result:
            result[p["number"]] = p["net"]
    return result


def board_edge_report(text: str) -> dict:
    lines = []
    for gb in blocks(text, "gr_line"):
        if atom(gb, "layer") != "Edge.Cuts":
            continue
        a, b = xy(gb, "start"), xy(gb, "end")
        if a and b:
            lines.append({"start": a, "end": b})
    coords = [p for line in lines for p in (line["start"], line["end"])]
    bbox = None
    if coords:
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    return {"line_count": len(lines), "bbox": bbox, "lines": lines}


def schematic_connector(text: str, ref: str) -> dict:
    for sb in blocks(text, "symbol"):
        if atom(sb, "lib_id") != "Connector_Generic:Conn_01x07":
            continue
        if qprop(sb, "Reference") != ref:
            continue
        return {
            "ref": ref,
            "lib_id": atom(sb, "lib_id"),
            "value": qprop(sb, "Value"),
            "footprint": qprop(sb, "Footprint"),
            "at": first_at(sb),
            "dnp": atom(sb, "dnp"),
        }
    raise ValueError(f"schematic connector {ref} not found")


def exact_no_connect(text: str, x: float, y: float) -> bool:
    pat = re.compile(r"\(no_connect\s+\(at\s+" + re.escape(str(x)) + r"\s+" + re.escape(str(y)) + r"\)")
    return bool(pat.search(text))


def find_slot_size(text: str) -> list[float] | None:
    m = re.search(
        r"trackball_breakout_right:\s*\n(?:.*\n){0,8}?\s*-\s+what:\s+rectangle\s*\n\s+size:\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]",
        text,
    )
    return [float(m.group(1)), float(m.group(2))] if m else None


def near(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    breakout_text = BREAKOUT_PCB.read_text(encoding="utf-8")
    right_pcb_text = RIGHT_PCB.read_text(encoding="utf-8")
    right_sch_text = RIGHT_SCH.read_text(encoding="utf-8")
    ergogen_text = ERGOGEN.read_text(encoding="utf-8")

    breakout_j1 = fp_by_ref(breakout_text, "J1")
    breakout_u2 = fp_by_ref(breakout_text, "U2")
    right_j2 = fp_by_ref(right_pcb_text, "J2")
    right_sch_j2 = schematic_connector(right_sch_text, "J2")
    breakout_edges = board_edge_report(breakout_text)
    slot_size = find_slot_size(ergogen_text)

    breakout_map = pad_map(breakout_j1)
    right_map = pad_map(right_j2)

    checks = {
        "breakout_j1_expected_footprint": breakout_j1["footprint"] == EXPECTED_FOOTPRINT,
        "breakout_j1_on_back_copper": breakout_j1["layer"] == "B.Cu",
        "breakout_j1_at_expected_location": breakout_j1["at"] is not None and near(breakout_j1["at"][0], 118.64) and near(breakout_j1["at"][1], 73.4),
        "breakout_pin_order_exact": all(breakout_map.get(pin) == net for pin, net in EXPECTED_ORDER.items()),
        "breakout_sensor_on_same_side": breakout_u2["layer"] == "B.Cu",
        "breakout_outline_22x25": breakout_edges["bbox"] == [100.0, 50.0, 122.0, 75.0],
        "reference_right_j2_expected_footprint": right_j2["footprint"] == EXPECTED_FOOTPRINT,
        "reference_right_pin_order_exact": all(right_map.get(pin) == net for pin, net in EXPECTED_RIGHT_ORDER.items()),
        "reference_right_schematic_j2_matches": right_sch_j2["footprint"] == EXPECTED_FOOTPRINT,
        "reference_motion_pin_intentionally_nc": exact_no_connect(right_sch_text, 135.89, 87.63),
        "ergogen_pass_through_slot_2x22": slot_size == [2.0, 22.0],
    }

    report = {
        "task": "2C",
        "sources": {
            "breakout_pcb": str(BREAKOUT_PCB.relative_to(ROOT)),
            "reference_right_pcb": str(RIGHT_PCB.relative_to(ROOT)),
            "reference_right_schematic": str(RIGHT_SCH.relative_to(ROOT)),
            "ergogen": str(ERGOGEN.relative_to(ROOT)),
        },
        "breakout": {
            "connector": breakout_j1,
            "sensor": breakout_u2,
            "edge_cuts": breakout_edges,
            "pin_map": breakout_map,
        },
        "reference_right": {
            "connector_pcb": right_j2,
            "connector_schematic": right_sch_j2,
            "pin_map": right_map,
            "motion_pin_3_no_connect": exact_no_connect(right_sch_text, 135.89, 87.63),
        },
        "pass_through_slot_size_mm": slot_size,
        "checks": checks,
    }

    out = json.dumps(report, indent=2, sort_keys=True)
    print(out)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(out + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
