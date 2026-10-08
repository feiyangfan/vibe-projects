#!/usr/bin/env python3
"""Task 3E cross-board electrical integration and freeze gate."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
FREEZE = ERGOGEN / "task3/task3e-cross-board-freeze.yaml"
TASK3A = ERGOGEN / "task3/task3a-electrical-contract.yaml"
LEFT = ERGOGEN / "task3/task3c-left-board.yaml"
RIGHT = ERGOGEN / "task3/task3d-right-board.yaml"
TASK2D = ERGOGEN / "task2/task2d-freeze.yaml"

NAMES = {
    "key": "KLOR_MX_HOTSWAP_SK6812MINI_E",
    "diode": "KLOR_D_SOD123",
    "controller": "KLOR_HELIOS_REV1_HOST",
    "trrs": "KLOR_MJ_4PP_9",
    "encoder": "KLOR_EC11E",
    "reset": "KLOR_SKRTLAE010_RESET",
    "pmw": "KLOR_PMW_1X07_P2_54",
}

PMW_NETS = {"PMW_SCK", "PMW_MOSI", "PMW_MISO", "PMW_CS"}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def fp_blocks(text: str) -> list[str]:
    return balanced_blocks(text, "footprint") + balanced_blocks(text, "module")


def fp_name(block: str) -> str:
    m = re.match(r'\((?:footprint|module)\s+"?([^"\s\)]+)"?', block)
    if not m:
        raise AssertionError("footprint name missing")
    return m.group(1)


def pad_nets(block: str) -> dict[str, str]:
    out = {}
    for pad in balanced_blocks(block, "pad"):
        m = re.match(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
        if not m:
            continue
        number = m.group(1) if m.group(1) is not None else m.group(2)
        if not number:
            continue
        net = re.search(r'\(net\s+\d+\s+"([^"]*)"\)', pad)
        value = net.group(1) if net else ""
        if number in out and out[number] != value:
            raise AssertionError(f"pad {number} has conflicting nets")
        out[number] = value
    return out


def unique_fp(text: str, name: str) -> str:
    found = [fp for fp in fp_blocks(text) if fp_name(fp) == name]
    if len(found) != 1:
        raise AssertionError(f"{name}: expected one footprint, got {len(found)}")
    return found[0]


def fp_count(text: str, name: str) -> int:
    return sum(fp_name(fp) == name for fp in fp_blocks(text))


def board_nets(text: str) -> set[str]:
    return {
        n for n in re.findall(r'\(net\s+\d+\s+"([^"]*)"\)', text)
        if n
    }


def expect_equal(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def main():
    if len(sys.argv) != 2:
        raise AssertionError("usage: validate_task3e.py GENERATED_DIR")

    generated = Path(sys.argv[1])
    left_path = generated / "pcbs/task3c_left_production.kicad_pcb"
    right_path = generated / "pcbs/task3d_right_production.kicad_pcb"
    if not left_path.is_file() or not right_path.is_file():
        raise AssertionError("Task 3E requires both generated production PCBs")

    freeze = load(FREEZE)
    task3a = load(TASK3A)
    left = load(LEFT)
    right = load(RIGHT)
    task2d = load(TASK2D)

    expect_equal("Task 3E status", freeze["status"], "task3e_frozen")
    expect_equal("Task 3A status", task3a["status"], "task3a_frozen")
    expect_equal("Task 3C status", left["status"], "task3c_complete")
    expect_equal("Task 3D status", right["status"], "task3d_complete")
    expect_equal("Task 2 revision", task2d["revision"], freeze["geometry"]["task2_revision"])
    expect_equal("Rev-6 ball center", task2d["trackball"]["ball_center_local"], freeze["geometry"]["ball_center_local"])
    expect_equal("right board ball center", right["board"]["ball_center_local"], freeze["geometry"]["ball_center_local"])
    expect_equal("right geometry revision", right["board"]["geometry_revision"], freeze["geometry"]["right_geometry_revision"])
    print("PASS Task-2 Rev 6 geometry remains the Task-3E authority")

    pair = freeze["pair"]
    expect_equal("left MX count", left["counts"]["mx_keys"], pair["left_mx_keys"])
    expect_equal("right MX count", right["counts"]["mx_keys"], pair["right_mx_keys"])
    expect_equal("total MX count", left["counts"]["mx_keys"] + right["counts"]["mx_keys"], pair["total_mx_keys"])
    expect_equal("left RGB count", left["counts"]["rgb_devices"], pair["left_rgb_devices"])
    expect_equal("right RGB count", right["counts"]["rgb_devices"], pair["right_rgb_devices"])
    expect_equal("total RGB count", left["counts"]["rgb_devices"] + right["counts"]["rgb_devices"], pair["total_rgb_devices"])
    expect_equal(
        "total active matrix positions",
        left["matrix"]["active_positions"] + right["matrix"]["active_positions"],
        pair["total_active_matrix_positions"],
    )
    print("PASS 20/19 MX, 20/19 RGB, and two encoder-click matrix positions")

    direction = freeze["matrix"]["diode_direction"]
    expect_equal("Task 3A diode direction", task3a["matrix"]["diode_direction"], direction)
    expect_equal("left diode direction", left["matrix"]["diode_direction"], direction)
    expect_equal("right diode direction", right["matrix"]["diode_direction"], direction)

    common = freeze["matrix"]["common_switches"]
    expect_equal("common switch set", sorted(set(left["matrix"]["switches"]) & set(right["matrix"]["switches"])), sorted(common))
    for sw in common:
        l = left["matrix"]["switches"][sw]
        r = right["matrix"]["switches"][sw]
        expect_equal(f"{sw} row", l["row"], r["row"])
        expect_equal(f"{sw} col", l["col"], r["col"])
        expect_equal(f"{sw} Task3A site", [l["row"], l["col"]], task3a["matrix"]["stock_sites"][sw])

    expect_equal("left-only SW22", freeze["matrix"]["left_only_switches"], ["SW22"])
    if "SW22" not in left["matrix"]["switches"] or "SW22" in right["matrix"]["switches"]:
        raise AssertionError("SW22 must exist only on the left production board")
    expect_equal(
        "SW22 Task3A site",
        [left["matrix"]["switches"]["SW22"]["row"], left["matrix"]["switches"]["SW22"]["col"]],
        task3a["matrix"]["stock_sites"]["SW22"],
    )

    enc = freeze["matrix"]["encoder_click"]
    for label, board in (("left", left), ("right", right)):
        click = board["matrix"]["encoder_click"]
        expect_equal(f"{label} encoder-click row", click["row"], enc["row"])
        expect_equal(f"{label} encoder-click col", click["col"], enc["col"])
        expect_equal(f"{label} encoder-click diode", click["diode"], enc["diode"])
    print("PASS pair matrix ownership and COL2ROW encoder clicks are coherent")

    expect_equal("left QMK rows", task3a["matrix"]["left"]["qmk_global_rows"], [0, 1, 2, 3])
    expect_equal("right QMK rows", task3a["matrix"]["right"]["qmk_global_rows"], [4, 5, 6, 7])

    expected_trrs = {
        1: freeze["split"]["trrs"]["pin_1"],
        2: freeze["split"]["trrs"]["pin_2"],
        3: freeze["split"]["trrs"]["pin_3"],
        4: freeze["split"]["trrs"]["pin_4"],
    }
    expect_equal("left TRRS", left["trrs"]["pins"], expected_trrs)
    expect_equal("right TRRS", right["trrs"]["pins"], expected_trrs)
    expect_equal("Task3A split GPIO", task3a["split"]["gpio"], freeze["split"]["controller_gpio"])
    expect_equal("Task3A split pad", task3a["split"]["controller_pad"], freeze["split"]["controller_pad"])
    expect_equal("split USB-source rule", task3a["power"]["usage_rules"]["usb_sources_while_split_connected"], freeze["power"]["usb_sources_while_split_connected"])
    print("PASS split RAW_5V/GND/SPLIT_DATA interface matches across halves")

    shared_pads = [3, 9, 10, 11, 12, 19, 20, 21, 22, 23, 24, 27, 28, 29, 30, 32]
    for pad in shared_pads:
        if pad in (25, 26):
            continue
        if pad not in (25, 26):
            if pad in ():
                pass
    for pad in [3, 9, 10, 11, 12, 19, 20, 21, 22, 23, 24, 27, 28, 29, 30, 32]:
        expect_equal(f"controller shared pad {pad}", left["controller"]["pads"][pad], right["controller"]["pads"][pad])

    expect_equal("left GP28 encoder", task3a["gpio_ownership"]["left"]["GP28"], freeze["encoders"]["left"]["GP28"])
    expect_equal("left GP29 encoder", task3a["gpio_ownership"]["left"]["GP29"], freeze["encoders"]["left"]["GP29"])
    expect_equal("right GP28 encoder", task3a["gpio_ownership"]["right"]["GP28"], freeze["encoders"]["right"]["GP28"])
    expect_equal("right GP29 encoder", task3a["gpio_ownership"]["right"]["GP29"], freeze["encoders"]["right"]["GP29"])
    expect_equal("left controller pad25", left["controller"]["pads"][25], "ENCODER_A")
    expect_equal("left controller pad26", left["controller"]["pads"][26], "ENCODER_B")
    expect_equal("right controller pad25", right["controller"]["pads"][25], "ENCODER_B")
    expect_equal("right controller pad26", right["controller"]["pads"][26], "ENCODER_A")
    print("PASS shared GPIO ownership with intentional right encoder A/B swap")

    left_chain = left["rgb"]["chain"]
    right_chain = right["rgb"]["chain"]
    expect_equal(
        "right RGB bypass",
        right_chain,
        [sw for sw in left_chain if sw != freeze["rgb"]["right_chain_is_left_chain_without"]],
    )
    expect_equal("RGB controller pad", task3a["rgb"]["controller_output_pad"], freeze["rgb"]["controller_pad"])
    expect_equal("RGB signal", left["rgb"]["input"], freeze["rgb"]["signal"])
    expect_equal("RGB signal right", right["rgb"]["input"], freeze["rgb"]["signal"])
    print("PASS right RGB chain is the left chain with only SW22 bypassed")

    pmw = freeze["pmw3360"]
    expect_equal("PMW ownership", task3a["pmw3360"]["side"], pmw["ownership"])
    for net, spec in pmw["spi"].items():
        expect_equal(f"{net} right GPIO", task3a["gpio_ownership"]["right"][spec["gpio"]], net)
        expect_equal(f"{net} right pad", right["controller"]["pads"][spec["controller_pad"]], net)
        expect_equal(f"{net} left pad unused", left["controller"]["pads"][spec["controller_pad"]], "NC")
    expect_equal("PMW header pin order", right["pmw3360"]["physical_pin_order_positive_y_to_negative_y"], pmw["header_pin_order"])
    expect_equal("PMW cable mapping", right["pmw3360"]["mating_rule"], pmw["mating_rule"])
    print("PASS PMW3360 ownership is exactly right-only")

    expect_equal(
        "removed Rev-1 feature freeze",
        task3a["removed_rev1_hardware"]["no_footprints_no_nets_no_gpio_ownership"],
        freeze["removed_rev1_hardware"]["no_footprints_no_nets_no_gpio_ownership"],
    )

    ltext = left_path.read_text(encoding="utf-8")
    rtext = right_path.read_text(encoding="utf-8")

    expected_counts = {
        "left": {
            NAMES["key"]: 20, NAMES["diode"]: 21, NAMES["controller"]: 1,
            NAMES["trrs"]: 1, NAMES["encoder"]: 1, NAMES["reset"]: 1, NAMES["pmw"]: 0,
        },
        "right": {
            NAMES["key"]: 19, NAMES["diode"]: 20, NAMES["controller"]: 1,
            NAMES["trrs"]: 1, NAMES["encoder"]: 1, NAMES["reset"]: 1, NAMES["pmw"]: 1,
        },
    }
    for label, text in (("left", ltext), ("right", rtext)):
        for name, expected in expected_counts[label].items():
            expect_equal(f"{label} {name} count", fp_count(text, name), expected)
        if re.search(r'\((?:segment|via|zone)\s', text):
            raise AssertionError(f"{label} board is no longer intentionally unrouted")

    ltrrs = pad_nets(unique_fp(ltext, NAMES["trrs"]))
    rtrrs = pad_nets(unique_fp(rtext, NAMES["trrs"]))
    expected_trrs_str = {str(k): ("" if v == "NC" else v) for k, v in expected_trrs.items()}
    for pin, net in expected_trrs_str.items():
        expect_equal(f"left generated TRRS pin {pin}", ltrrs.get(pin, ""), net)
        expect_equal(f"right generated TRRS pin {pin}", rtrrs.get(pin, ""), net)

    lctl = pad_nets(unique_fp(ltext, NAMES["controller"]))
    rctl = pad_nets(unique_fp(rtext, NAMES["controller"]))
    for pad in ["3", "9", "10", "11", "12", "19", "20", "21", "22", "23", "24", "27", "28", "29", "30", "32"]:
        expect_equal(f"generated shared controller pad {pad}", lctl.get(pad, ""), rctl.get(pad, ""))
    expect_equal("generated left encoder pad25", lctl.get("25", ""), "ENCODER_A")
    expect_equal("generated left encoder pad26", lctl.get("26", ""), "ENCODER_B")
    expect_equal("generated right encoder pad25", rctl.get("25", ""), "ENCODER_B")
    expect_equal("generated right encoder pad26", rctl.get("26", ""), "ENCODER_A")

    lnets = board_nets(ltext)
    rnets = board_nets(rtext)
    leaked = sorted(PMW_NETS & lnets)
    missing = sorted(PMW_NETS - rnets)
    if leaked:
        raise AssertionError(f"PMW nets leaked onto left generated board: {leaked}")
    if missing:
        raise AssertionError(f"right generated board missing PMW nets: {missing}")
    print("PASS generated left/right boards satisfy pair-level interface invariants")
    print("Task 3E cross-board electrical integration passed; Task 3 is electrically frozen")


if __name__ == "__main__":
    main()
