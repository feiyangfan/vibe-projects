#!/usr/bin/env python3
"""Task 3D right production-intent PCB gate."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
CONTRACT = ERGOGEN / "task3/task3d-right-board.yaml"
TASK3A = ERGOGEN / "task3/task3a-electrical-contract.yaml"
TASK3B = ERGOGEN / "task3/task3b-footprints.yaml"
TASK3C = ERGOGEN / "task3/task3c-left-board.yaml"
TASK2D = ERGOGEN / "task2/task2d-freeze.yaml"
CONFIG = ERGOGEN / "config.yaml"

TOL = 1e-6
GEOM_TOL = 2e-6

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


def resolve_point(config, name: str, seen=None):
    """Resolve the small anchor/ref subset used by the frozen Task-2/3 points."""
    if seen is None:
        seen = set()
    if name in seen:
        raise AssertionError(f"point reference cycle at {name}")
    seen = set(seen)
    seen.add(name)

    anchor = config["points"]["zones"][name]["anchor"]
    if "ref" in anchor:
        bx, by, br = resolve_point(config, anchor["ref"], seen)
    else:
        bx, by, br = (0.0, 0.0, 0.0)

    sx, sy = (0.0, 0.0)
    if "shift" in anchor:
        sx, sy = (float(anchor["shift"][0]), float(anchor["shift"][1]))

    # All referenced Task-2 trackball datums are unrotated before the final
    # Task-3D 180-degree PMW orientation, so additive shift is exact here.
    return (
        bx + sx,
        by + sy,
        br + float(anchor.get("rotate", 0.0)),
    )


def normalize_angle(angle):
    return ((angle + 180.0) % 360.0) - 180.0


def assert_angle(name, actual, expected):
    if abs(normalize_angle(actual - expected)) > TOL:
        raise AssertionError(f"{name}: {actual} != {expected}")


def assert_close(name, actual, expected, tol=TOL):
    if len(actual) != len(expected) or any(abs(a - b) > tol for a, b in zip(actual, expected)):
        raise AssertionError(f"{name}: {actual} != {expected}")


def pcb_point(config, point_name):
    """Convert frozen canonical (+Y up) point to KiCad (+Y down)."""
    x, y, r = resolve_point(config, point_name)
    return (x, -y, -r)


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


def global_pad_in_canonical(fp, pad):
    fx, fy, fr = at_xyz(fp)
    px, py = pad["at"]
    a = math.radians(fr)
    gx = fx + px * math.cos(a) - py * math.sin(a)
    gy = fy + px * math.sin(a) + py * math.cos(a)
    return (gx, -gy)


def main():
    if len(sys.argv) != 2:
        raise AssertionError("usage: validate_task3d.py GENERATED_DIR")

    generated = Path(sys.argv[1])
    board_path = generated / "pcbs/task3d_right_production.kicad_pcb"
    if not board_path.is_file():
        raise AssertionError(f"missing generated board: {board_path}")

    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    task3a = yaml.safe_load(TASK3A.read_text(encoding="utf-8"))
    task3b = yaml.safe_load(TASK3B.read_text(encoding="utf-8"))
    task3c = yaml.safe_load(TASK3C.read_text(encoding="utf-8"))
    task2d = yaml.safe_load(TASK2D.read_text(encoding="utf-8"))
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    if contract["status"] not in {"task3d_candidate", "task3d_complete"}:
        raise AssertionError("unexpected Task 3D status")
    if task3a["status"] != "task3a_frozen":
        raise AssertionError("Task 3A must remain frozen")
    if task3b["status"] != "task3b_qualified":
        raise AssertionError("Task 3B must remain qualified")
    if task3c["status"] != "task3c_complete":
        raise AssertionError("Task 3C must remain complete")
    if not str(task2d["status"]).startswith("task2d_frozen"):
        raise AssertionError("Task 2D must remain frozen")

    pcb_cfg = config["pcbs"]["task3d_right_production"]
    if pcb_cfg["outlines"]["main"]["outline"] != "trackball_board":
        raise AssertionError("right production PCB must use frozen trackball_board geometry")
    if task2d["pcb_geometry"]["composition"] != [
        {"outline": "stock_board", "operation": "add"},
        {"outline": "pmw_support_tongue", "operation": "add"},
        {"outline": "trackball_cavity", "operation": "subtract"},
        {"outline": "breakout_service_slot", "operation": "subtract"},
    ]:
        raise AssertionError("Task-2D frozen trackball composition changed")
    print("PASS frozen stock + support tongue - open cavity - service notch right-board geometry")

    # Non-reversible production policy: right SMD populations use the qualified
    # front-side variants; the PMW header is also frozen to F.Cu.
    for name, spec in pcb_cfg["footprints"].items():
        what = spec["what"]
        if what in {"klor_key", "klor_diode", "klor_trrs", "klor_reset"}:
            if spec["params"].get("side") != "F":
                raise AssertionError(f"{name}: right production side must be F")
    print("PASS right production assembly uses qualified F-side variants")

    text = board_path.read_text(encoding="utf-8")
    all_fps = fp_blocks(text)
    by_name = {}
    for fp in all_fps:
        by_name.setdefault(footprint_name(fp), []).append(fp)

    expected_counts = {
        NAMES["key"]: 19,
        NAMES["diode"]: 20,
        NAMES["controller"]: 1,
        NAMES["trrs"]: 1,
        NAMES["encoder"]: 1,
        NAMES["reset"]: 1,
        NAMES["mount"]: 9,
        NAMES["pmw"]: 1,
    }
    for name, count in expected_counts.items():
        actual = len(by_name.get(name, []))
        if actual != count:
            raise AssertionError(f"{name}: footprint count {actual} != {count}")
    print("PASS exact right production footprint counts")

    controller_unique = by_name[NAMES["controller"]][0]
    expected_controller = pcb_point(config, contract["controller"]["point"])
    actual_controller = at_xyz(controller_unique)
    assert_close(
        "controller canonical->KiCad position",
        actual_controller[:2],
        expected_controller[:2],
    )
    assert_angle(
        "controller canonical->KiCad rotation",
        actual_controller[2],
        expected_controller[2],
    )
    print("PASS frozen canonical-to-KiCad placement transform")

    switch_contract = contract["matrix"]["switches"]
    if "SW22" in switch_contract:
        raise AssertionError("SW22 must not exist in Task 3D matrix contract")

    matrix_positions = set()
    chain = contract["rgb"]["chain"]
    if "SW22" in chain:
        raise AssertionError("SW22 must be bypassed by the right RGB chain")
    chain_index = {name: i for i, name in enumerate(chain)}

    for sw, spec in switch_contract.items():
        fp = find_instance(all_fps, config, NAMES["key"], spec["point"])
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
            if "F.Cu" not in select_pad(gp, padno)["layers"]:
                raise AssertionError(f"{sw}: pad {padno} is not on qualified F-side copper")

        i = chain_index[sw]
        expected_din = "RGB_DATA_5V" if i == 0 else f"RGB_{chain[i-1]}_TO_{sw}"
        expected_dout = "" if i == len(chain)-1 else f"RGB_{sw}_TO_{chain[i+1]}"
        if select_pad(gp, 3)["net"] != expected_din:
            raise AssertionError(f"{sw}: RGB DIN changed")
        if select_pad(gp, 1)["net"] != expected_dout:
            raise AssertionError(f"{sw}: RGB DOUT changed")

        dpoint = "d" + spec["diode"][1:]
        dfp = find_instance(all_fps, config, NAMES["diode"], dpoint)
        dp = pads(dfp)
        if select_pad(dp, 1)["net"] != spec["row"]:
            raise AssertionError(f"{spec['diode']}: wrong row")
        if select_pad(dp, 2)["net"] != link:
            raise AssertionError(f"{spec['diode']}: wrong switch-side net")
        for padno in (1, 2):
            p = select_pad(dp, padno)
            if p["type"] != "smd" or "F.Cu" not in p["layers"] or p["drill"] is not None:
                raise AssertionError(f"{spec['diode']}: pad {padno} not qualified F-side SMD")
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
    for padno in (1, 2):
        if "F.Cu" not in select_pad(d18p, padno)["layers"]:
            raise AssertionError("D18 must use qualified F-side production lands")
    if net_count(all_fps, enc_spec["switch_net"]) != 2:
        raise AssertionError("encoder click must have exactly encoder+D18 endpoints")
    matrix_positions.add((enc_spec["row"], enc_spec["col"]))

    if contract["matrix"]["active_positions"] != 20 or len(matrix_positions) != 20:
        raise AssertionError(f"matrix active-position count changed: {len(matrix_positions)}")
    print("PASS 19 MX + encoder click form 20 unique COL2ROW matrix positions")

    if len(chain) != 19:
        raise AssertionError("right RGB chain must contain exactly 19 devices")
    for i in range(len(chain)-1):
        net = f"RGB_{chain[i]}_TO_{chain[i+1]}"
        if net_count(all_fps, net) != 2:
            raise AssertionError(f"{net}: RGB chain endpoint count changed")
    if net_count(all_fps, "RGB_DATA_5V") != 2:
        raise AssertionError("RGB_DATA_5V must connect controller pad32 to first RGB DIN")
    forbidden_removed_nets = {
        "SW22_TO_D22",
        "RGB_SW13_TO_SW22",
        "RGB_SW22_TO_SW14",
    }
    all_nets = {p["net"] for fp in all_fps for p in pads(fp) if p["net"]}
    leaked = sorted(forbidden_removed_nets & all_nets)
    if leaked:
        raise AssertionError(f"removed R34/SW22 nets leaked onto right board: {leaked}")
    print("PASS exact 19-device RGB chain bypasses removed SW22/R34")

    ctl = find_instance(all_fps, config, NAMES["controller"], contract["controller"]["point"])
    cp = pads(ctl)
    for number, expected in contract["controller"]["pads"].items():
        actual = select_pad(cp, number)["net"]
        expected_net = "" if expected == "NC" else expected
        if actual != expected_net:
            raise AssertionError(f"controller pad {number}: {actual} != {expected_net}")
    if select_pad(cp, 25)["net"] != "ENCODER_B" or select_pad(cp, 26)["net"] != "ENCODER_A":
        raise AssertionError("right encoder GP28/GP29 swap changed")
    print("PASS Helios right GPIO ownership including encoder direction swap")

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
    if len(p1) != 2 or any(p["net"] != "RESET" or "F.Cu" not in p["layers"] for p in p1):
        raise AssertionError("reset pad 1 geometry/net changed")
    if len(p2) != 1 or p2[0]["net"] != "GND" or "F.Cu" not in p2[0]["layers"]:
        raise AssertionError("reset pad 2 geometry/net changed")
    if net_count(all_fps, "SPLIT_DATA") != 2:
        raise AssertionError("SPLIT_DATA must connect controller to TRRS only")
    print("PASS split/power/reset interfaces coherent")

    pmw = find_instance(all_fps, config, NAMES["pmw"], contract["pmw3360"]["point"])
    pmw_at = at_xyz(pmw)
    expected_pmw_at = pcb_point(config, contract["pmw3360"]["point"])
    assert_close("PMW center", pmw_at[:2], expected_pmw_at[:2])
    assert_angle("PMW rotation", pmw_at[2], expected_pmw_at[2])

    frozen_center = resolve_point(config, contract["pmw3360"]["frozen_center_point"])
    prod_center = resolve_point(config, contract["pmw3360"]["point"])
    assert_close("PMW production center preserves Task-2 center", prod_center[:2], frozen_center[:2])
    assert_angle(
        "PMW canonical production rotation",
        prod_center[2],
        float(contract["pmw3360"]["canonical_rotation"]),
    )

    pp = pads(pmw)
    pin_order = {
        int(k): v
        for k, v in contract["pmw3360"]["physical_pin_order_positive_y_to_negative_y"].items()
    }
    pitch = float(contract["pmw3360"]["pitch"])
    for n in range(1, 8):
        p = select_pad(pp, n)
        expected_net = "" if pin_order[n] == "NC" else pin_order[n]
        if p["net"] != expected_net:
            raise AssertionError(f"PMW pin {n}: {p['net']} != {expected_net}")
        expected_y = frozen_center[1] + (3 - (n - 1)) * pitch
        actual_xy = global_pad_in_canonical(pmw, p)
        assert_close(
            f"PMW pin {n} frozen physical position",
            actual_xy,
            (frozen_center[0], expected_y),
            GEOM_TOL,
        )
    if net_count(all_fps, "PMW_CS") != 2:
        raise AssertionError("PMW_CS must connect controller and header only")
    if net_count(all_fps, "PMW_MISO") != 2:
        raise AssertionError("PMW_MISO must connect controller and header only")
    if net_count(all_fps, "PMW_MOSI") != 2:
        raise AssertionError("PMW_MOSI must connect controller and header only")
    if net_count(all_fps, "PMW_SCK") != 2:
        raise AssertionError("PMW_SCK must connect controller and header only")
    if net_count(all_fps, "V3V3") != 2:
        raise AssertionError("V3V3 must connect Helios pad27 and PMW header pin6 only")
    ball_center = resolve_point(config, "ball_center")
    breakout_center = resolve_point(config, "breakout_center")
    if not (frozen_center[0] > ball_center[0] and breakout_center[0] > ball_center[0]):
        raise AssertionError("PMW connector/breakout must remain on +X / right side of ball")
    if contract["pmw3360"]["pin_1_end"] != "positive_canonical_y":
        raise AssertionError("PMW pin 1 must remain at positive canonical Y")
    if contract["pmw3360"]["pin_7_end"] != "negative_canonical_y":
        raise AssertionError("PMW pin 7 must remain at negative canonical Y")
    assert_close(
        "Task3D ball center",
        ball_center[:2],
        tuple(float(x) for x in contract["board"]["ball_center_local"]),
    )
    print("PASS KLORBall-35-style right-side PMW center, physical direction, SPI and 3V3 ownership")

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
            raise AssertionError(f"Task 3D board must be unrouted; found {token}")
    print("PASS no tracks, vias, or copper zones: routing remains Task 4")

    allowed = set(expected_counts)
    unexpected = sorted(set(by_name) - allowed)
    if unexpected:
        raise AssertionError(f"unexpected/non-qualified footprint classes: {unexpected}")

    if "SW22_TO_D22" in text or "RGB_SW13_TO_SW22" in text or "RGB_SW22_TO_SW14" in text:
        raise AssertionError("removed R34/SW22 electrical intent reappeared")

    print("Task 3D right production-intent PCB passed")


if __name__ == "__main__":
    main()
