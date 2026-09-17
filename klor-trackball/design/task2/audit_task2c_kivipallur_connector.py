#!/usr/bin/env python3
"""Task 2C: source-audit the Kivipallur connector/mating contract.

Klorball35 uses a 2x22 mm Cmts.User rectangle as the breakout insertion guide;
it is not itself a fabricated Edge.Cuts slot. Task 3 must create the actual
KLOR pass-through/clearance at the locked Task 1 datum.
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
RIGHT_ORDER = {
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
    return (m.group(1) if m and m.group(1) is not None else m.group(2)) if m else None


def at(block: str) -> list[float] | None:
    m = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?\)", block)
    return [float(v) for v in m.groups() if v is not None] if m else None


def point(block: str, token: str) -> list[float] | None:
    m = re.search(r"\(" + re.escape(token) + r"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)", block)
    return [float(m.group(1)), float(m.group(2))] if m else None


def parse_pads(fp: str) -> list[dict]:
    result = []
    for pb in blocks(fp, "pad"):
        h = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pb)
        if not h:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pb)
        result.append({
            "number": h.group(1), "type": h.group(2), "shape": h.group(3),
            "at": at(pb), "net_id": int(net.group(1)) if net else None,
            "net": net.group(2) if net else None,
        })
    return result


def footprints(text: str) -> list[dict]:
    result = []
    for fb in blocks(text, "footprint"):
        ref = qprop(fb, "Reference")
        if not ref:
            continue
        head = re.match(r'\(footprint\s+"([^"]*)"', fb)
        result.append({
            "ref": ref, "value": qprop(fb, "Value"),
            "footprint": head.group(1) if head else None,
            "layer": atom(fb, "layer"), "at": at(fb), "pads": parse_pads(fb),
        })
    return result


def fp(text: str, ref: str) -> dict:
    found = [row for row in footprints(text) if row["ref"] == ref]
    if len(found) != 1:
        raise ValueError(f"expected one {ref}, found {len(found)}")
    return found[0]


def pad_map(footprint: dict) -> dict[str, str | None]:
    return {p["number"]: p["net"] for p in footprint["pads"] if p["number"]}


def pad(footprint: dict, number: str) -> dict:
    found = [p for p in footprint["pads"] if p["number"] == number]
    if len(found) != 1:
        raise ValueError(f"{footprint['ref']} pad {number}: expected 1, found {len(found)}")
    return found[0]


def global_pad_xy(footprint: dict, p: dict) -> list[float]:
    """KiCad board XY uses screen-style +Y-down rotation convention."""
    fx, fy = footprint["at"][:2]
    theta = math.radians(footprint["at"][2] if len(footprint["at"]) > 2 else 0.0)
    px, py = p["at"][:2]
    return [
        fx + px * math.cos(theta) + py * math.sin(theta),
        fy - px * math.sin(theta) + py * math.cos(theta),
    ]


def lines(text: str, layer: str) -> list[dict]:
    result = []
    for gb in blocks(text, "gr_line"):
        if atom(gb, "layer") != layer:
            continue
        a, b = point(gb, "start"), point(gb, "end")
        if a and b:
            result.append({"start": a, "end": b})
    return result


def line_components(rows: list[dict]) -> list[dict]:
    def key(p: list[float]) -> tuple[float, float]:
        return (round(p[0], 4), round(p[1], 4))
    adjacency: dict[tuple[float, float], list[int]] = defaultdict(list)
    for i, row in enumerate(rows):
        adjacency[key(row["start"])].append(i)
        adjacency[key(row["end"])].append(i)
    unseen = set(range(len(rows)))
    result = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        ids = [seed]
        while queue:
            i = queue.popleft()
            for p in (rows[i]["start"], rows[i]["end"]):
                for j in adjacency[key(p)]:
                    if j in unseen:
                        unseen.remove(j)
                        queue.append(j)
                        ids.append(j)
        pts = [p for i in ids for p in (rows[i]["start"], rows[i]["end"])]
        lengths = sorted(math.dist(rows[i]["start"], rows[i]["end"]) for i in ids)
        longest = max((rows[i] for i in ids), key=lambda r: math.dist(r["start"], r["end"]))
        dx = longest["end"][0] - longest["start"][0]
        dy = longest["end"][1] - longest["start"][1]
        mag = math.hypot(dx, dy)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        result.append({
            "line_count": len(ids), "lengths": lengths,
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "center": [(min(xs)+max(xs))/2, (min(ys)+max(ys))/2],
            "long_axis_unit": [dx/mag, dy/mag] if mag else None,
        })
    return result


def guide_candidates(text: str) -> list[dict]:
    result = []
    for comp in line_components(lines(text, "Cmts.User")):
        ls = comp["lengths"]
        if comp["line_count"] == 4 and len(ls) == 4 and abs(ls[0]-2)<0.05 and abs(ls[1]-2)<0.05 and abs(ls[2]-22)<0.05 and abs(ls[3]-22)<0.05:
            result.append(comp)
    return result


def edge_bbox(text: str) -> list[float]:
    pts = [p for row in lines(text, "Edge.Cuts") for p in (row["start"], row["end"])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def schematic_connector(text: str, ref: str) -> dict:
    for sb in blocks(text, "symbol"):
        if atom(sb, "lib_id") == "Connector_Generic:Conn_01x07" and qprop(sb, "Reference") == ref:
            return {"ref": ref, "footprint": qprop(sb, "Footprint"), "at": at(sb), "dnp": atom(sb, "dnp")}
    raise ValueError(f"schematic connector {ref} not found")


def no_connect(text: str, x: float, y: float) -> bool:
    return bool(re.search(r"\(no_connect\s+\(at\s+" + re.escape(str(x)) + r"\s+" + re.escape(str(y)) + r"\)", text))


def norm(net: str | None) -> str | None:
    return net[1:] if net and net.startswith("/") else net


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    bt = BREAKOUT_PCB.read_text(encoding="utf-8")
    rt = RIGHT_PCB.read_text(encoding="utf-8")
    st = RIGHT_SCH.read_text(encoding="utf-8")
    et = ERGOGEN.read_text(encoding="utf-8")

    bj1, u2, rj2 = fp(bt, "J1"), fp(bt, "U2"), fp(rt, "J2")
    rsch = schematic_connector(st, "J2")
    bmap, rmap = pad_map(bj1), pad_map(rj2)
    bpos = {n: global_pad_xy(bj1, pad(bj1, n)) for n in BREAKOUT_ORDER}
    rpos = {n: global_pad_xy(rj2, pad(rj2, n)) for n in RIGHT_ORDER}
    bmid = [(bpos["1"][0]+bpos["7"][0])/2, (bpos["1"][1]+bpos["7"][1])/2]
    rmid = [(rpos["1"][0]+rpos["7"][0])/2, (rpos["1"][1]+rpos["7"][1])/2]
    guides = guide_candidates(rt)

    mate = []
    mate_ok = True
    for bp, rp in MATE_PAIRS:
        bn, rn = bmap[bp], rmap[rp]
        ok = (bn == "/MOTION" and rn.startswith("unconnected-(J2-Pin_5")) if bp == "3" else norm(bn) == norm(rn)
        mate_ok &= ok
        mate.append({"breakout_pin": int(bp), "breakout_net": bn, "right_pin": int(rp), "right_net": rn, "signal_match": ok})

    row_vec = [rpos["7"][0]-rpos["1"][0], rpos["7"][1]-rpos["1"][1]]
    row_mag = math.hypot(*row_vec)
    row_unit = [row_vec[0]/row_mag, row_vec[1]/row_mag]
    guide = guides[0] if len(guides) == 1 else None
    guide_alignment = None if not guide else abs(row_unit[0]*guide["long_axis_unit"][0] + row_unit[1]*guide["long_axis_unit"][1])
    guide_offset = None if not guide else [rmid[0]-guide["center"][0], rmid[1]-guide["center"][1]]
    guide_offset_mm = None if not guide else math.dist(rmid, guide["center"])

    config_size = bool(re.search(r"trackball_breakout_right:\s*\n(?:.*\n){0,8}?\s*-\s+what:\s+rectangle\s*\n\s+size:\s*\[\s*2(?:\.0)?\s*,\s*22(?:\.0)?\s*\]", et))
    config_layer = bool(re.search(r"-\s+outline:\s+trackball_breakout_right\s*\n\s+layer:\s+Cmts\.User", et))

    checks = {
        "breakout_j1_expected_footprint": bj1["footprint"] == HEADER_FP,
        "breakout_component_side_is_back": bj1["layer"] == "B.Cu" and u2["layer"] == "B.Cu",
        "breakout_pin_order_exact": bmap == BREAKOUT_ORDER,
        "breakout_outline_22x25": edge_bbox(bt) == [100.0, 50.0, 122.0, 75.0],
        "breakout_header_is_trailing_edge": bmid[1] > u2["at"][1] and abs(bmid[0]-u2["at"][0]) < 0.1,
        "right_j2_expected_footprint": rj2["footprint"] == HEADER_FP and rsch["footprint"] == HEADER_FP,
        "right_j2_front_side": rj2["layer"] == "F.Cu",
        "right_reversed_pin_order_exact": rmap == RIGHT_ORDER,
        "opposite_facing_mate_signal_for_signal": mate_ok,
        "motion_reference_is_nc": no_connect(st, 135.89, 87.63),
        "ergogen_guide_is_2x22": config_size,
        "ergogen_guide_layer_is_cmts_user": config_layer,
        "right_pcb_has_one_2x22_cmts_user_guide": len(guides) == 1,
        "right_header_parallel_to_guide_long_axis": guide_alignment is not None and guide_alignment > 0.9999,
        "right_header_to_guide_offset_locked": guide_offset_mm is not None and abs(guide_offset_mm - 4.61362) < 0.01,
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
            "connector": bj1, "sensor": u2, "pin_map": bmap, "pin_global_xy": bpos,
            "header_midpoint_xy": bmid, "edge_bbox": edge_bbox(bt),
            "header_to_sensor_vector_xy": [u2["at"][0]-bmid[0], u2["at"][1]-bmid[1]],
        },
        "reference_right": {
            "connector": rj2, "schematic": rsch, "pin_map": rmap, "pin_global_xy": rpos,
            "header_midpoint_xy": rmid, "pin1_to_pin7_unit": row_unit,
            "motion_nc": no_connect(st, 135.89, 87.63), "cmts_user_guides_2x22": guides,
            "header_to_guide_offset_xy": guide_offset, "header_to_guide_offset_mm": guide_offset_mm,
            "guide_axis_alignment_abs_dot": guide_alignment,
        },
        "mating": {
            "rule": "opposite-facing headers mate breakout pin N to keyboard pin 8-N",
            "pairs": mate, "motion_revision1": "NC",
        },
        "reference_guide": {
            "size_mm": [2.0, 22.0], "layer": "Cmts.User", "fabricated_cutout": False,
            "task3_action": "create real KLOR pass-through/clearance at locked Task 1 slot datum",
        },
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
