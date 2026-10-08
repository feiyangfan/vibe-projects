#!/usr/bin/env python3
"""Task 4B regeneration-safe routing proof validator."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
PROOF = ERGOGEN / "task4/task4b-routing-proof.yaml"
RULES = ERGOGEN / "task4/task4a-routing-contract.yaml"

TOL = 1e-6


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


def at_xyz(block: str):
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


def endpoints(text: str, net_name: str):
    found = []
    for fp in blocks(text, "footprint") + blocks(text, "module"):
        fp_at = at_xyz(fp)
        for pad in blocks(fp, "pad"):
            nm = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pad)
            if nm and nm.group(2) == net_name:
                found.append(absolute_pad(fp_at, at_xyz(pad)))
    return sorted(found)


def net_table(text: str):
    return {
        int(number): name
        for number, name in re.findall(r'\(net\s+(\d+)\s+"([^"]*)"\)', text)
    }


def segment_info(text: str):
    nets = net_table(text)
    out = []
    for seg in blocks(text, "segment"):
        start = re.search(r"\(start\s+([-\d.]+)\s+([-\d.]+)\)", seg)
        end = re.search(r"\(end\s+([-\d.]+)\s+([-\d.]+)\)", seg)
        width = re.search(r"\(width\s+([-\d.]+)\)", seg)
        layer = re.search(r'\(layer\s+"([^"]+)"\)', seg)
        net = re.search(r"\(net\s+(\d+)\)", seg)
        if not all((start, end, width, layer, net)):
            raise AssertionError("malformed proof segment")
        out.append({
            "start": (float(start.group(1)), float(start.group(2))),
            "end": (float(end.group(1)), float(end.group(2))),
            "width": float(width.group(1)),
            "layer": layer.group(1),
            "net": nets[int(net.group(1))],
        })
    return out


def same_point(a, b):
    return abs(a[0] - b[0]) <= TOL and abs(a[1] - b[1]) <= TOL


def validate_board(base_text: str, routed_text: str, proof: dict, rules: dict):
    if blocks(routed_text, "via"):
        raise AssertionError("Task 4B proof unexpectedly uses vias")
    if blocks(routed_text, "zone"):
        raise AssertionError("Task 4B proof unexpectedly adds zones")

    selected = set(proof["proof"]["nets"])
    segs = segment_info(routed_text)
    routed_nets = {s["net"] for s in segs}
    if routed_nets != selected:
        raise AssertionError(f"routed nets {sorted(routed_nets)} != {sorted(selected)}")

    layer = proof["proof"]["route_layer"]
    route_fingerprints = {}

    for net_name, spec in proof["proof"]["nets"].items():
        pts = endpoints(base_text, net_name)
        if len(pts) != spec["expected_endpoints"]:
            raise AssertionError(f"{net_name}: wrong endpoint count")
        net_segs = [s for s in segs if s["net"] == net_name]
        expected_width = float(rules["net_classes"][spec["class"]]["track_width"])
        if not net_segs:
            raise AssertionError(f"{net_name}: no routed segments")
        if any(abs(s["width"] - expected_width) > TOL for s in net_segs):
            raise AssertionError(f"{net_name}: wrong track width")
        if any(s["layer"] != layer for s in net_segs):
            raise AssertionError(f"{net_name}: wrong layer")

        degree = {}
        for s in net_segs:
            degree[s["start"]] = degree.get(s["start"], 0) + 1
            degree[s["end"]] = degree.get(s["end"], 0) + 1
            dx = abs(s["end"][0] - s["start"][0])
            dy = abs(s["end"][1] - s["start"][1])
            if dx > TOL and dy > TOL and abs(dx - dy) > TOL:
                raise AssertionError(f"{net_name}: non-45-degree diagonal")

        route_ends = [p for p, d in degree.items() if d == 1]
        if len(route_ends) != 2 or not all(any(same_point(p, e) for p in route_ends) for e in pts):
            raise AssertionError(f"{net_name}: route does not terminate on both generated pads")

        route_fingerprints[net_name] = tuple(
            sorted(
                (
                    round(s["start"][0], 6), round(s["start"][1], 6),
                    round(s["end"][0], 6), round(s["end"][1], 6),
                )
                for s in net_segs
            )
        )
    return route_fingerprints


def main():
    if len(sys.argv) != 5:
        raise AssertionError(
            "usage: validate_task4b.py PROD_BASE PROD_ROUTED PERTURBED_BASE PERTURBED_ROUTED"
        )

    prod_base, prod_routed, pert_base, pert_routed = map(Path, sys.argv[1:])
    proof = load(PROOF)
    rules = load(RULES)

    if proof["status"] not in {"task4b_candidate", "task4b_complete"}:
        raise AssertionError("unexpected Task 4B status")
    if rules["status"] != "task4a_frozen":
        raise AssertionError("Task 4A must remain frozen")

    prod_base_text = prod_base.read_text(encoding="utf-8")
    prod_routed_text = prod_routed.read_text(encoding="utf-8")
    pert_base_text = pert_base.read_text(encoding="utf-8")
    pert_routed_text = pert_routed.read_text(encoding="utf-8")

    if blocks(prod_base_text, "segment") or blocks(pert_base_text, "segment"):
        raise AssertionError("proof base boards must be unrouted")

    prod = validate_board(prod_base_text, prod_routed_text, proof, rules)
    pert = validate_board(pert_base_text, pert_routed_text, proof, rules)
    print("PASS representative matrix + RGB proof routes obey Task 4A")

    expected_changed = set(proof["perturbation_fixture"]["expected_changed_proof_nets"])
    for net_name in proof["proof"]["nets"]:
        before_endpoints = endpoints(prod_base_text, net_name)
        after_endpoints = endpoints(pert_base_text, net_name)
        changed = before_endpoints != after_endpoints
        if (net_name in expected_changed) != changed:
            raise AssertionError(
                f"{net_name}: endpoint-change state {changed} does not match fixture contract"
            )
        if net_name in expected_changed and prod[net_name] == pert[net_name]:
            raise AssertionError(f"{net_name}: route did not replay after upstream geometry change")
    print("PASS upstream point perturbation changes routes without manual track edits")

    if "uuid" not in proof["proof"]["routing_identity"]["forbidden"][0].lower():
        raise AssertionError("routing-identity policy malformed")
    router_source = (ERGOGEN / "scripts/route_task4b.py").read_text(encoding="utf-8")
    forbidden_searches = ("find_uuid", "lookup_uuid", "existing_uuid")
    if any(token in router_source for token in forbidden_searches):
        raise AssertionError("proof router contains forbidden UUID lookup mechanism")
    print("PASS routing proof is net-name/pad-geometry driven, not identity driven")

    print("Task 4B regeneration-safe routing mechanism proof passed")


if __name__ == "__main__":
    main()
