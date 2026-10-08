#!/usr/bin/env python3
"""Task 4B deterministic proof router.

Routes a deliberately small set of two-endpoint nets by net name + pad geometry.
It never searches for or depends on existing KiCad UUIDs.
"""

from __future__ import annotations

import math
import re
import sys
import uuid
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
PROOF = ERGOGEN / "task4/task4b-routing-proof.yaml"
RULES = ERGOGEN / "task4/task4a-routing-contract.yaml"

NAMESPACE = uuid.UUID("e3081881-6bdc-4bc0-8a3d-9f5f70f1cc18")
TOL = 1e-9


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def blocks(text: str, token: str) -> list[str]:
    out = []
    pattern = re.compile(r"\\(" + re.escape(token) + r"(?=\\s|\\))")
    pos = 0
    while True:
        match = pattern.search(text, pos)
        if not match:
            return out
        start = match.start()
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
                    out.append(text[start:i + 1])
                    pos = i + 1
                    break
        else:
            raise AssertionError(f"unbalanced {token} block")


def at_xyz(block: str) -> tuple[float, float, float]:
    m = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", block)
    if not m:
        raise AssertionError("missing at")
    return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0.0)


def absolute_pad(fp_at, pad_at):
    x, y, r = fp_at
    px, py, _ = pad_at
    a = math.radians(r)
    return (
        round(x + px * math.cos(a) - py * math.sin(a), 6),
        round(y + px * math.sin(a) + py * math.cos(a), 6),
    )


def net_table(text: str):
    by_name = {}
    for number, name in re.findall(r'\(net\s+(\d+)\s+"([^"]*)"\)', text):
        by_name.setdefault(name, int(number))
    return by_name


def endpoints(text: str, net_name: str):
    found = []
    for fp in blocks(text, "footprint") + blocks(text, "module"):
        fp_at = at_xyz(fp)
        for pad in blocks(fp, "pad"):
            nm = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pad)
            if not nm or nm.group(2) != net_name:
                continue
            found.append(absolute_pad(fp_at, at_xyz(pad)))
    return sorted(found)


def route45(a, b):
    x1, y1 = a
    x2, y2 = b
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) <= TOL or abs(dy) <= TOL or abs(abs(dx) - abs(dy)) <= TOL:
        return [a, b]
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    diagonal = min(abs(dx), abs(dy))
    bend = (
        round(x1 + sx * diagonal, 6),
        round(y1 + sy * diagonal, 6),
    )
    return [a, bend, b]


def fmt(v: float) -> str:
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in {"", "-0"} else s


def segment(net_name, net_id, index, start, end, width, layer):
    seed = f"task4b|{net_name}|{index}|{start}|{end}|{width}|{layer}"
    sid = uuid.uuid5(NAMESPACE, seed)
    return (
        "\t(segment\n"
        f"\t\t(start {fmt(start[0])} {fmt(start[1])})\n"
        f"\t\t(end {fmt(end[0])} {fmt(end[1])})\n"
        f"\t\t(width {fmt(width)})\n"
        f'\t\t(layer "{layer}")\n'
        f"\t\t(net {net_id})\n"
        f'\t\t(uuid "{sid}")\n'
        "\t)"
    )


def main():
    if len(sys.argv) != 3:
        raise AssertionError("usage: route_task4b.py INPUT.kicad_pcb OUTPUT.kicad_pcb")

    src, dst = map(Path, sys.argv[1:])
    text = src.read_text(encoding="utf-8")
    proof = load(PROOF)
    rules = load(RULES)

    if blocks(text, "segment") or blocks(text, "via") or blocks(text, "zone"):
        raise AssertionError("Task 4B proof router requires a fresh unrouted Task-3 board")

    if proof["proof"]["half"] != "left":
        raise AssertionError("Task 4B proof currently targets the left production board")

    layer = proof["proof"]["route_layer"]
    expected_layer = rules["layer_policy"]["left"]["local_component_side"]
    if layer != expected_layer:
        raise AssertionError(f"proof layer {layer} != Task4A left local layer {expected_layer}")

    net_ids = net_table(text)
    rendered = []

    for net_name, spec in proof["proof"]["nets"].items():
        if net_name not in net_ids:
            raise AssertionError(f"missing proof net {net_name}")
        pts = endpoints(text, net_name)
        if len(pts) != spec["expected_endpoints"]:
            raise AssertionError(f"{net_name}: endpoints {len(pts)} != {spec['expected_endpoints']}")

        net_class = spec["class"]
        width = float(rules["net_classes"][net_class]["track_width"])
        path = route45(pts[0], pts[1])
        for i, (start, end) in enumerate(zip(path, path[1:])):
            rendered.append(segment(net_name, net_ids[net_name], i, start, end, width, layer))

    close = text.rfind(")")
    if close < 0:
        raise AssertionError("invalid KiCad PCB")
    routed = text[:close].rstrip() + "\n" + "\n".join(rendered) + "\n" + text[close:]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(routed, encoding="utf-8")


if __name__ == "__main__":
    main()
