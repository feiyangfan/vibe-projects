#!/usr/bin/env python3
"""Audit the stock KLOR SW22/D22/RGB topology for Task 2A.

This script is intentionally read-only. It parses the checked-in KiCad schematic and
PCB, reports the exact pad/net connectivity around SW22, identifies the colocated
SK6812-class RGB device from source geometry/text, and resolves its immediate data
chain neighbors from shared nets.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PCB = ROOT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
SCH = ROOT / "klor1.4/PCB/klor1_4/klor1_4.kicad_sch"


def balanced_block(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError(f"unterminated S-expression at offset {start}")


def blocks(text: str, token: str) -> Iterable[str]:
    pat = re.compile(r"\(" + re.escape(token) + r"(?=\s|\()")
    pos = 0
    while True:
        m = pat.search(text, pos)
        if not m:
            return
        block = balanced_block(text, m.start())
        yield block
        pos = m.start() + len(block)


def qprop(block: str, name: str) -> str | None:
    m = re.search(r'\(property\s+"' + re.escape(name) + r'"\s+"([^"]*)"', block)
    return m.group(1) if m else None


def first_at(block: str) -> list[float] | None:
    # Footprint/symbol placement is the first shallow-ish (at ...) in its block.
    m = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?\)", block)
    if not m:
        return None
    return [float(x) for x in m.groups() if x is not None]


def atom(block: str, name: str) -> str | None:
    m = re.search(r"\(" + re.escape(name) + r'\s+(?:"([^"]*)"|([^\s()]+))', block)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def parse_pads(fp_block: str) -> list[dict]:
    out = []
    for pb in blocks(fp_block, "pad"):
        m = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pb)
        if not m:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pb)
        pinfunction = re.search(r'\(pinfunction\s+"([^"]*)"\)', pb)
        pintype = re.search(r'\(pintype\s+"([^"]*)"\)', pb)
        at = first_at(pb)
        out.append(
            {
                "number": m.group(1),
                "type": m.group(2),
                "shape": m.group(3),
                "at": at,
                "net_id": int(net.group(1)) if net else None,
                "net": net.group(2) if net else None,
                "pinfunction": pinfunction.group(1) if pinfunction else None,
                "pintype": pintype.group(1) if pintype else None,
            }
        )
    return out


def parse_footprints(text: str) -> list[dict]:
    fps = []
    for fb in blocks(text, "footprint"):
        ref = qprop(fb, "Reference")
        if not ref:
            m = re.search(r'\(fp_text\s+reference\s+"?([^"\s()]+)', fb)
            ref = m.group(1) if m else None
        if not ref:
            continue
        head = re.match(r'\(footprint\s+"([^"]*)"', fb)
        fps.append(
            {
                "ref": ref,
                "value": qprop(fb, "Value"),
                "footprint": head.group(1) if head else None,
                "at": first_at(fb),
                "layer": atom(fb, "layer"),
                "pads": parse_pads(fb),
                "is_rgb_text_match": bool(re.search(r"SK6812|NeoPixel|WS2812", fb, re.I)),
            }
        )
    return fps


def parse_schematic_targets(text: str, refs: set[str]) -> list[dict]:
    result = []
    for sb in blocks(text, "symbol"):
        ref = qprop(sb, "Reference")
        if ref not in refs:
            continue
        result.append(
            {
                "ref": ref,
                "value": qprop(sb, "Value"),
                "footprint": qprop(sb, "Footprint"),
                "lib_id": atom(sb, "lib_id"),
                "unit": int(atom(sb, "unit")) if atom(sb, "unit") and atom(sb, "unit").isdigit() else atom(sb, "unit"),
                "at": first_at(sb),
            }
        )
    return result


def pad_nets(fp: dict) -> list[str]:
    return sorted({p["net"] for p in fp["pads"] if p.get("net")})


def shared_net_index(fps: list[dict]) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for fp in fps:
        for p in fp["pads"]:
            if p.get("net"):
                idx.setdefault(p["net"], []).append(
                    {
                        "ref": fp["ref"],
                        "pad": p["number"],
                        "pinfunction": p.get("pinfunction"),
                    }
                )
    return idx


def distance(a: list[float] | None, b: list[float] | None) -> float | None:
    if not a or not b or len(a) < 2 or len(b) < 2:
        return None
    return math.hypot(a[0] - b[0], a[1] - b[1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    ap.add_argument("--near-mm", type=float, default=30.0)
    args = ap.parse_args()

    pcb_text = PCB.read_text(encoding="utf-8")
    sch_text = SCH.read_text(encoding="utf-8")
    fps = parse_footprints(pcb_text)
    by_ref = {fp["ref"]: fp for fp in fps}
    index = shared_net_index(fps)

    sw = by_ref.get("SW22")
    diode = by_ref.get("D22")
    if not sw or not diode:
        missing = [r for r, obj in (("SW22", sw), ("D22", diode)) if obj is None]
        raise SystemExit(f"missing required PCB references: {', '.join(missing)}")

    nearby = []
    for fp in fps:
        d = distance(sw["at"], fp["at"])
        if d is not None and d <= args.near_mm:
            nearby.append(
                {
                    "ref": fp["ref"],
                    "value": fp["value"],
                    "footprint": fp["footprint"],
                    "at": fp["at"],
                    "distance_from_sw22_mm": round(d, 6),
                    "nets": pad_nets(fp),
                    "is_rgb_text_match": fp["is_rgb_text_match"],
                }
            )
    nearby.sort(key=lambda x: (x["distance_from_sw22_mm"], x["ref"]))

    rgb_candidates = [
        fp for fp in fps
        if fp["is_rgb_text_match"] and distance(sw["at"], fp["at"]) is not None and distance(sw["at"], fp["at"]) <= 12.0
    ]
    rgb_candidates.sort(key=lambda fp: distance(sw["at"], fp["at"]) or 1e9)
    rgb = rgb_candidates[0] if rgb_candidates else None

    def connectivity(fp: dict) -> dict:
        result = {}
        for p in fp["pads"]:
            net = p.get("net")
            result[p["number"]] = {
                "net": net,
                "pinfunction": p.get("pinfunction"),
                "pintype": p.get("pintype"),
                "shared_with": [x for x in index.get(net, []) if x["ref"] != fp["ref"]] if net else [],
            }
        return result

    rgb_chain = None
    if rgb:
        funcs = {str(p.get("pinfunction") or "").upper(): p for p in rgb["pads"]}
        din = funcs.get("DIN")
        dout = funcs.get("DOUT")
        rgb_chain = {
            "ref": rgb["ref"],
            "value": rgb["value"],
            "footprint": rgb["footprint"],
            "at": rgb["at"],
            "distance_from_sw22_mm": round(distance(sw["at"], rgb["at"]) or 0.0, 6),
            "pads": rgb["pads"],
            "din_net": din.get("net") if din else None,
            "dout_net": dout.get("net") if dout else None,
            "din_peers": [x for x in index.get(din.get("net"), []) if x["ref"] != rgb["ref"]] if din and din.get("net") else [],
            "dout_peers": [x for x in index.get(dout.get("net"), []) if x["ref"] != rgb["ref"]] if dout and dout.get("net") else [],
        }

    sw_nets = set(pad_nets(sw))
    d_nets = set(pad_nets(diode))
    report = {
        "task": "2A",
        "sources": {"pcb": str(PCB.relative_to(ROOT)), "schematic": str(SCH.relative_to(ROOT))},
        "schematic_targets": parse_schematic_targets(sch_text, {"SW22", "D22", rgb["ref"] if rgb else ""}),
        "sw22": {**sw, "connectivity": connectivity(sw)},
        "d22": {**diode, "connectivity": connectivity(diode)},
        "sw22_d22_shared_nets": sorted(sw_nets & d_nets),
        "rgb_candidate": rgb_chain,
        "nearby_footprints": nearby,
        "checks": {
            "sw22_found": sw is not None,
            "d22_found": diode is not None,
            "sw22_d22_share_net": bool(sw_nets & d_nets),
            "rgb_candidate_found": rgb is not None,
            "rgb_din_resolved": bool(rgb_chain and rgb_chain.get("din_net")),
            "rgb_dout_resolved": bool(rgb_chain and rgb_chain.get("dout_net")),
        },
    }

    out = json.dumps(report, indent=2, sort_keys=True)
    print(out)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(out + "\n", encoding="utf-8")

    return 0 if all(report["checks"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
