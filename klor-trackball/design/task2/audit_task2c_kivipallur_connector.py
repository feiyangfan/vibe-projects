#!/usr/bin/env python3
"""Task 2C: audit the Kivipallur connector and its Klorball35 mating reference.

The important detail is that the two 1x7 headers intentionally use opposite
pin-number orders when they face each other. This audit records both orders,
proves the signal-for-signal reversed mate, and resolves the pass-through slot.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
BREAKOUT_PCB = ROOT / "klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb"
RIGHT_PCB = ROOT / "klorball35/kicad/klorball35_right/klorball35_right.kicad_pcb"
RIGHT_SCH = ROOT / "klorball35/kicad/klorball35_right/klorball35_right.kicad_sch"
ERGOGEN = ROOT / "klorball35/config.yml"

HEADER_FP = "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"
BREAKOUT_ORDER = {
    "1": "GND", "2": "+3V3", "3": "/MOTION", "4": "/SCK",
    "5": "/MOSI", "6": "/MISO", "7": "/CS",
}
REFERENCE_RIGHT_ORDER = {
    "1": "/CS", "2": "/MISO", "3": "/MOSI", "4": "/SCK",
    "5": "unconnected-(J2-Pin_5-Pad5)", "6": "+3V3", "7": "GND",
}
MATE_PAIRS = [("1", "7"), ("2", "6"), ("3", "5"), ("4", "4"),
              ("5", "3"), ("6", "2"), ("7", "1")]


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
        m = pat.search(text, pos)
        if not m:
            return
        block = balanced(text, m.start())
        yield block
        pos = m.start() + len(block)


def qprop(block: str, name: str) -> str | None:
    m = re.search(r'\(property\s+"' + re.escape(name) + r'"\s+"([^"]*)"', block)
    return m.group(1) if m else None


def atom(block: str, name: str) -> str | None:
    m = re.search(r"\(" + re.escape(name) + r'\s+(?:"([^"]*)"|([^\s()]+))', block)
    return (m.group(1) if m and m.group(1) is not None else m.group(2)) if m else None


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
            "number": h.group(1), "type": h.group(2), "shape": h.group(3),
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
            "ref": ref, "value": qprop(fb, "Value"),
            "footprint": head.group(1) if head else None,
            "layer": atom(fb, "layer"), "at": first_at(fb),
            "pads": parse_pads(fb),
        })
    return out


def fp_by_ref(text: str, ref: str) -> dict:
    found = [fp for fp in footprints(text) if fp["ref"] == ref]
    if len(found) != 1:
        raise ValueError(f"expected one {ref}, found {len(found)}")
    return found[0]


def pad_map(fp: dict) -> dict[str, str | None]:
    return {p["number"]: p["net"] for p in fp["pads"] if p["number"]}


def pad_by_number(fp: dict, number: str) -> dict:
    matches = [p for p in fp["pads"] if p["number"] == number]
    if len(matches) != 1:
        raise ValueError(f"{fp['ref']} pad {number}: expected 1, found {len(matches)}")
    return matches[0]


def global_pad_xy(fp: dict, pad: dict) -> list[float]:
    fx, fy = fp["at"][:2]
    theta = math.radians(fp["at"][2] if len(fp["at"]) > 2 else 0.0)
    px, py = pad["at"][:2]
    # KiCad back-side footprints mirror local Y before parent rotation.
    if fp["layer"] == "B.Cu":
        py = -py
    return [
        fx + px * math.cos(theta) - py * math.sin(theta),
        fy + px * math.sin(theta) + py * math.cos(theta),
    ]


def edge_lines(text: str) -> list[dict]:
    out = []
    for gb in blocks(text, "gr_line"):
        if atom(gb, "layer") != "Edge.Cuts":
            continue
        a, b = xy(gb, "start"), xy(gb, "end")
        if a and b:
            out.append({"start": a, "end": b})
    return out


def line_components(lines: list[dict]) -> list[dict]:
    def key(p: list[float]) -> tuple[float, float]:
        return (round(p[0], 4), round(p[1], 4))

    adjacency: dict[tuple[float, float], list[int]] = defaultdict(list)
    for i, line in enumerate(lines):
        adjacency[key(line["start"])].append(i)
        adjacency[key(line["end"])].append(i)

    unseen = set(range(len(lines)))
    components = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        ids = [seed]
        while queue:
            i = queue.popleft()
            for p in (lines[i]["start"], lines[i]["end"]):
                for j in adjacency[key(p)]:
                    if j in unseen:
                        unseen.remove(j)
                        queue.append(j)
                        ids.append(j)
        pts = [p for i in ids for p in (lines[i]["start"], lines[i]["end"])]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        lengths = sorted(math.dist(lines[i]["start"], lines[i]["end"]) for i in ids)
        components.append({
            "line_ids": ids,
            "line_count": len(ids),
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "center": [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2],
            "lengths": lengths,
        })
    return components


def breakout_edge_report(text: str) -> dict:
    lines = edge_lines(text)
    pts = [p for line in lines for p in (line["start"], line["end"])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return {"line_count": len(lines), "bbox": [min(xs), min(ys), max(xs), max(ys)], "lines": lines}


def slot_candidates(text: str) -> list[dict]:
    result = []
    for comp in line_components(edge_lines(text)):
        if comp["line_count"] != 4:
            continue
        lengths = comp["lengths"]
        if len(lengths) == 4 and abs(lengths[0] - 2.0) < 0.05 and abs(lengths[1] - 2.0) < 0.05 and abs(lengths[2] - 22.0) < 0.05 and abs(lengths[3] - 22.0) < 0.05:
            result.append(comp)
    return result


def schematic_connector(text: str, ref: str) -> dict:
    for sb in blocks(text, "symbol"):
        if atom(sb, "lib_id") == "Connector_Generic:Conn_01x07" and qprop(sb, "Reference") == ref:
            return {
                "ref": ref, "lib_id": atom(sb, "lib_id"), "value": qprop(sb, "Value"),
                "footprint": qprop(sb, "Footprint"), "at": first_at(sb), "dnp": atom(sb, "dnp"),
            }
    raise ValueError(f"schematic connector {ref} not found")


def exact_no_connect(text: str, x: float, y: float) -> bool:
    return bool(re.search(r"\(no_connect\s+\(at\s+" + re.escape(str(x)) + r"\s+" + re.escape(str(y)) + r"\)", text))


def find_slot_size(text: str) -> list[float] | None:
    m = re.search(r"trackball_breakout_right:\s*\n(?:.*\n){0,8}?\s*-\s+what:\s+rectangle\s*\n\s+size:\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]", text)
    return [float(m.group(1)), float(m.group(2))] if m else None


def norm(net: str | None) -> str | None:
    if net is None:
        return None
    return net[1:] if net.startswith("/") else net


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    breakout_text = BREAKOUT_PCB.read_text(encoding="utf-8")
    right_pcb_text = RIGHT_PCB.read_text(encoding="utf-8")
    right_sch_text = RIGHT_SCH.read_text(encoding="utf-8")
    ergogen_text = ERGOGEN.read_text(encoding="utf-8")

    bj1 = fp_by_ref(breakout_text, "J1")
    sensor = fp_by_ref(breakout_text, "U2")
    rj2 = fp_by_ref(right_pcb_text, "J2")
    rsch = schematic_connector(right_sch_text, "J2")
    bmap, rmap = pad_map(bj1), pad_map(rj2)
    bedges = breakout_edge_report(breakout_text)
    slots = slot_candidates(right_pcb_text)
    slot_size = find_slot_size(ergogen_text)

    b_positions = {n: global_pad_xy(bj1, pad_by_number(bj1, n)) for n in BREAKOUT_ORDER}
    r_positions = {n: global_pad_xy(rj2, pad_by_number(rj2, n)) for n in REFERENCE_RIGHT_ORDER}
    b_mid = [(b_positions["1"][0] + b_positions["7"][0]) / 2, (b_positions["1"][1] + b_positions["7"][1]) / 2]
    sensor_xy = sensor["at"][:2]

    mate = []
    mate_ok = True
    for bp, rp in MATE_PAIRS:
        bnet, rnet = bmap.get(bp), rmap.get(rp)
        if bp == "3":
            signal_ok = bnet == "/MOTION" and (rnet or "").startswith("unconnected-(J2-Pin_5")
        else:
            signal_ok = norm(bnet) == norm(rnet)
        mate_ok &= signal_ok
        mate.append({"breakout_pin": int(bp), "breakout_net": bnet, "reference_right_pin": int(rp), "reference_right_net": rnet, "signal_match": signal_ok})

    checks = {
        "breakout_j1_expected_footprint": bj1["footprint"] == HEADER_FP,
        "breakout_j1_back_component_side": bj1["layer"] == "B.Cu" and sensor["layer"] == "B.Cu",
        "breakout_pin_order_exact": bmap == BREAKOUT_ORDER,
        "breakout_outline_22x25": bedges["bbox"] == [100.0, 50.0, 122.0, 75.0],
        "breakout_header_along_trailing_edge": abs(b_mid[0] - sensor_xy[0]) < 0.1 and b_mid[1] > sensor_xy[1],
        "reference_right_j2_expected_footprint": rj2["footprint"] == HEADER_FP,
        "reference_right_j2_front_side": rj2["layer"] == "F.Cu",
        "reference_right_reversed_order_exact": rmap == REFERENCE_RIGHT_ORDER,
        "reversed_mate_signal_for_signal": mate_ok,
        "reference_motion_pin_intentionally_nc": exact_no_connect(right_sch_text, 135.89, 87.63),
        "ergogen_pass_through_slot_2x22": slot_size == [2.0, 22.0],
        "actual_right_pcb_has_one_2x22_slot": len(slots) == 1,
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
            "connector": bj1, "sensor": sensor, "edge_cuts": bedges,
            "pin_map": bmap, "pin_global_xy": b_positions,
            "header_midpoint_xy": b_mid,
            "header_to_sensor_vector_xy": [sensor_xy[0] - b_mid[0], sensor_xy[1] - b_mid[1]],
        },
        "reference_right": {
            "connector_pcb": rj2, "connector_schematic": rsch,
            "pin_map": rmap, "pin_global_xy": r_positions,
            "motion_pin_3_no_connect": exact_no_connect(right_sch_text, 135.89, 87.63),
            "slot_candidates_2x22": slots,
        },
        "mating": {
            "rule": "opposite-facing 1x7 headers mate breakout pin N to keyboard pin 8-N",
            "pairs": mate,
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
