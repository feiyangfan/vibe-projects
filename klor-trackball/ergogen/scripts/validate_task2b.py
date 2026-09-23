#!/usr/bin/env python3
"""Task 2B regression gate for preserved KLOR/Konrad stock geometry."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
KLOR = HERE.parents[2]
STOCK_PCB = KLOR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
STOCK_PLATE_SVG = KLOR / "klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.svg"
CONFIG = ERGOGEN / "config.yaml"

POS_TOL = 1e-6
ROT_TOL = 1e-6
PATH_TOL = 2e-6

KONRAD_REFS = [*(f"SW{i}" for i in range(1, 18)), "SW20", "SW21", "SW22"]
POINT_MAP = {
    **{ref.lower(): ref for ref in KONRAD_REFS},
    "encoder_ref": "SW18",
    "mcu_ref": "U1",
    "trrs_ref": "J1",
    **{f"mh{i}": f"MH{i}" for i in range(1, 10)},
}

# Previously source-validated stock KiCad -> switchplate-native rigid transform.
# Task 2B uses this only to place the immutable switchplate perimeter/axes into
# the same canonical local frame as the PCB. The validator independently checks
# that the encoded SVG-derived geometry matches these source values.
R_KP = (
    (0.999999991, 0.000131877),
    (0.000131877, -0.999999991),
)
T_KP = (-80.655587, 153.995244)
SVG_MM = 25.4 / 72.0


def balanced_blocks(text: str, token: str) -> list[str]:
    out = []
    needle = "(" + token
    pos = 0
    while True:
        start = text.find(needle, pos)
        if start < 0:
            return out
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
            raise AssertionError(f"unbalanced {token} block")
        out.append(text[start:end])
        pos = end


def parse_footprints(text: str):
    found = {}
    for fp in balanced_blocks(text, "footprint"):
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', fp)
        if not ref_m:
            continue
        at_m = re.search(
            r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", fp
        )
        if not at_m:
            continue
        found[ref_m.group(1)] = (
            float(at_m.group(1)),
            float(at_m.group(2)),
            float(at_m.group(3) or 0.0),
        )
    return found


def local_from_kicad(p, origin):
    return (p[0] - origin[0], origin[1] - p[1], -p[2])


def assert_xyz(name, actual, expected, ptol=POS_TOL, rtol=ROT_TOL):
    delta = tuple(abs(a - e) for a, e in zip(actual, expected))
    if delta[0] > ptol or delta[1] > ptol or delta[2] > rtol:
        raise AssertionError(
            f"{name}: actual={actual}, expected={expected}, delta={delta}"
        )
    print(
        f"PASS {name:16s} x={actual[0]:10.6f} "
        f"y={actual[1]:10.6f} r={actual[2]:8.3f}"
    )


def top_edge_primitives(text: str):
    # Only board-level gr_line/gr_curve/gr_arc blocks on Edge.Cuts.
    out = []
    depth = 0
    quoted = False
    escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            i += 1
            continue
        if ch == '"':
            quoted = True
            i += 1
            continue
        if ch == "(":
            depth += 1
            if depth == 2:
                m = re.match(r"\((gr_line|gr_curve|gr_arc)\b", text[i:])
                if m:
                    d = 0
                    q = False
                    esc = False
                    end = None
                    for j in range(i, len(text)):
                        c = text[j]
                        if q:
                            if esc:
                                esc = False
                            elif c == "\\":
                                esc = True
                            elif c == '"':
                                q = False
                            continue
                        if c == '"':
                            q = True
                        elif c == "(":
                            d += 1
                        elif c == ")":
                            d -= 1
                            if d == 0:
                                end = j + 1
                                break
                    if end is None:
                        raise AssertionError("unbalanced board graphic")
                    block = text[i:end]
                    if '(layer "Edge.Cuts")' in block:
                        out.append(parse_primitive(block))
                    i = end
                    depth = 1
                    continue
        elif ch == ")":
            depth -= 1
        i += 1
    return out


def parse_primitive(block: str):
    typ = re.match(r"\((gr_\w+)", block).group(1)
    if typ == "gr_line":
        pts = [
            (float(a), float(b))
            for a, b in re.findall(r"\((?:start|end)\s+([-\d.]+)\s+([-\d.]+)\)", block)
        ]
    elif typ == "gr_curve":
        pts = [
            (float(a), float(b))
            for a, b in re.findall(r"\(xy\s+([-\d.]+)\s+([-\d.]+)\)", block)
        ]
    else:
        pts = [
            (float(a), float(b))
            for a, b in re.findall(r"\((?:start|mid|end)\s+([-\d.]+)\s+([-\d.]+)\)", block)
        ]
    return {"type": typ, "pts": pts, "start": pts[0], "end": pts[-1]}


def coord_key(p):
    return f"{p[0]:.6f},{p[1]:.6f}"


def edge_chains(prims):
    unused = set(range(len(prims)))
    chains = []
    while unused:
        first = next(iter(unused))
        unused.remove(first)
        chain = [(first, False)]
        end = prims[first]["end"]
        while True:
            found = None
            rev = False
            for j in unused:
                if coord_key(prims[j]["start"]) == coord_key(end):
                    found = j
                    break
                if coord_key(prims[j]["end"]) == coord_key(end):
                    found = j
                    rev = True
                    break
            if found is None:
                break
            unused.remove(found)
            chain.append((found, rev))
            end = prims[found]["start"] if rev else prims[found]["end"]
            if coord_key(end) == coord_key(prims[first]["start"]):
                break
        chains.append(chain)
    return sorted(chains, key=len, reverse=True)


def oriented_points(prim, reverse):
    pts = prim["pts"]
    if not reverse:
        return pts
    if prim["type"] == "gr_curve":
        return [pts[3], pts[2], pts[1], pts[0]]
    if prim["type"] == "gr_arc":
        return [pts[2], pts[1], pts[0]]
    return [pts[1], pts[0]]


def expected_board_segments(text, origin):
    prims = top_edge_primitives(text)
    result = []
    for chain in edge_chains(prims):
        segs = []
        for idx, (pi, rev) in enumerate(chain):
            prim = prims[pi]
            typ = {"gr_line": "line", "gr_curve": "bezier", "gr_arc": "arc"}[prim["type"]]
            pts = [
                local_from_kicad((x, y, 0.0), origin)[:2]
                for x, y in oriented_points(prim, rev)
            ]
            segs.append((typ, pts if idx == 0 else pts[1:]))
        result.append(segs)
    return result


def config_segments(config, outline_name):
    part = config["outlines"][outline_name][0]
    out = []
    for seg in part["segments"]:
        pts = [tuple(float(v) for v in p["shift"]) for p in seg["points"]]
        out.append((seg["type"], pts))
    return out


def assert_segments(name, actual, expected):
    if len(actual) != len(expected):
        raise AssertionError(f"{name}: segment count {len(actual)} != {len(expected)}")
    for i, ((at, ap), (et, ep)) in enumerate(zip(actual, expected)):
        if at != et:
            raise AssertionError(f"{name}[{i}]: type {at} != {et}")
        if len(ap) != len(ep):
            raise AssertionError(f"{name}[{i}]: point count {len(ap)} != {len(ep)}")
        for j, (a, e) in enumerate(zip(ap, ep)):
            if math.dist(a, e) > PATH_TOL:
                raise AssertionError(f"{name}[{i}].points[{j}]: {a} != {e}")
    print(f"PASS {name}: {len(actual)} exact source-derived path segments")


def plate_to_kicad(p):
    qx, qy = p[0] - T_KP[0], p[1] - T_KP[1]
    # inverse of the validated orthonormal transform = transpose
    return (
        R_KP[0][0] * qx + R_KP[1][0] * qy,
        R_KP[0][1] * qx + R_KP[1][1] * qy,
    )


def svg_path_geometry(svg_text: str, origin):
    m = re.search(r'<path[^>]*\sd="([^"]+)"', svg_text)
    if not m:
        raise AssertionError("switchplate SVG path missing")
    tokens = re.findall(r"[A-Za-z]|[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?", m.group(1))
    i = 0
    cmd = None
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    prev_ctrl = None
    subno = 0
    outer = []
    subpaths = []
    current_points = None

    def is_cmd(s):
        return bool(re.fullmatch(r"[A-Za-z]", s))

    def n():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    def add(*pts):
        current_points.extend(pts)

    while i < len(tokens):
        if is_cmd(tokens[i]):
            cmd = tokens[i]
            i += 1
        if cmd is None:
            raise AssertionError("malformed SVG path")
        rel = cmd.islower()
        C = cmd.upper()

        if C == "M":
            x, y = n(), n()
            if rel:
                x += cur[0]
                y += cur[1]
            cur = (x, y)
            start = cur
            subno += 1
            current_points = [cur]
            subpaths.append(current_points)
            prev_ctrl = None
            cmd = "l" if rel else "L"
        elif C == "Z":
            if subno == 1 and cur != start:
                outer.append(("line", [cur, start]))
            add(start)
            cur = start
            prev_ctrl = None
            cmd = None
        elif C == "L":
            x, y = n(), n()
            if rel:
                x += cur[0]
                y += cur[1]
            p = (x, y)
            if subno == 1:
                outer.append(("line", [cur, p]))
            cur = p
            add(cur)
            prev_ctrl = None
        elif C == "H":
            x = n() + (cur[0] if rel else 0.0)
            p = (x, cur[1])
            if subno == 1:
                outer.append(("line", [cur, p]))
            cur = p
            add(cur)
            prev_ctrl = None
        elif C == "V":
            y = n() + (cur[1] if rel else 0.0)
            p = (cur[0], y)
            if subno == 1:
                outer.append(("line", [cur, p]))
            cur = p
            add(cur)
            prev_ctrl = None
        elif C == "C":
            x1, y1, x2, y2, x, y = (n(), n(), n(), n(), n(), n())
            if rel:
                x1 += cur[0]; y1 += cur[1]
                x2 += cur[0]; y2 += cur[1]
                x += cur[0]; y += cur[1]
            pts = [cur, (x1, y1), (x2, y2), (x, y)]
            if subno == 1:
                outer.append(("bezier", pts))
            add(*pts[1:])
            cur = (x, y)
            prev_ctrl = (x2, y2)
        elif C == "S":
            x2, y2, x, y = n(), n(), n(), n()
            if rel:
                x2 += cur[0]; y2 += cur[1]
                x += cur[0]; y += cur[1]
            c1 = (
                2 * cur[0] - prev_ctrl[0],
                2 * cur[1] - prev_ctrl[1],
            ) if prev_ctrl else cur
            pts = [cur, c1, (x2, y2), (x, y)]
            if subno == 1:
                outer.append(("bezier", pts))
            add(*pts[1:])
            cur = (x, y)
            prev_ctrl = (x2, y2)
        else:
            raise AssertionError(f"unsupported SVG command {cmd}")

    def svg_to_local(p):
        kx, ky = plate_to_kicad((p[0] * SVG_MM, p[1] * SVG_MM))
        return local_from_kicad((kx, ky, 0.0), origin)[:2]

    outer_local = []
    for idx, (typ, pts) in enumerate(outer):
        converted = [svg_to_local(p) for p in pts]
        outer_local.append((typ, converted if idx == 0 else converted[1:]))

    axes = []
    for pts in subpaths:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if abs(w - 5.96) < 0.02 and abs(h - 5.96) < 0.02:
            center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            axes.append(svg_to_local(center))
    return outer_local, axes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", type=Path, required=True)
    args = ap.parse_args()

    required = [
        args.generated / "points/points.yaml",
        args.generated / "outlines/stock_board.dxf",
        args.generated / "outlines/stock_plate_perimeter.dxf",
        args.generated / "outlines/task2b_preview.dxf",
        args.generated / "pcbs/task2b_stock_reference.kicad_pcb",
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing/empty generated output: {path}")

    pcb_text = STOCK_PCB.read_text(encoding="utf-8")
    fps = parse_footprints(pcb_text)
    origin = fps["SW13"]
    generated = yaml.safe_load(
        (args.generated / "points/points.yaml").read_text(encoding="utf-8")
    )

    for point_name, stock_ref in POINT_MAP.items():
        p = generated[point_name]
        actual = (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))
        assert_xyz(point_name, actual, local_from_kicad(fps[stock_ref], origin))

    if "sw19" in generated:
        raise AssertionError("SW19 is alternate-layout geometry and must not be in fixed Konrad")
    print("PASS fixed Konrad point set excludes alternate-layout SW19")

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    expected_chains = expected_board_segments(pcb_text, origin)
    names = ["stock_board_outer", "stock_board_cutout_1", "stock_board_cutout_2"]
    if [len(c) for c in expected_chains] != [66, 8, 6]:
        raise AssertionError(f"unexpected stock Edge.Cuts chain lengths: {[len(c) for c in expected_chains]}")
    for name, expected in zip(names, expected_chains):
        assert_segments(name, config_segments(config, name), expected)

    plate_expected, axes_expected = svg_path_geometry(
        STOCK_PLATE_SVG.read_text(encoding="utf-8"), origin
    )
    assert_segments(
        "stock_plate_perimeter",
        config_segments(config, "stock_plate_perimeter"),
        plate_expected,
    )
    if len(axes_expected) != 8:
        raise AssertionError(f"expected 8 structural axes, found {len(axes_expected)}")
    for i, expected in enumerate(axes_expected, 1):
        p = generated[f"case_mount_{i}"]
        actual = (float(p["x"]), float(p["y"]), float(p.get("r", 0.0)))
        assert_xyz(f"case_mount_{i}", actual, (*expected, 0.0), PATH_TOL, ROT_TOL)

    stock_keys = [k for k in generated if re.fullmatch(r"sw(?:[1-9]|1[0-7]|20|21|22)", k)]
    if len(stock_keys) != 20:
        raise AssertionError(f"expected 20 fixed-Konrad stock keys, got {len(stock_keys)}")
    print("PASS 20-key stock Konrad geometry reconstructed")
    print("PASS 9 stock PCB mounting-hole references reconstructed")
    print("PASS 8 structural switchplate/case axes reconstructed")
    print("PASS stock PCB perimeter + two internal Edge.Cuts chains reconstructed exactly")
    print("PASS stock switchplate outer perimeter reconstructed from source SVG")
    print("Task 2B preserved-stock-geometry regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
