#!/usr/bin/env python3
"""Audit the stock KLOR R34/SW22 removed-key circuit for Task 2A.

Read-only source audit. It parses the checked-in KiCad schematic and PCB and reports:
- SW22 switch + integrated SK6812 pad/net topology
- D22 matrix-diode topology
- immediate RGB data-chain neighbors
- nearby footprints
- local copper segments/vias for all SW22/D22 nets

The output is intended to be reproducible evidence for the Task 2A disposition.
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
    m = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?\)", block)
    if not m:
        return None
    return [float(x) for x in m.groups() if x is not None]


def atom(block: str, name: str) -> str | None:
    m = re.search(r"\(" + re.escape(name) + r'\s+(?:"([^"]*)"|([^\s()]+))', block)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def xy(block: str, name: str) -> list[float] | None:
    m = re.search(r"\(" + re.escape(name) + r"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)", block)
    return [float(m.group(1)), float(m.group(2))] if m else None


def distance(a: list[float] | None, b: list[float] | None) -> float | None:
    if not a or not b or len(a) < 2 or len(b) < 2:
        return None
    return math.hypot(a[0] - b[0], a[1] - b[1])


def absolute_pad_xy(fp_at: list[float] | None, pad_at: list[float] | None) -> list[float] | None:
    if not fp_at or not pad_at:
        return None
    angle = math.radians(fp_at[2] if len(fp_at) > 2 else 0.0)
    x, y = pad_at[0], pad_at[1]
    xr = x * math.cos(angle) - y * math.sin(angle)
    yr = x * math.sin(angle) + y * math.cos(angle)
    return [round(fp_at[0] + xr, 6), round(fp_at[1] + yr, 6)]


def parse_pads(fp_block: str, fp_at: list[float] | None) -> list[dict]:
    out = []
    for pb in blocks(fp_block, "pad"):
        m = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pb)
        if not m:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pb)
        pinfunction = re.search(r'\(pinfunction\s+"([^"]*)"\)', pb)
        pintype = re.search(r'\(pintype\s+"([^"]*)"\)', pb)
        pad_at = first_at(pb)
        out.append(
            {
                "number": m.group(1),
                "type": m.group(2),
                "shape": m.group(3),
                "at": pad_at,
                "absolute_xy": absolute_pad_xy(fp_at, pad_at),
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
        fp_at = first_at(fb)
        fps.append(
            {
                "ref": ref,
                "value": qprop(fb, "Value"),
                "footprint": head.group(1) if head else None,
                "at": fp_at,
                "layer": atom(fb, "layer"),
                "pads": parse_pads(fb, fp_at),
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
        unit = atom(sb, "unit")
        result.append(
            {
                "ref": ref,
                "value": qprop(sb, "Value"),
                "footprint": qprop(sb, "Footprint"),
                "lib_id": atom(sb, "lib_id"),
                "unit": int(unit) if unit and unit.isdigit() else unit,
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


def parse_local_copper(text: str, target_net_ids: set[int], center: list[float], radius: float) -> dict:
    result = {str(n): {"segments": [], "vias": []} for n in sorted(target_net_ids)}
    for sb in blocks(text, "segment"):
        net = atom(sb, "net")
        if not net or not net.isdigit() or int(net) not in target_net_ids:
            continue
        start = xy(sb, "start")
        end = xy(sb, "end")
        if min(distance(center, start) or 1e9, distance(center, end) or 1e9) > radius:
            continue
        result[net]["segments"].append(
            {
                "start": start,
                "end": end,
                "width": float(atom(sb, "width")) if atom(sb, "width") else None,
                "layer": atom(sb, "layer"),
            }
        )
    for vb in blocks(text, "via"):
        net = atom(vb, "net")
        if not net or not net.isdigit() or int(net) not in target_net_ids:
            continue
        at = first_at(vb)
        if distance(center, at) is None or distance(center, at) > radius:
            continue
        result[net]["vias"].append(
            {
                "at": at[:2],
                "size": float(atom(vb, "size")) if atom(vb, "size") else None,
                "drill": float(atom(vb, "drill")) if atom(vb, "drill") else None,
                "layers": re.findall(r'"([FB]\.Cu)"', vb),
            }
        )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    ap.add_argument("--near-mm", type=float, default=30.0)
    ap.add_argument("--copper-radius-mm", type=float, default=18.0)
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

    # In this KLOR source the SK6812 is integrated into the SWxx footprint/symbol.
    rgb = sw if sw["is_rgb_text_match"] else None

    def connectivity(fp: dict) -> dict:
        result = {}
        for p in fp["pads"]:
            if not p["number"]:
                continue
            net = p.get("net")
            result.setdefault(p["number"], {
                "net": net,
                "net_id": p.get("net_id"),
                "pinfunction": p.get("pinfunction"),
                "pintype": p.get("pintype"),
                "absolute_pad_xy": [],
                "shared_with": [x for x in index.get(net, []) if x["ref"] != fp["ref"]] if net else [],
            })
            if p.get("absolute_xy") not in result[p["number"]]["absolute_pad_xy"]:
                result[p["number"]]["absolute_pad_xy"].append(p.get("absolute_xy"))
        return result

    rgb_chain = None
    if rgb:
        funcs = {}
        for p in rgb["pads"]:
            fn = str(p.get("pinfunction") or "").upper()
            if fn and fn not in funcs:
                funcs[fn] = p
        din = funcs.get("DIN")
        dout = funcs.get("DOUT")
        rgb_chain = {
            "ref": rgb["ref"],
            "integrated_in_switch_footprint": True,
            "din_net": din.get("net") if din else None,
            "din_net_id": din.get("net_id") if din else None,
            "dout_net": dout.get("net") if dout else None,
            "dout_net_id": dout.get("net_id") if dout else None,
            "din_peers": [x for x in index.get(din.get("net"), []) if x["ref"] != rgb["ref"]] if din and din.get("net") else [],
            "dout_peers": [x for x in index.get(dout.get("net"), []) if x["ref"] != rgb["ref"]] if dout and dout.get("net") else [],
        }

    sw_conn = connectivity(sw)
    d_conn = connectivity(diode)
    target_net_ids = {
        int(p["net_id"])
        for p in sw["pads"] + diode["pads"]
        if p.get("net_id") is not None
    }
    local_copper = parse_local_copper(pcb_text, target_net_ids, sw["at"][:2], args.copper_radius_mm)

    net_names = {}
    for p in sw["pads"] + diode["pads"]:
        if p.get("net_id") is not None and p.get("net"):
            net_names[str(p["net_id"])] = p["net"]

    # Source-backed disposition. D22 becomes a one-ended row3 stub when SW22 is
    # removed; the derivative therefore removes both SW22 and D22. The RGB unit is
    # SW22 unit 2 / pads 1-4, so bypass is SW13 DOUT directly to SW14 DIN.
    disposition = {
        "logical_key": "R34",
        "logical_key_is_component_reference": False,
        "remove_footprints": ["SW22", "D22"],
        "matrix": {
            "sw22_column_net": sw_conn.get("5", {}).get("net"),
            "sw22_to_diode_net": sw_conn.get("6", {}).get("net"),
            "d22_anode_net": d_conn.get("2", {}).get("net"),
            "d22_cathode_net": d_conn.get("1", {}).get("net"),
            "action": "Delete SW22 and D22. Do not bridge matrix nets. Remove the obsolete Net-(D22-A) local copper stub while preserving the col1 and row3 trunks.",
        },
        "rgb": {
            "device": "SW22 unit 2 / integrated SK6812 pads 1-4",
            "incoming": "SW13 DOUT",
            "incoming_net": rgb_chain.get("din_net") if rgb_chain else None,
            "outgoing": "SW14 DIN",
            "outgoing_net": rgb_chain.get("dout_net") if rgb_chain else None,
            "bypass": "Connect SW13 DOUT directly to SW14 DIN in copper; delete the former SW22 DIN/DOUT branches. No logical VCC/GND bypass is required, but local rail continuity must be preserved when deleting SW22 copper.",
        },
    }

    report = {
        "task": "2A",
        "sources": {"pcb": str(PCB.relative_to(ROOT)), "schematic": str(SCH.relative_to(ROOT))},
        "schematic_targets": parse_schematic_targets(sch_text, {"SW22", "D22"}),
        "sw22": {**sw, "connectivity": sw_conn},
        "d22": {**diode, "connectivity": d_conn},
        "sw22_d22_shared_nets": sorted(set(pad_nets(sw)) & set(pad_nets(diode))),
        "rgb_chain": rgb_chain,
        "nearby_footprints": nearby,
        "local_copper_net_names": net_names,
        "local_copper": local_copper,
        "disposition": disposition,
        "checks": {
            "sw22_found": sw is not None,
            "d22_found": diode is not None,
            "sw22_d22_share_net": bool(set(pad_nets(sw)) & set(pad_nets(diode))),
            "rgb_is_integrated_in_sw22": bool(rgb is sw),
            "rgb_din_resolved": bool(rgb_chain and rgb_chain.get("din_net")),
            "rgb_dout_resolved": bool(rgb_chain and rgb_chain.get("dout_net")),
            "matrix_column_resolved": sw_conn.get("5", {}).get("net") == "col1",
            "matrix_row_resolved": d_conn.get("1", {}).get("net") == "row3",
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
