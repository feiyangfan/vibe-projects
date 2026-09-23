#!/usr/bin/env python3
"""Task 3C left production-intent PCB gate."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
CONTRACT = ERGOGEN / "task3/task3c-left-board.yaml"
TASK3A = ERGOGEN / "task3/task3a-electrical-contract.yaml"
TASK3B = ERGOGEN / "task3/task3b-footprints.yaml"
TASK2D = ERGOGEN / "task2/task2d-freeze.yaml"
CONFIG = ERGOGEN / "config.yaml"

TOL = 1e-6

NAMES = {
    "key": "KLOR_MX_HOTSWAP_SK6812MINI_E",
    "diode": "KLOR_D_SOD123",
    "controller": "KLOR_HELIOS_REV1_HOST",
    "trrs": "KLOR_MJ_4PP_9",
    "encoder": "KLOR_EC11E",
    "reset": "KLOR_SKRTLAE010_RESET",
    "mount": "KLOR_MOUNTING_HOLE",
    "pmw": "KLOR_PMW_1X07_P2_54",
}


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


def fp_blocks(text: str) -> list[str]:
    return balanced_blocks(text, "footprint") + balanced_blocks(text, "module")


def footprint_name(block: str) -> str:
    m = re.match(r'\((?:footprint|module)\s+"?([^"\s\)]+)"?', block)
    if not m:
        raise AssertionError("footprint/module name missing")
    return m.group(1)


def at_xyz(block: str):
    m = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", block)
    if not m:
        raise AssertionError("footprint at missing")
    return (float(m.group(1)), float(m.group(2)), float(m.group(3) or 0.0))


def pad_info(block: str):
    head = re.match(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))\s+(\S+)\s+(\S+)', block)
    if not head:
        raise AssertionError(f"bad pad block: {block[:120]}")
    number = head.group(1) if head.group(1) is not None else head.group(2)
    typ, shape = head.group(3), head.group(4)
    at = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)", block)
    drill = re.search(r"\(drill(?:\s+oval)?\s+([-\d.]+)(?:\s+([-\d.]+))?\)", block)
    layers = re.search(r"\(layers\s+([^\)]+)\)", block)
    net = re.search(r'\(net\s+\d+\s+"([^"]*)"\)', block)
    return {
        "number": number,
        "type": typ,
        "shape": shape,
        "at": (float(at.group(1)), float(at.group(2))) if at else (0.0, 0.0),
        "drill": (
            (float(drill.group(1)), float(drill.group(2) or drill.group(1)))
            if drill else None
        ),
        "layers": tuple(x.strip('"') for x in layers.group(1).split()) if layers else (),
        "net": net.group(1) if net else "",
    }


def pads(block: str):
    return [pad_info(x) for x in balanced_blocks(block, "pad")]


def point(config, name: str):
    anchor = config["points"]["zones"][name]["anchor"]
    shift = anchor["shift"]
    return (float(shift[0]), float(shift[1]), float(anchor.get("rotate", 0.0)))


def assert_close(name, actual, expected):
    if any(abs(a - b) > TOL for a, b in zip(actual, expected)):
        raise AssertionError(f"{name}: {actual} != {expected}")


def pcb_point(config, point_name):
    """Convert frozen Task-2 canonical (+Y up) point to KiCad (+Y down)."""
    local = point(config, point_name)
    return (local[0], -local[1], -local[2])


def find_instance(all_fps, config, fp_name, point_name):
    expected = pcb_point(config, point_name)
    found = [
        fp for fp in all_fps
        if footprint_name(fp) == fp_name
        and abs(at_xyz(fp)[0] - expected[0]) <= TOL
        and abs(at_xyz(fp)[1] - expected[1]) <= TOL
    ]
    if len(found) != 1:
        raise AssertionError(
            f"{fp_name}@{point_name}: expected 1 instance at {expected[:2]}, got {len(found)}"
        )
    return found[0]


def select_pad(plist, number):
    found = [p for p in plist if p["number"] == str(number)]
    if len(found) != 1:
        raise AssertionError(f"pad {number}: got {len(found)}")
    return found[0]


def net_count(all_fps, net):
    return sum(1 for fp in all_fps for p in pads(fp) if p["net"] == net)


def main():
    if len(sys.argv) != 2:
        raise AssertionError("usage: validate_task3c.py GENERATED_DIR")

    generated = Path(sys.argv[1])
    board_path = generated / "pcbs/task3c_left_production.kicad_pcb"
    if not board_path.is_file():
        raise AssertionError(f"missing generated board: {board_path}")

    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    task3a = yaml.safe_load(TASK3A.read_text(encoding="utf-8"))
    task3b = yaml.safe_load(TASK3B.read_text(encoding="utf-8"))
    task2d = yaml.safe_load(TASK2D.read_text(encoding="utf-8"))
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    if contract["status"] not in {"task3c_candidate", "task3c_complete"}:
        raise AssertionError("unexpected Task 3C status")
    if task3a["status"] != "task3a_frozen":
        raise AssertionError("Task 3A must remain frozen")
    if task3b["status"] != "task3b_qualified":
        raise AssertionError("Task 3B must remain qualified")
    if not str(task2d["status"]).startswith("task2d_frozen"):
        raise AssertionError("Task 2D must remain frozen")

    pcb_cfg = config["pcbs"]["task3c_left_production"]
    if pcb_cfg["outlines"]["main"]["outline"] != "stock_board":
        raise AssertionError("left production PCB must use frozen stock_board geometry")

    text = board_path.read_text(encoding="utf-8")
    all_fps = fp_blocks(text)
    by_name = {}
    for fp in all_fps:
        by_name.setdefault(footprint_name(fp), []).append(fp)

    expected_counts = {
        NAMES["key"]: 20,
        NAMES["diode"]: 21,
        NAMES["controller"]: 1,
        NAMES["trrs"]: 1,
        NAMES["encoder"]: 1,
        NAMES["reset"]: 1,
        NAMES["mount"]: 9,
    }
    for name, count in expected_counts.items():
        actual = len(by_name.get(name, []))
        if actual != count:
            raise AssertionError(f"{name}: footprint count {actual} != {count}")
    if by_name.get(NAMES["pmw"]):
        raise AssertionError("left board must not contain PMW header")
    print("PASS exact left production footprint counts")

    # The frozen canonical frame reflects KiCad Y so +Y points up.
    # Generated KiCad output reverses that reflection: (x, y, r) -> (x, -y, -r).
    controller_unique = by_name[NAMES["controller"]][0]
    expected_controller = pcb_point(config, contract["controller"]["point"])
    actual_controller = at_xyz(controller_unique)
    assert_close("controller canonical->KiCad transform", actual_controller, expected_controller)
    print("PASS frozen canonical-to-KiCad reflection")

    switch_contract = contract["matrix"]["switches"]
    matrix_positions = set()
    key_instances = {}
    diode_instances = {}

    chain = contract["rgb"]["chain"]
    chain_index = {name: i for i, name in enumerate(chain)}

    for sw, spec in switch_contract.items():
        fp = find_instance(all_fps, config, NAMES["key"], spec["point"])
        key_instances[sw] = fp
        gp = pads(fp)
        n = sw[2:]
        link = f"{sw}_TO_D{n}"
        if select_pad(gp, 5)["net"] != spec["col"]:
            raise AssertionError(f"{sw}: wrong matrix column")
        if select_pad(gp, 6)["net"] != link:
            raise AssertionError(f"{sw}: wrong switch-to-diode net")
        if select_pad(gp, 2)["net"] != "GND":
            raise AssertionError(f"{sw}: RGB GND changed")
        if select_pad(gp, 4)["net"] != "RAW_5V":
            raise AssertionError(f"{sw}: RGB VDD changed")
        for padno in (1, 2, 3, 4, 5, 6):
            if "B.Cu" not in select_pad(gp, padno)["layers"]:
                raise AssertionError(f"{sw}: pad {padno} is not on qualified B-side copper")

        i = chain_index[sw]
        expected_din = "RGB_DATA_5V" if i == 0 else f"RGB_{chain[i-1]}_TO_{sw}"
        expected_dout = "" if i == len(chain)-1 else f"RGB_{sw}_TO_{chain[i+1]}"
        if select_pad(gp, 3)["net"] != expected_din:
            raise AssertionError(f"{sw}: RGB DIN changed")
        if select_pad(gp, 1)["net"] != expected_dout:
            raise AssertionError(f"{sw}: RGB DOUT changed")

        dpoint = "d" + spec["diode"][1:]
        dfp = find_instance(all_fps, config, NAMES["diode"], dpoint)
        diode_instances[spec["diode"]] = dfp
        dp = pads(dfp)
        if select_pad(dp, 1)["net"] != spec["row"]:
            raise AssertionError(f"{spec['diode']}: wrong row")
        if select_pad(dp, 2)["net"] != link:
            raise AssertionError(f"{spec['diode']}: wrong switch-side net")
        for padno in (1, 2):
            p = select_pad(dp, padno)
            if p["type"] != "smd" or "B.Cu" not in p["layers"] or p["drill"] is not None:
                raise AssertionError(f"{spec['diode']}: pad {padno} not qualified B-side SMD")
        if net_count(all_fps, link) != 2:
            raise AssertionError(f"{link}: expected exactly key+diode endpoints")

        pos = (spec["row"], spec["col"])
        if pos in matrix_positions:
            raise AssertionError(f"duplicate matrix position {pos}")
        matrix_positions.add(pos)

    enc_spec = contract["matrix"]["encoder_click"]
    enc = find_instance(all_fps, config, NAMES["encoder"], enc_spec["point"])
    ep = pads(enc)
    for pin, net in {
        "A": "ENCODER_A",
        "B": "ENCODER_B",
        "C": "GND",
        "S1": enc_spec["col"],
        "S2": enc_spec["switch_net"],
    }.items():
        if select_pad(ep, pin)["net"] != net:
            raise AssertionError(f"encoder {pin}: wrong net")

    d18 = find_instance(all_fps, config, NAMES["diode"], enc_spec["diode_point"])
    d18p = pads(d18)
    if select_pad(d18p, 1)["net"] != enc_spec["row"]:
        raise AssertionError("D18 row changed")
    if select_pad(d18p, 2)["net"] != enc_spec["switch_net"]:
        raise AssertionError("D18 encoder-click net changed")
    if net_count(all_fps, enc_spec["switch_net"]) != 2:
        raise AssertionError("encoder click must have exactly encoder+D18 endpoints")
    matrix_positions.add((enc_spec["row"], enc_spec["col"]))

    if contract["matrix"]["active_positions"] != 21 or len(matrix_positions) != 21:
        raise AssertionError(f"matrix active-position count changed: {len(matrix_positions)}")
    print("PASS 20 MX + encoder click form 21 unique COL2ROW matrix positions")

    for i in range(len(chain)-1):
        net = f"RGB_{chain[i]}_TO_{chain[i+1]}"
        if net_count(all_fps, net) != 2:
            raise AssertionError(f"{net}: RGB chain endpoint count changed")
    if net_count(all_fps, "RGB_DATA_5V") != 2:
        raise AssertionError("RGB_DATA_5V must connect controller pad32 to first RGB DIN")
    print("PASS exact 20-device left RGB chain")

    ctl = find_instance(all_fps, config, NAMES["controller"], contract["controller"]["point"])
    cp = pads(ctl)
    for number, expected in contract["controller"]["pads"].items():
        actual = select_pad(cp, number)["net"]
        expected_net = "" if expected == "NC" else expected
        if actual != expected_net:
            raise AssertionError(f"controller pad {number}: {actual} != {expected_net}")

    all_nets = {p["net"] for fp in all_fps for p in pads(fp) if p["net"]}
    for forbidden in contract["controller"]["forbidden_nets"]:
        if forbidden in all_nets:
            raise AssertionError(f"right-only net leaked onto left board: {forbidden}")
    print("PASS Helios left GPIO ownership with no PMW nets")

    trrs = find_instance(all_fps, config, NAMES["trrs"], contract["trrs"]["point"])
    tp = pads(trrs)
    for number, expected in contract["trrs"]["pins"].items():
        expected_net = "" if expected == "NC" else expected
        if select_pad(tp, number)["net"] != expected_net:
            raise AssertionError(f"TRRS pin {number}: wrong net")

    reset = find_instance(all_fps, config, NAMES["reset"], contract["reset"]["point"])
    rp = pads(reset)
    p1 = [p for p in rp if p["number"] == "1"]
    p2 = [p for p in rp if p["number"] == "2"]
    if len(p1) != 2 or any(p["net"] != "RESET" or "B.Cu" not in p["layers"] for p in p1):
        raise AssertionError("reset pad 1 geometry/net changed")
    if len(p2) != 1 or p2[0]["net"] != "GND" or "B.Cu" not in p2[0]["layers"]:
        raise AssertionError("reset pad 2 geometry/net changed")

    if net_count(all_fps, "SPLIT_DATA") != 2:
        raise AssertionError("SPLIT_DATA must connect controller to TRRS only")
    print("PASS split/power/reset interfaces coherent")

    for i in range(1, 10):
        mh = find_instance(all_fps, config, NAMES["mount"], f"mh{i}")
        mp = pads(mh)
        if len(mp) != 1 or mp[0]["number"] != "":
            raise AssertionError(f"MH{i}: malformed NPTH")
        expected = 2.2 if i == 9 else 3.2
        if mp[0]["drill"] != (expected, expected) or mp[0]["net"]:
            raise AssertionError(f"MH{i}: drill/copper changed")
    print("PASS frozen nine PCB mounting holes")

    for token in ("segment", "via", "zone"):
        if any(f"({token}{ws}" in text for ws in (" ", chr(9), chr(10), chr(13))):
            raise AssertionError(f"Task 3C board must be unrouted; found {token}")
    print("PASS no tracks, vias, or copper zones: routing remains Task 4")

    # All production footprints on this board must be from the Task-3B local set.
    allowed = set(expected_counts) | {NAMES["pmw"]}
    unexpected = sorted(set(by_name) - allowed)
    if unexpected:
        raise AssertionError(f"unexpected/non-qualified footprint classes: {unexpected}")

    print("Task 3C left production-intent PCB passed")


if __name__ == "__main__":
    main()
