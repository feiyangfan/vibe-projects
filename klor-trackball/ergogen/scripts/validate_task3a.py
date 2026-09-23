#!/usr/bin/env python3
"""Task 3A regression gate for the frozen KLOR electrical architecture."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
KLOR = HERE.parents[2]

CONTRACT = ERGOGEN / "task3/task3a-electrical-contract.yaml"
TASK2_FREEZE = ERGOGEN / "task2/task2d-freeze.yaml"
REQUIREMENTS = KLOR / "REQUIREMENTS.md"
STOCK_PCB = KLOR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
STOCK_QMK = KLOR / "klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json"
KIVIPALLUR = (
    KLOR
    / "klorball35/kicad/Kivipallur_PMW3360_breakout/"
      "Kivipallur_PMW3360_breakout.kicad_pcb"
)


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


def footprint_table(text: str):
    result = {}
    for fp in balanced_blocks(text, "footprint"):
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', fp)
        if not ref_m:
            ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', fp)
        if not ref_m:
            continue
        pads = {}
        for m in re.finditer(
            r'\(pad\s+"([^"]+)"[\s\S]*?\(net\s+\d+\s+"([^"]*)"\)',
            fp,
        ):
            pads[m.group(1)] = m.group(2)
        result[ref_m.group(1)] = pads
    return result


def matrix_site_from_stock(ref: str, fps: dict[str, dict[str, str]]):
    sw = fps[ref]
    diode = fps["D" + ref.removeprefix("SW")]
    col = sw["5"].upper()
    row = diode["1"].upper()
    return [row, col]


def derive_stock_rgb_chain(fps: dict[str, dict[str, str]]):
    din_owner = {}
    for ref, pads in fps.items():
        if not re.fullmatch(r"SW\d+", ref):
            continue
        if "3" in pads:
            din_owner[pads["3"]] = ref

    chain = []
    current_net = "LED"
    seen = set()
    while current_net in din_owner:
        ref = din_owner[current_net]
        if ref in seen:
            raise AssertionError("cycle in stock RGB chain")
        seen.add(ref)
        chain.append(ref)
        current_net = fps[ref]["1"]
    return chain


def assert_gpio_unique(side: str, mapping: dict[str, str]):
    seen = {}
    for gpio, owner in mapping.items():
        if gpio in seen:
            raise AssertionError(f"{side}: duplicate GPIO {gpio}")
        seen[gpio] = owner
    print(f"PASS {side} GPIO ownership unique across {len(mapping)} active GPIOs")


def main():
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    freeze = yaml.safe_load(TASK2_FREEZE.read_text(encoding="utf-8"))
    req = REQUIREMENTS.read_text(encoding="utf-8")
    stock_text = STOCK_PCB.read_text(encoding="utf-8")
    kiv_text = KIVIPALLUR.read_text(encoding="utf-8")
    fps = footprint_table(stock_text)
    kiv_fps = footprint_table(kiv_text)

    if freeze["status"] != "task2d_frozen":
        raise AssertionError("Task 2 must be frozen before Task 3A")
    if (
        freeze["product_geometry"]["left_keys"],
        freeze["product_geometry"]["right_keys"],
        freeze["product_geometry"]["total_keys"],
    ) != (20, 19, 39):
        raise AssertionError("Task-2 key-count freeze changed")
    print("PASS Task-2D geometry dependency is frozen at 20/19/39")

    if contract["status"] not in {"task3a_frozen_candidate", "task3a_frozen"}:
        raise AssertionError(f"unexpected Task-3A status: {contract['status']}")
    ctrl = contract["controller"]
    expected_controller = {
        "model": "0xCB Helios",
        "hardware_revision": "rev1.0",
        "mcu": "RP2040",
        "qmk_board": "0xcb/helios",
        "source_repository": "0xCB-dev/0xCB-Helios",
        "source_commit": "e1a25eb5e4b1bcb25e13dcb18bd6e841dcf7be11",
    }
    for key, value in expected_controller.items():
        if ctrl[key] != value:
            raise AssertionError(f"controller {key} changed: {ctrl[key]!r}")
    print("PASS production controller frozen to audited Helios rev1.0 source")

    pads = ctrl["audited_pads"]
    expected_pad_map = {
        "GP1": 3, "GP2": 6, "GP3": 7, "GP4": 8,
        "GP5": 9, "GP6": 10, "GP7": 11, "GP8": 12, "GP9": 13,
        "GP21": 19, "GP23": 20, "GP20": 21, "GP22": 22,
        "GP26": 23, "GP27": 24, "GP28": 25, "GP29": 26,
        "3V3": 27, "RESET": 28, "GND": 29, "RAW_5V": 30,
        "GP11": 31, "GP25_SHIFTED": 32,
    }
    for signal, pad in expected_pad_map.items():
        if int(pads[signal]["pad"]) != pad:
            raise AssertionError(f"Helios audited pad drift: {signal}")
    if pads["GP25_SHIFTED"]["mcu_gpio"] != "GP25":
        raise AssertionError("level-shifted RGB pad no longer sourced by GP25")
    print("PASS audited Helios pad contract")

    power = contract["power"]
    if power["controller_configuration"]["helios_jp2_default_bridge"] != [1, 2]:
        raise AssertionError("Helios RAW/+5V bridge assumption changed")
    if power["rails"]["RAW_5V"]["nominal_voltage"] != 5:
        raise AssertionError("RAW_5V voltage changed")
    if float(power["rails"]["V3V3"]["nominal_voltage"]) != 3.3:
        raise AssertionError("V3V3 voltage changed")
    if power["usage_rules"]["usb_sources_while_split_connected"] != 1:
        raise AssertionError("split USB-source safety rule changed")
    if power["usage_rules"]["powered_TRRS_hotplug_supported"] is not False:
        raise AssertionError("powered TRRS hotplug must remain unsupported")
    if not power["rgb_budget"]["firmware_brightness_limit_required"]:
        raise AssertionError("RGB power-budget guard removed")
    print("PASS power domains and powered-TRRS safety contract")

    matrix = contract["matrix"]
    if matrix["diode_direction"] != "COL2ROW":
        raise AssertionError("matrix diode direction changed")
    expected_rows = {
        "ROW0": ("GP5", 9),
        "ROW1": ("GP6", 10),
        "ROW2": ("GP7", 11),
        "ROW3": ("GP8", 12),
    }
    expected_cols = {
        "COL0": ("GP27", 24),
        "COL1": ("GP26", 23),
        "COL2": ("GP22", 22),
        "COL3": ("GP20", 21),
        "COL4": ("GP23", 20),
        "COL5": ("GP21", 19),
    }
    for name, (gpio, pad) in expected_rows.items():
        if matrix["rows"][name] != {"gpio": gpio, "controller_pad": pad}:
            raise AssertionError(f"{name} ownership changed")
    for name, (gpio, pad) in expected_cols.items():
        if matrix["columns"][name] != {"gpio": gpio, "controller_pad": pad}:
            raise AssertionError(f"{name} ownership changed")

    stock_refs = [*(f"SW{i}" for i in range(1, 18)), "SW20", "SW21", "SW22"]
    for ref in stock_refs:
        actual = matrix["stock_sites"][ref]
        expected = matrix_site_from_stock(ref, fps)
        if actual != expected:
            raise AssertionError(f"{ref} matrix site {actual} != stock {expected}")
    sw18 = fps["SW18"]
    d18 = fps["D18"]
    if matrix["stock_sites"]["ENCODER_CLICK"] != [d18["1"].upper(), sw18["S1"].upper()]:
        raise AssertionError("encoder-click matrix site no longer matches stock")
    print("PASS matrix sites derived from stock PCB")

    left_mx = matrix["left"]["mx_switches"]
    right_mx = matrix["right"]["mx_switches"]
    if len(left_mx) != 20 or len(set(left_mx)) != 20:
        raise AssertionError("left MX set must contain exactly 20 unique switches")
    if len(right_mx) != 19 or len(set(right_mx)) != 19:
        raise AssertionError("right MX set must contain exactly 19 unique switches")
    if "SW19" in left_mx or "SW19" in right_mx:
        raise AssertionError("alternate-layout SW19 returned")
    if "SW22" not in left_mx or "SW22" in right_mx:
        raise AssertionError("R34/SW22 side-specific occupancy changed")
    if matrix["left"]["active_matrix_positions"] != 21:
        raise AssertionError("left matrix position count must include encoder push")
    if matrix["right"]["active_matrix_positions"] != 20:
        raise AssertionError("right matrix position count must include encoder push")
    print("PASS 39 MX + 2 encoder-push matrix-position accounting")

    enc = contract["encoders"]
    if enc["click"] != {"column": "COL5", "row": "ROW3", "diode_direction": "COL2ROW"}:
        raise AssertionError("encoder-click electrical contract changed")
    if enc["left_rotary"] != {"A": "GP28", "B": "GP29", "common": "GND"}:
        raise AssertionError("left encoder rotary contract changed")
    if enc["right_rotary"]["A"] != "GP29" or enc["right_rotary"]["B"] != "GP28":
        raise AssertionError("right encoder A/B reversal changed")
    print("PASS encoder rotary + push contracts")

    split = contract["split"]
    expected_trrs = {
        "pin_1": "RAW_5V",
        "pin_2": "GND",
        "pin_3": "NC",
        "pin_4": "SPLIT_DATA",
    }
    if split["transport"] != "half_duplex_serial" or split["gpio"] != "GP1":
        raise AssertionError("split transport changed")
    if split["trrs"] != expected_trrs:
        raise AssertionError("TRRS pin contract changed")
    print("PASS half-duplex TRRS contract")

    rgb = contract["rgb"]
    stock_chain = derive_stock_rgb_chain(fps)
    if stock_chain[0] != "SW19":
        raise AssertionError(f"unexpected stock RGB chain start: {stock_chain}")
    fixed_chain = [ref for ref in stock_chain if ref != "SW19"]
    right_chain = [ref for ref in fixed_chain if ref != "SW22"]
    if rgb["left"]["chain"] != fixed_chain or rgb["left"]["count"] != 20:
        raise AssertionError("left RGB chain no longer derives from fixed-Konrad stock chain")
    if rgb["right"]["chain"] != right_chain or rgb["right"]["count"] != 19:
        raise AssertionError("right RGB chain no longer bypasses SW22 exactly")
    if rgb["controller_gpio"] != "GP25" or rgb["controller_output_pad"] != 32:
        raise AssertionError("RGB controller ownership changed")
    if rgb["electrical_output"] != "5V_level_shifted_on_Helios":
        raise AssertionError("RGB level-shifter contract removed")
    print("PASS left/right RGB chains and 5V level-shifted data contract")

    pmw = contract["pmw3360"]
    expected_spi = {
        "SCK": {"gpio": "GP2", "controller_pad": 6},
        "MOSI": {"gpio": "GP3", "controller_pad": 7},
        "MISO": {"gpio": "GP4", "controller_pad": 8},
        "CS": {"gpio": "GP9", "controller_pad": 13},
    }
    if pmw["side"] != "right_only" or pmw["spi"] != expected_spi:
        raise AssertionError("PMW SPI ownership changed")
    if pmw["motion"]["electrical_state"] != "NC":
        raise AssertionError("PMW MOTION unexpectedly enabled")

    kiv = kiv_fps["J1"]
    expected_breakout = {
        1: "GND",
        2: "+3V3",
        3: "/MOTION",
        4: "/SCK",
        5: "/MOSI",
        6: "/MISO",
        7: "/CS",
    }
    for pin, net in expected_breakout.items():
        if kiv[str(pin)] != net:
            raise AssertionError(f"Kivipallur source pin {pin} changed: {kiv[str(pin)]}")

    keyboard = {int(k): v for k, v in pmw["keyboard_header"]["pin_order"].items()}
    expected_keyboard = {
        1: "PMW_CS",
        2: "PMW_MISO",
        3: "PMW_MOSI",
        4: "PMW_SCK",
        5: "NC_MOTION",
        6: "V3V3",
        7: "GND",
    }
    if keyboard != expected_keyboard:
        raise AssertionError("keyboard-side PMW header order changed")
    if pmw["keyboard_header"]["mating_rule"] != "breakout_pin_N_to_keyboard_pin_8_minus_N":
        raise AssertionError("PMW mating rule changed")
    print("PASS Kivipallur source and reversed keyboard-side pin contract")

    for side in ("left", "right"):
        assert_gpio_unique(side, contract["gpio_ownership"][side])
    if set(contract["gpio_ownership"]["left"]) & {"GP2", "GP3", "GP4", "GP9"}:
        raise AssertionError("left side unexpectedly owns PMW GPIOs")
    if {
        "GP2": "PMW_SCK",
        "GP3": "PMW_MOSI",
        "GP4": "PMW_MISO",
        "GP9": "PMW_CS",
    }.items() - contract["gpio_ownership"]["right"].items():
        raise AssertionError("right-side PMW GPIO ownership incomplete")
    print("PASS side-specific PMW ownership")

    removed = set(contract["removed_rev1_hardware"]["no_footprints_no_nets_no_gpio_ownership"])
    required_removed = {
        "OLED",
        "DRV2605L_haptic",
        "buzzer_audio",
        "PAW3204",
        "general_I2C_accessories",
        "battery_connector",
        "battery_operation",
        "hardware_power_switch",
        "full_duplex_RX",
        "alternate_layout_SW19",
    }
    if not required_removed.issubset(removed):
        raise AssertionError("Rev-1 removed-hardware list incomplete")
    print("PASS removed stock features own no Rev-1 electrical interface")

    required_req_text = [
        "Selected controller: **0xCB Helios rev1.0**.",
        "RGB: **GP25 through the Helios onboard 5 V level shifter**;",
        "regulated 3.3 V from each Helios for the right-side PMW3360 breakout;",
    ]
    for phrase in required_req_text:
        if phrase not in req:
            raise AssertionError(f"REQUIREMENTS.md missing Task-3A freeze text: {phrase}")
    if "RGB: GP0;" in req:
        raise AssertionError("obsolete GP0 preferred baseline remains in requirements")
    print("PASS REQUIREMENTS.md updated to Task-3A electrical freeze")

    if contract["task3b_handoff"]["routing"] != "forbidden_until_task4":
        raise AssertionError("Task 3 accidentally claimed routing")
    print("PASS routing remains outside Task 3")

    print("Task 3A electrical architecture gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
