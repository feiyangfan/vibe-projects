#!/usr/bin/env python3
"""Task 4A routing rules and net-class freeze gate."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
CONTRACT = ERGOGEN / "task4/task4a-routing-contract.yaml"
TASK3E = ERGOGEN / "task3/task3e-cross-board-freeze.yaml"
STOCK_PRO = ERGOGEN.parent / "klor1.4/PCB/klor1_4/klor1_4.kicad_pro"
STOCK_DRU = ERGOGEN.parent / "klor1.4/PCB/klor1_4/klor1_4.kicad_dru"
STOCK_PCB = ERGOGEN.parent / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"

TOL = 1e-9


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def close(a, b):
    return abs(float(a) - float(b)) <= TOL


def expect_close(label, actual, expected):
    if not close(actual, expected):
        raise AssertionError(f"{label}: {actual} != {expected}")


def expect_equal(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def find_stock_class(project: dict, name: str) -> dict:
    found = [
        item for item in project["net_settings"]["classes"]
        if item["name"] == name
    ]
    if len(found) != 1:
        raise AssertionError(f"stock net class {name}: got {len(found)}")
    return found[0]


def classify(net: str, classes: dict) -> list[str]:
    matches = []
    for name, spec in classes.items():
        if net in spec.get("exact", []):
            matches.append(name)
            continue
        if any(re.fullmatch(pattern, net) for pattern in spec.get("regex", [])):
            matches.append(name)
    return matches


def board_nets(text: str) -> set[str]:
    return {
        name for _, name in re.findall(r'\(net\s+(\d+)\s+"([^"]*)"\)', text)
        if name
    }


def has_routing_item(text: str, token: str) -> bool:
    return re.search(rf"\({re.escape(token)}(?:\s|\n|\r|\t)", text) is not None


def main():
    if len(sys.argv) != 2:
        raise AssertionError("usage: validate_task4a.py GENERATED_DIR")

    generated = Path(sys.argv[1])
    left_path = generated / "pcbs/task3c_left_production.kicad_pcb"
    right_path = generated / "pcbs/task3d_right_production.kicad_pcb"
    if not left_path.is_file() or not right_path.is_file():
        raise AssertionError("Task 4A requires the generated Task-3 PCB pair")

    contract = load_yaml(CONTRACT)
    task3e = load_yaml(TASK3E)

    expect_equal("Task 4A status", contract["status"], "task4a_frozen")
    expect_equal("Task 3E status", task3e["status"], "task3e_frozen")
    expect_equal("Task 4A adds tracks", contract["routing_boundary"]["task4a_adds_tracks"], False)
    expect_equal("Task 4A adds vias", contract["routing_boundary"]["task4a_adds_vias"], False)
    expect_equal("Task 4A adds zones", contract["routing_boundary"]["task4a_adds_zones"], False)
    print("PASS Task 4A remains a routing-rule freeze only")

    stock_project = json.loads(STOCK_PRO.read_text(encoding="utf-8"))
    evidence = contract["stock_evidence"]["project_netclasses"]
    for stock_name, evidence_name in (("Default", "default"), ("Power", "power")):
        actual = find_stock_class(stock_project, stock_name)
        expected = evidence[evidence_name]
        for field in ("clearance", "track_width", "via_diameter", "via_drill"):
            expect_close(f"stock {stock_name} {field}", actual[field], expected[field])
    print("PASS stock KLOR Default/Power net-class evidence")

    dru = STOCK_DRU.read_text(encoding="utf-8")
    custom = contract["stock_evidence"]["custom_rules"]
    required_snippets = {
        "routed edge": f'(constraint edge_clearance (min {custom["routed_edge_clearance"]}mm))',
        "track/pad": f'(constraint clearance (min {custom["track_to_pad_clearance"]}mm))',
        "track/NPTH": f'(constraint hole_clearance (min {custom["track_to_npth_hole_clearance"]}mm))',
        "track/PTH": f'(constraint hole_clearance (min {custom["track_to_pth_hole_clearance"]}mm))',
        "annular": f'(constraint annular_width (min {custom["plated_annular_width_min"]}mm))',
    }
    for label, snippet in required_snippets.items():
        if snippet not in dru:
            raise AssertionError(f"stock custom rule evidence missing: {label}")
    print("PASS stock KLOR custom DRC evidence")

    stock_text = STOCK_PCB.read_text(encoding="utf-8")
    widths = {float(x) for x in re.findall(r'\(segment[\s\S]*?\(width\s+([0-9.]+)\)', stock_text)}
    expected_widths = {float(x) for x in contract["stock_evidence"]["routed_board"]["observed_trace_widths"]}
    expect_equal("stock routed trace widths", widths, expected_widths)

    via_pairs = {
        (float(a), float(b))
        for a, b in re.findall(
            r'\(via[\s\S]*?\(size\s+([0-9.]+)\)[\s\S]*?\(drill\s+([0-9.]+)\)',
            stock_text,
        )
    }
    stock_via = contract["stock_evidence"]["routed_board"]["observed_via"]
    expect_equal("stock routed via geometry", via_pairs, {(float(stock_via["diameter"]), float(stock_via["drill"]))})
    print("PASS stock routed board uses only frozen evidence widths/via geometry")

    fab = contract["fabrication_envelope"]
    expect_equal("layer count", fab["board"]["layers"], 2)
    expect_close("board thickness", fab["board"]["finished_thickness"], 1.6)
    expect_close("1 oz copper thickness", fab["board"]["copper_thickness"], 0.035)

    cap = fab["manufacturer_reference"]["capability_snapshot"]
    rules = contract["global_rules"]
    if rules["different_net_clearance"] < cap["min_track_spacing"]:
        raise AssertionError("Task-4 clearance is below fabrication reference")
    if rules["routed_edge_clearance"] < cap["routed_edge_copper_clearance"]:
        raise AssertionError("Task-4 edge clearance is below fabrication reference")
    if rules["track_to_pth_hole_clearance"] < cap["recommended_pth_to_track"]:
        raise AssertionError("Task-4 PTH/track clearance is below fabrication reference recommendation")
    if rules["blind_buried_vias"] != "forbidden" or rules["microvias"] != "forbidden":
        raise AssertionError("Task 4 must remain ordinary 2-layer through-via construction")

    for via_name, via in contract["vias"].items():
        if via["drill"] < cap["min_via_hole"]:
            raise AssertionError(f"{via_name} via drill below fabrication reference")
        if via["diameter"] < cap["min_via_diameter"]:
            raise AssertionError(f"{via_name} via diameter below fabrication reference")
        if via["diameter"] - via["drill"] + TOL < cap["preferred_via_diameter_minus_hole"]:
            raise AssertionError(f"{via_name} via does not meet preferred diameter-minus-hole margin")
        computed_annular = (via["diameter"] - via["drill"]) / 2
        expect_close(f"{via_name} annular width", via["annular_width"], computed_annular)
        if computed_annular + TOL < rules["plated_annular_width_min"]:
            raise AssertionError(f"{via_name} via below Task-4 annular-width rule")
    print("PASS fabrication margins and via geometry")

    classes = contract["net_classes"]
    signal_classes = ("matrix", "rgb_data", "control", "split", "pmw_spi")
    for name in signal_classes:
        expect_close(f"{name} width", classes[name]["track_width"], 0.254)
        expect_close(f"{name} clearance", classes[name]["clearance"], rules["different_net_clearance"])
        expect_equal(f"{name} via", classes[name]["via"], "standard")
    for name in ("power", "ground"):
        expect_close(f"{name} width", classes[name]["track_width"], 0.381)
        expect_close(f"{name} clearance", classes[name]["clearance"], rules["different_net_clearance"])
        expect_equal(f"{name} via", classes[name]["via"], "power")
    expect_equal("PMW right-only", classes["pmw_spi"]["right_only"], True)
    expect_equal("PMW preferred layer", classes["pmw_spi"]["preferred_layer"], "F.Cu")
    expect_equal("PMW length matching", classes["pmw_spi"]["length_matching_required"], False)
    expect_equal("PMW controlled impedance", classes["pmw_spi"]["controlled_impedance_required"], False)
    print("PASS frozen per-class width/clearance/via policy")

    left_text = left_path.read_text(encoding="utf-8")
    right_text = right_path.read_text(encoding="utf-8")

    for label, text in (("left", left_text), ("right", right_text)):
        for token in ("segment", "via", "zone"):
            if has_routing_item(text, token):
                raise AssertionError(f"{label}: Task 4A must not add {token}")
    print("PASS Task-3 pair remains intentionally unrouted")

    expected_pmw = set(classes["pmw_spi"]["exact"])
    for label, text in (("left", left_text), ("right", right_text)):
        nets = board_nets(text)
        for net in sorted(nets):
            matches = classify(net, classes)
            if len(matches) != 1:
                raise AssertionError(f"{label} net {net!r}: routing classes {matches}")
        pmw = nets & expected_pmw
        if label == "left" and pmw:
            raise AssertionError(f"left board has PMW nets: {sorted(pmw)}")
        if label == "right" and pmw != expected_pmw:
            raise AssertionError(f"right PMW nets {sorted(pmw)} != {sorted(expected_pmw)}")
        print(f"PASS {label} generated nets each map to exactly one routing class")

    zones = contract["ground"]["zones"]
    expect_equal("ground zone layers", zones["required_layers"], ["F.Cu", "B.Cu"])
    expect_close("ground zone clearance", zones["clearance"], rules["different_net_clearance"])
    expect_equal("left local layer", contract["layer_policy"]["left"]["local_component_side"], "B.Cu")
    expect_equal("right local layer", contract["layer_policy"]["right"]["local_component_side"], "F.Cu")
    print("PASS dual-layer ground and per-half local-layer policy")

    print("Task 4A routing rules and net classes passed")


if __name__ == "__main__":
    main()
