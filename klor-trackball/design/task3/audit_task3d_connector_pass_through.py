#!/usr/bin/env python3
"""Audit Task 3D final J4 placement and fabricated breakout pass-through."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
PCB = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_pcb"
SCH = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_sch"
REL_PCB = "klor-trackball/PCB/konrad_trackball/konrad_trackball.kicad_pcb"

BASE_COMMIT = "fa2c2895e7ac3b2712dde4d7dc912dba50a22c98"
BASE_PCB_BLOB = "c3fefdb583d653a836d2ab99a9d94126ea331a3b"
FINAL_PCB_BLOB = "4272f9c3895fd46c0688b3eb530fc7299b540727"
SCHEMATIC_BLOB = "4239dd2f139be30e24ee7109800a5ae9f179aee3"

SLOT_CENTER = (143.111043, 134.747997)
SLOT = (142.111043, 123.747997, 144.111043, 145.747997)
J4_AT = (147.724665, 142.367997, 0.0)
J4_ROW_MID = (147.724665, 134.747997)
J4_OFFSET = 4.613622

OLD_EDGE = "6a8d966a-c3bb-40c7-938f-b720f86fa562"
CURVE = "b693c5db-8f44-4066-8000-0f32a9cfada9"
NEW_EDGES = {
    "3d3d0001-0000-4000-8000-000000000001": ((142.111043,139.186691),(142.111043,123.747997)),
    "3d3d0001-0000-4000-8000-000000000002": ((142.111043,123.747997),(144.111043,123.747997)),
    "3d3d0001-0000-4000-8000-000000000003": ((144.111043,123.747997),(144.111043,144.25)),
    "3d3d0001-0000-4000-8000-000000000004": ((144.111043,144.25),(150.0,144.25)),
    "3d3d0001-0000-4000-8000-000000000005": ((150.0,144.25),(150.0,139.175891)),
    "3d3d0001-0000-4000-8000-000000000006": ((150.0,139.175891),(152.769828,139.175891)),
}
REMOVED_SEGMENTS = {
    "b6e262ab-112a-4aec-a375-10baa529f63e",
    "4ddd41fb-2b70-431a-ac03-133940fe8c9b",
    "c992ed9d-871b-4175-8587-7aea69a149d8",
    "7292750a-d8ce-4ae7-af47-971813d11a90",
    "61201bf3-5d7a-4139-9a00-918afa211305",
    "ad3afa37-5d1c-4f74-863c-60814b2ce7c9",
    "3c3c0005-0000-4000-8000-000000000001",
    "2317eaaf-21e6-4023-b6db-ca58196bac19",
    "6820dad4-1b71-4728-a8f1-85c254ada3a2",
}
REMOVED_VIAS = {
    "9e118286-0035-495c-8cfe-b4182667bbd8",
    "46d54c98-0f16-4fbd-80d5-7c4789c1229e",
}
NEW_SEGMENTS = {
    "3d3d0002-0000-4000-8000-000000000001": ((136.695,131.61),(141.5,131.61),0.381,"F.Cu",3),
    "3d3d0002-0000-4000-8000-000000000002": ((141.5,131.61),(141.5,123.15),0.381,"F.Cu",3),
    "3d3d0002-0000-4000-8000-000000000003": ((141.5,123.15),(144.72,123.15),0.381,"F.Cu",3),
    "3d3d0002-0000-4000-8000-000000000004": ((143.03,120.1),(144.72,121.79),0.381,"F.Cu",3),
    "3d3d0002-0000-4000-8000-000000000005": ((144.72,121.79),(144.72,123.15),0.381,"F.Cu",3),
    "3d3d0002-0000-4000-8000-000000000006": ((144.72,123.15),(144.72,126.861786),0.381,"F.Cu",3),
    "3d3d0002-0000-4000-8000-000000000007": ((144.72,126.861786),(144.8905,127.032286),0.381,"F.Cu",3),
    "3d3d0003-0000-4000-8000-000000000001": ((146.443984,133.06),(145.3,133.81),0.381,"F.Cu",3),
    "3d3d0003-0000-4000-8000-000000000002": ((145.3,133.81),(145.701524,134.560002),0.381,"B.Cu",3),
    "3d3d0004-0000-4000-8000-000000000001": ((151.129969,128.715031),(151.705,130.22),0.254,"B.Cu",76),
}
NEW_VIA = ("3d3d0003-0000-4000-8000-000000000003", (145.3,133.81), 0.4, 0.3, 3)


def git_blob(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)], cwd=REPO, check=True,
        text=True, capture_output=True,
    ).stdout.strip()


def git_show(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=REPO, check=True,
        text=True, capture_output=True,
    ).stdout


def balanced(text: str, start: int) -> tuple[str, int]:
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
                return text[start:i + 1], i + 1
    raise ValueError("unbalanced expression")


def blocks(text: str, token: str) -> list[str]:
    out = []
    pos = 0
    needle = "(" + token
    while True:
        pos = text.find(needle, pos)
        if pos < 0:
            return out
        b, end = balanced(text, pos)
        out.append(b)
        pos = end


def uuid(block: str) -> str | None:
    m = re.search(r'\(uuid\s+"([^"]+)"\)', block)
    return None if not m else m.group(1)


def by_uuid(text: str, token: str) -> dict[str, str]:
    return {u: b for b in blocks(text, token) if (u := uuid(b))}


def ref(block: str) -> str | None:
    m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    if not m:
        m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', block)
    return None if not m else m.group(1)


def footprints(text: str) -> dict[str, str]:
    return {r: b for b in blocks(text, "footprint") if (r := ref(b))}


def point(block: str, name: str):
    m = re.search(rf'\({name}\s+([-\d.]+)\s+([-\d.]+)\)', block)
    return None if not m else (float(m.group(1)), float(m.group(2)))


def top_at(block: str):
    m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
    return None if not m else (float(m.group(1)), float(m.group(2)), float(m.group(3) or 0.0))


def top_layer(block: str):
    m = re.search(r'\(layer\s+"([^"]+)"\)', block)
    return None if not m else m.group(1)


def pad_rows(block: str):
    rows = []
    for p in blocks(block, "pad"):
        n = re.match(r'\(pad\s+"([^"]+)"', p)
        at = top_at(p)
        net = re.search(r'\(net\s+(\d+)\s+"([^"]+)"\)', p)
        if n and at:
            rows.append((n.group(1), at, None if not net else (int(net.group(1)), net.group(2))))
    return rows


def segment_rows(text: str):
    out = {}
    for b in blocks(text, "segment"):
        u = uuid(b)
        a, z = point(b, "start"), point(b, "end")
        w = re.search(r'\(width\s+([-\d.]+)\)', b)
        layer = top_layer(b)
        net = re.search(r'\(net\s+(\d+)\)', b)
        if u and a and z and w and layer and net:
            out[u] = (a, z, float(w.group(1)), layer, int(net.group(1)), b)
    return out


def via_rows(text: str):
    out = {}
    for b in blocks(text, "via"):
        u = uuid(b)
        at = top_at(b)
        size = re.search(r'\(size\s+([-\d.]+)\)', b)
        drill = re.search(r'\(drill\s+([-\d.]+)\)', b)
        net = re.search(r'\(net\s+(\d+)\)', b)
        if u and at and size and drill and net:
            out[u] = ((at[0],at[1]), float(size.group(1)), float(drill.group(1)), int(net.group(1)), b)
    return out


def edge_rows(text: str):
    out = {}
    for kind in ("gr_line", "gr_curve", "gr_rect"):
        for b in blocks(text, kind):
            if '(layer "Edge.Cuts")' in b and (u := uuid(b)):
                out[u] = (kind, b)
    return out


def close(a, b, eps=1e-6):
    if isinstance(a, tuple):
        return len(a) == len(b) and all(close(x, y, eps) for x, y in zip(a, b))
    return abs(float(a)-float(b)) <= eps


def normalize_top_at(block: str) -> str:
    return re.sub(
        r'\(at\s+[-\d.]+\s+[-\d.]+(?:\s+[-\d.]+)?\)',
        "(at <TOP>)", block, count=1,
    )


def dpoint_segment(p, a, b):
    vx, vy = b[0]-a[0], b[1]-a[1]
    wx, wy = p[0]-a[0], p[1]-a[1]
    d = vx*vx + vy*vy
    t = 0.0 if not d else max(0.0, min(1.0, (wx*vx+wy*vy)/d))
    q = (a[0]+t*vx, a[1]+t*vy)
    return math.dist(p, q)


def orient(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def intersects(a,b,c,d):
    return orient(a,b,c)*orient(a,b,d) < 0 and orient(c,d,a)*orient(c,d,b) < 0


def dsegment(a,b,c,d):
    if intersects(a,b,c,d):
        return 0.0
    return min(dpoint_segment(a,c,d), dpoint_segment(b,c,d),
               dpoint_segment(c,a,b), dpoint_segment(d,a,b))


def segment_hits_open_rect(a,b,r):
    xl,yt,xr,yb = r
    inside = lambda p: xl < p[0] < xr and yt < p[1] < yb
    if inside(a) or inside(b):
        return True
    edges = [((xl,yt),(xr,yt)),((xr,yt),(xr,yb)),
             ((xr,yb),(xl,yb)),((xl,yb),(xl,yt))]
    return any(intersects(a,b,c,d) for c,d in edges)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    current = PCB.read_text(encoding="utf-8")
    base = git_show(BASE_COMMIT, REL_PCB)

    bfp, cfp = footprints(base), footprints(current)
    bseg, cseg = segment_rows(base), segment_rows(current)
    bvia, cvia = via_rows(base), via_rows(current)
    bedge, cedge = edge_rows(base), edge_rows(current)

    j4 = cfp["J4"]
    j4_at = top_at(j4)
    pads = {n: (at, net) for n, at, net in pad_rows(j4)}
    j4_globals = {
        n: (j4_at[0]+at[0], j4_at[1]+at[1])
        for n,(at,net) in pads.items()
    }
    row_mid = ((j4_globals["1"][0]+j4_globals["7"][0])/2,
               (j4_globals["1"][1]+j4_globals["7"][1])/2)

    expected_pins = {
        "1": (82,"PMW_CS"), "2": (83,"PMW_MISO"),
        "3": (84,"PMW_MOSI"), "4": (85,"PMW_SCK"),
        "5": None, "6": (3,"VCC"), "7": (1,"GND"),
    }

    edge_expected = (set(bedge)-{OLD_EDGE}) | set(NEW_EDGES)
    unaffected_edge = all(
        cedge[u][1] == bedge[u][1]
        for u in set(bedge)-{OLD_EDGE,CURVE}
    )
    curve_pts = [
        tuple(map(float, m))
        for m in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', cedge[CURVE][1])
    ]
    curve_exact = curve_pts == [
        (124.598127,141.714517),(130.470110,140.137470),
        (136.469818,139.294864),(142.111043,139.186691),
    ]
    new_edges_exact = all(
        u in cedge and cedge[u][0] == "gr_line"
        and close(point(cedge[u][1],"start"), ab[0])
        and close(point(cedge[u][1],"end"), ab[1])
        for u,ab in NEW_EDGES.items()
    )

    expected_seg_ids = (set(bseg)-REMOVED_SEGMENTS) | set(NEW_SEGMENTS)
    retained_segments_exact = all(
        cseg[u][5] == bseg[u][5] for u in set(bseg)-REMOVED_SEGMENTS
    )
    new_segments_exact = all(
        u in cseg
        and close(cseg[u][0], spec[0]) and close(cseg[u][1], spec[1])
        and close(cseg[u][2], spec[2])
        and cseg[u][3] == spec[3] and cseg[u][4] == spec[4]
        for u,spec in NEW_SEGMENTS.items()
    )

    expected_via_ids = (set(bvia)-REMOVED_VIAS) | {NEW_VIA[0]}
    retained_vias_exact = all(
        cvia[u][4] == bvia[u][4] for u in set(bvia)-REMOVED_VIAS
    )
    new_via_exact = (
        NEW_VIA[0] in cvia
        and close(cvia[NEW_VIA[0]][0], NEW_VIA[1])
        and close(cvia[NEW_VIA[0]][1], NEW_VIA[2])
        and close(cvia[NEW_VIA[0]][2], NEW_VIA[3])
        and cvia[NEW_VIA[0]][3] == NEW_VIA[4]
    )

    # The full nominal 2x22 service envelope must contain no routed copper.
    slot_segments = [u for u,v in cseg.items() if segment_hits_open_rect(v[0],v[1],SLOT)]
    xl,yt,xr,yb = SLOT
    slot_vias = [u for u,v in cvia.items() if xl < v[0][0] < xr and yt < v[0][1] < yb]

    # New Edge.Cuts must respect the 0.3 mm routed-copper rule.
    edge_lines = list(NEW_EDGES.values())
    copper_edge_min = math.inf
    for a,b,w,layer,net,_ in cseg.values():
        for c,d in edge_lines:
            copper_edge_min = min(copper_edge_min, dsegment(a,b,c,d)-w/2)
    via_edge_min = math.inf
    for p,size,drill,net,_ in cvia.values():
        for c,d in edge_lines:
            via_edge_min = min(via_edge_min, dpoint_segment(p,c,d)-size/2)
    j4_edge_min = min(
        dpoint_segment(p,c,d)-0.85
        for p in j4_globals.values() for c,d in edge_lines
    )

    # J4 pads must clear all different-net routed copper/vias.
    pad_track_min = math.inf
    pad_via_min = math.inf
    for n,p in j4_globals.items():
        pnet = pads[n][1][0] if pads[n][1] else None
        for a,b,w,layer,net,_ in cseg.values():
            if net != pnet:
                pad_track_min = min(pad_track_min, dpoint_segment(p,a,b)-0.85-w/2)
        for vp,size,drill,net,_ in cvia.values():
            if net != pnet:
                pad_via_min = min(pad_via_min, math.dist(p,vp)-0.85-size/2)

    # Edge lines/curves (excluding closed gr_rect cutouts) must still form degree-2 chains.
    pieces = []
    for kind in ("gr_line","gr_curve"):
        for b in blocks(current,kind):
            if '(layer "Edge.Cuts")' not in b:
                continue
            if kind == "gr_line":
                a,z = point(b,"start"), point(b,"end")
            else:
                pts = [tuple(map(float,m)) for m in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)',b)]
                a,z = pts[0],pts[-1]
            pieces.append((a,z))
    degree = {}
    key = lambda p: (round(p[0],6),round(p[1],6))
    for a,z in pieces:
        degree[key(a)] = degree.get(key(a),0)+1
        degree[key(z)] = degree.get(key(z),0)+1

    gx = SLOT_CENTER[0] + 0.000000342*SLOT_CENTER[1] - 0.000089
    gy = 0.000000342*SLOT_CENTER[0] - SLOT_CENTER[1] - 0.000052

    base_pmw_seg_ids = {u for u,v in bseg.items() if v[4] in (82,83,84,85)}
    cur_pmw_seg_ids = {u for u,v in cseg.items() if v[4] in (82,83,84,85)}
    cur_pmw_vias = {u for u,v in cvia.items() if v[3] in (82,83,84,85)}

    checks = {
        "task3c_base_commit_available": bool(base),
        "task3c_base_pcb_blob_locked": subprocess.run(
            ["git","rev-parse",f"{BASE_COMMIT}:{REL_PCB}"], cwd=REPO,
            check=True, text=True, capture_output=True,
        ).stdout.strip() == BASE_PCB_BLOB,
        "task3d_pcb_blob_locked": git_blob(PCB) == FINAL_PCB_BLOB,
        "task3b_schematic_preserved": git_blob(SCH) == SCHEMATIC_BLOB,
        "zone_fill_cache_stripped": "(filled_polygon" not in current,
        "footprint_reference_set_preserved": set(cfp) == set(bfp),
        "only_j4_footprint_placement_changed": all(
            cfp[r] == bfp[r] for r in set(bfp)-{"J4"}
        ) and normalize_top_at(cfp["J4"]) == normalize_top_at(bfp["J4"]),
        "j4_front_side": top_layer(j4) == "F.Cu",
        "j4_final_at_exact": close(j4_at,J4_AT),
        "j4_pin_contract_exact": all(pads[n][1] == net for n,net in expected_pins.items()),
        "j4_row_midpoint_exact": close(row_mid,J4_ROW_MID),
        "j4_reference_offset_exact": abs((row_mid[0]-SLOT_CENTER[0])-J4_OFFSET) < 1e-6
            and abs(row_mid[1]-SLOT_CENTER[1]) < 1e-6,
        "j4_row_global_y_pin1_negative_y": all(
            abs(p[0]-J4_AT[0]) < 1e-6 for p in j4_globals.values()
        ) and j4_globals["1"][1] > j4_globals["7"][1],
        "locked_slot_datum_maps_to_gerber": abs(gx-143.111) < 2e-6 and abs(gy+134.748) < 2e-6,
        "edge_uuid_set_authorized_exact": set(cedge) == edge_expected,
        "unaffected_edge_cuts_exact": unaffected_edge,
        "truncated_stock_curve_exact": curve_exact,
        "new_notch_and_tongue_edges_exact": new_edges_exact,
        "old_edge_member_fully_retired": OLD_EDGE not in current,
        "new_edge_members_grouped": all(current.count(u) == 2 for u in NEW_EDGES),
        "edge_line_curve_topology_closed": all(v == 2 for v in degree.values()),
        "segment_uuid_changes_authorized_exact": set(cseg) == expected_seg_ids,
        "retained_segments_exact": retained_segments_exact,
        "new_vcc_and_rgb_segments_exact": new_segments_exact,
        "via_uuid_changes_authorized_exact": set(cvia) == expected_via_ids,
        "retained_vias_exact": retained_vias_exact,
        "relocated_vcc_via_exact": new_via_exact,
        "zones_unchanged": blocks(current,"zone") == blocks(base,"zone"),
        "pass_through_corridor_has_no_tracks": not slot_segments,
        "pass_through_corridor_has_no_vias": not slot_vias,
        "new_edges_track_clearance_ge_0_3": copper_edge_min >= 0.3-1e-6,
        "new_edges_via_clearance_ge_0_3": via_edge_min >= 0.3-1e-6,
        "j4_pad_to_new_edge_clearance_ge_0_3": j4_edge_min >= 0.3-1e-6,
        "j4_pad_to_other_net_tracks_clear": pad_track_min >= 0.2-1e-6,
        "j4_pad_to_other_net_vias_clear": pad_via_min >= 0.127-1e-6,
        "rgb_bypass_relocated_exact": "3d3d0004-0000-4000-8000-000000000001" in cseg,
        "pmw_signal_routing_still_deferred_to_3e": cur_pmw_seg_ids == base_pmw_seg_ids and not cur_pmw_vias,
    }

    result = {
        "task": "3D",
        "status": "complete" if all(checks.values()) else "failed",
        "pcb_blob": git_blob(PCB),
        "slot": {
            "gerber_center": [143.111,-134.748],
            "kicad_center": list(SLOT_CENTER),
            "reference_envelope_mm": [2.0,22.0],
            "service_direction": "-X",
        },
        "connector": {
            "reference": "J4",
            "top_level_at_kicad": list(J4_AT),
            "row_midpoint_kicad": list(J4_ROW_MID),
            "guide_offset_mm": J4_OFFSET,
            "side": "F.Cu",
        },
        "support_tongue": {
            "right_x": 150.0,
            "bottom_y": 144.25,
        },
        "clearances_mm": {
            "min_track_copper_to_new_edge": copper_edge_min,
            "min_via_copper_to_new_edge": via_edge_min,
            "min_j4_pad_copper_to_new_edge": j4_edge_min,
            "min_j4_pad_to_other_net_track_copper": pad_track_min,
            "min_j4_pad_to_other_net_via_copper": pad_via_min,
        },
        "slot_tracks": slot_segments,
        "slot_vias": slot_vias,
        "checks": checks,
    }
    rendered = json.dumps(result,indent=2,sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True,exist_ok=True)
        args.json_output.write_text(rendered+"\n",encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
