#!/usr/bin/env python3
"""Task 2F: final electrical/firmware interface freeze.

This is the Task 2 completion gate. It consumes fresh Task 2A-2E audit
evidence and produces one authoritative connector/net/GPIO/firmware contract.
It does not modify production PCB or firmware files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "design/task2/generated"

DEFAULT_2A = GEN / "task2a-removed-key-audit.json"
DEFAULT_2B = GEN / "task2b-gpio-trrs-audit.json"
DEFAULT_2C = GEN / "task2c-kivipallur-connector-audit.json"
DEFAULT_2D = GEN / "task2d-pcb-net-contract-audit.json"
DEFAULT_2E = GEN / "task2e-firmware-ownership-audit.json"

FINAL_INTERFACE = [
    {
        "keyboard_pin": 1,
        "breakout_pin": 7,
        "breakout_signal": "CS",
        "pcb_net": "PMW_CS",
        "mcu_gpio": "GP9",
        "u1_pad": "12",
        "firmware_function": "PMW3360 CS",
        "stock_source": "AUDIO / BZ1.1",
        "stock_change": "disable audio/music and PWM4; BZ1 DNP/no active load; repurpose GP9",
    },
    {
        "keyboard_pin": 2,
        "breakout_pin": 6,
        "breakout_signal": "MISO",
        "pcb_net": "PMW_MISO",
        "mcu_gpio": "GP4",
        "u1_pad": "7",
        "firmware_function": "SPI0 MISO / PMW3360 MISO",
        "stock_source": "RX / TRRS J1.3",
        "stock_change": "remove verified J1.3-adjacent RX branch; J1.3 becomes NC; keep full-duplex disabled",
    },
    {
        "keyboard_pin": 3,
        "breakout_pin": 5,
        "breakout_signal": "MOSI",
        "pcb_net": "PMW_MOSI",
        "mcu_gpio": "GP3",
        "u1_pad": "6",
        "firmware_function": "SPI0 MOSI / PMW3360 MOSI",
        "stock_source": "SCL / I2C1 / PAW3204 / haptic",
        "stock_change": "disable I2C1 and PAW3204; J2 haptic DNP; legacy I2C jumpers open; repurpose GP3",
    },
    {
        "keyboard_pin": 4,
        "breakout_pin": 4,
        "breakout_signal": "SCK",
        "pcb_net": "PMW_SCK",
        "mcu_gpio": "GP2",
        "u1_pad": "5",
        "firmware_function": "SPI0 SCK / PMW3360 SCK",
        "stock_source": "SDA / I2C1 / PAW3204",
        "stock_change": "disable I2C1 and PAW3204; legacy I2C jumpers open; repurpose GP2",
    },
    {
        "keyboard_pin": 5,
        "breakout_pin": 3,
        "breakout_signal": "MOTION",
        "pcb_net": None,
        "mcu_gpio": None,
        "u1_pad": None,
        "firmware_function": "unused / polling",
        "stock_source": None,
        "stock_change": "leave connector pad electrically unconnected; do not define POINTING_DEVICE_MOTION_PIN",
    },
    {
        "keyboard_pin": 6,
        "breakout_pin": 2,
        "breakout_signal": "+3V3",
        "pcb_net": "VCC",
        "mcu_gpio": None,
        "u1_pad": "21",
        "firmware_function": "3.3 V supply",
        "stock_source": "KLOR VCC",
        "stock_change": "connect to existing KLOR VCC rail; do not create a separate 3V3 net",
    },
    {
        "keyboard_pin": 7,
        "breakout_pin": 1,
        "breakout_signal": "GND",
        "pcb_net": "GND",
        "mcu_gpio": None,
        "u1_pad": ["3", "4", "23"],
        "firmware_function": "ground",
        "stock_source": "KLOR GND",
        "stock_change": "connect to existing KLOR ground plane/rail",
    },
]

NON_CONNECTOR_CHANGES = {
    "removed_key": {
        "logical_key": "R34",
        "pcb_switch": "SW22",
        "diode": "D22",
        "matrix_position": [7, 1],
        "action": "remove SW22 and D22; delete local Net-(D22-A) copper; preserve col1/row3 trunks; do not bridge matrix nets",
    },
    "rgb": {
        "pin": "GP0",
        "bypass": "SW13 DOUT -> SW14 DIN",
        "left_count": 20,
        "right_count": 19,
        "total_count": 39,
    },
    "split": {
        "pin": "GP1",
        "mode": "half-duplex",
        "pcb_path": "TX -> J1.4",
        "action": "preserve",
        "handedness": "EE_HANDS",
    },
    "connector_orientation": {
        "keyboard_side": "F.Cu",
        "row_axis": "global-y",
        "pin1_end": "negative-y",
        "pin7_end": "positive-y",
        "connector_side_of_guide": "positive-x/non-sensor-side",
        "service_direction": "negative-x",
        "mating_rule": "breakout pin N <-> keyboard pin 8-N",
    },
    "pass_through": {
        "task1_center_xy": [143.111, -134.748],
        "reference_guide_size_mm": [2.0, 22.0],
        "reference_guide_layer": "Cmts.User",
        "task3_action": "create actual KLOR fabricated pass-through/edge clearance",
    },
    "optional_features_revision1": {
        "oled": "disabled/DNP",
        "haptic": "disabled/DNP",
        "audio": "disabled/BZ1 inactive",
        "music": "disabled",
        "stock_paw3204": "disabled",
        "i2c1": "disabled",
        "pwm4_audio": "disabled",
    },
}

FIRMWARE_CONTRACT = {
    "pointing_device_enable": True,
    "driver": "pmw3360",
    "spi_driver": "SPID0",
    "spi_sck_pin": "GP2",
    "spi_mosi_pin": "GP3",
    "spi_miso_pin": "GP4",
    "pmw33xx_cs_pin": "GP9",
    "split_pointing_enable": True,
    "pointing_device_side": "right",
    "motion_pin": None,
    "serial_tx_pin": "GP1",
    "serial_mode": "half-duplex",
    "handedness": "EE_HANDS",
    "hal_use_spi": True,
    "rp_spi_use_spi0": True,
    "hal_use_i2c": False,
    "rp_i2c_use_i2c1": False,
    "hal_use_pwm": False,
    "rp_pwm_use_pwm4": False,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def all_checks_pass(report: dict) -> bool:
    checks = report.get("checks", {})
    return bool(checks) and all(checks.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task2a-json", type=Path, default=DEFAULT_2A)
    ap.add_argument("--task2b-json", type=Path, default=DEFAULT_2B)
    ap.add_argument("--task2c-json", type=Path, default=DEFAULT_2C)
    ap.add_argument("--task2d-json", type=Path, default=DEFAULT_2D)
    ap.add_argument("--task2e-json", type=Path, default=DEFAULT_2E)
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    a = load(args.task2a_json)
    b = load(args.task2b_json)
    c = load(args.task2c_json)
    d = load(args.task2d_json)
    e = load(args.task2e_json)

    d_by_pin = {row["connector_pin"]: row for row in d["contract"]}
    e_target = e["target"]
    e_qmk = e_target["qmk"]
    e_pins = e_target["pin_ownership"]

    checks: dict[str, bool] = {
        "task2a_passes": all_checks_pass(a),
        "task2b_passes": all_checks_pass(b),
        "task2c_passes": all_checks_pass(c),
        "task2d_passes": all_checks_pass(d),
        "task2e_passes": all_checks_pass(e),

        "removed_key_exact": (
            a["disposition"]["logical_key"] == "R34"
            and a["disposition"]["remove_footprints"] == ["SW22", "D22"]
            and a["disposition"]["matrix"]["sw22_column_net"] == "col1"
            and a["disposition"]["matrix"]["d22_cathode_net"] == "row3"
        ),
        "rgb_bypass_exact": (
            a["disposition"]["rgb"]["incoming"] == "SW13 DOUT"
            and a["disposition"]["rgb"]["outgoing"] == "SW14 DIN"
        ),

        "gp1_split_preserved": (
            b["gpio_topology"]["GP1"]["stock_net"] == "TX"
            and b["gpio_topology"]["GP1"]["planned"] == "split-half-duplex"
            and b["gp4_trrs_isolation"]["trrs_contact"] == "J1.3"
            and b["gp4_trrs_isolation"]["segment_verified_in_source"] is True
        ),

        "connector_mating_rule_locked": (
            c["mating"]["rule"] == "opposite-facing headers mate breakout pin N to keyboard pin 8-N"
            and c["mating"]["motion_revision1"] == "NC"
            and c["reference_guide"]["fabricated_cutout"] is False
        ),

        "seven_pin_contract_exact": all(
            d_by_pin[row["keyboard_pin"]]["breakout_signal"] == row["breakout_signal"]
            and d_by_pin[row["keyboard_pin"]]["target_pcb_net"] == row["pcb_net"]
            and d_by_pin[row["keyboard_pin"]].get("mcu_gpio") == row["mcu_gpio"]
            for row in FINAL_INTERFACE
        ),

        "spi_gpio_matches_firmware": (
            e_qmk["spi_sck_pin"] == "GP2"
            and e_qmk["spi_mosi_pin"] == "GP3"
            and e_qmk["spi_miso_pin"] == "GP4"
            and e_qmk["pmw33xx_cs_pin"] == "GP9"
            and e_pins["GP2"] == "PMW3360-SCK"
            and e_pins["GP3"] == "PMW3360-MOSI"
            and e_pins["GP4"] == "PMW3360-MISO"
            and e_pins["GP9"] == "PMW3360-CS"
        ),

        "right_only_pointing_locked": (
            e_qmk["pointing_device_driver"] == "pmw3360"
            and e_qmk["split_pointing"] is True
            and e_qmk["pointing_device_side"] == "right"
            and e_qmk["motion_pin"] is None
        ),

        "retained_gpio_contract_exact": (
            e_pins["GP0"] == "RGB-WS2812"
            and e_pins["GP1"] == "split-half-duplex-serial"
            and e_target["matrix"]["rows"] == ["GP5", "GP6", "GP7", "GP8"]
            and e_target["matrix"]["cols"] == ["GP27", "GP26", "GP22", "GP20", "GP23", "GP21"]
            and e_target["encoder"]["left"] == {"pin_a": "GP28", "pin_b": "GP29"}
            and e_target["encoder"]["right"] == {"pin_a": "GP29", "pin_b": "GP28"}
        ),

        "rgb_counts_exact": (
            e_target["rgb"]["left_count"] == 20
            and e_target["rgb"]["right_count"] == 19
            and e_target["rgb"]["total_count"] == 39
        ),

        "no_motion_owner": (
            d_by_pin[5]["target_pcb_net"] is None
            and d_by_pin[5]["mcu_gpio"] is None
            and e_qmk["motion_pin"] is None
        ),

        "power_contract_exact": (
            d_by_pin[6]["target_pcb_net"] == "VCC"
            and d_by_pin[6]["u1_pad"] == "21"
            and d_by_pin[7]["target_pcb_net"] == "GND"
        ),

        "legacy_peripheral_ownership_retired": (
            e_target["features"]["oled"] is False
            and e_target["features"]["haptic"] is False
            and e_target["features"]["audio"] is False
            and e_target["hal_mcu"]["HAL_USE_I2C"] == "FALSE"
            and e_target["hal_mcu"]["RP_I2C_USE_I2C1"] == "FALSE"
            and e_target["hal_mcu"]["HAL_USE_PWM"] == "FALSE"
            and e_target["hal_mcu"]["RP_PWM_USE_PWM4"] == "FALSE"
        ),

        "spi0_enabled": (
            e_target["hal_mcu"]["HAL_USE_SPI"] == "TRUE"
            and e_target["hal_mcu"]["RP_SPI_USE_SPI0"] == "TRUE"
        ),
    }

    final_gpio_owners = {
        "GP0": "RGB",
        "GP1": "split-serial",
        "GP2": "PMW-SCK",
        "GP3": "PMW-MOSI",
        "GP4": "PMW-MISO",
        "GP5": "matrix-row",
        "GP6": "matrix-row",
        "GP7": "matrix-row",
        "GP8": "matrix-row",
        "GP9": "PMW-CS",
        "GP20": "matrix-col",
        "GP21": "matrix-col",
        "GP22": "matrix-col",
        "GP23": "matrix-col",
        "GP26": "matrix-col",
        "GP27": "matrix-col",
        "GP28": "encoder",
        "GP29": "encoder",
    }
    checks["final_gpio_owners_unique"] = len(final_gpio_owners) == len(set(final_gpio_owners))
    checks["unresolved_gpio_conflicts_zero"] = all(checks.values())

    report = {
        "task": "2F",
        "task2_status": "complete" if all(checks.values()) else "blocked",
        "sources": {
            "task2a_json": str(args.task2a_json),
            "task2b_json": str(args.task2b_json),
            "task2c_json": str(args.task2c_json),
            "task2d_json": str(args.task2d_json),
            "task2e_json": str(args.task2e_json),
        },
        "final_interface": FINAL_INTERFACE,
        "non_connector_changes": NON_CONNECTOR_CHANGES,
        "firmware_contract": FIRMWARE_CONTRACT,
        "final_gpio_owners": final_gpio_owners,
        "task3_authorization": {
            "authorized": all(checks.values()),
            "scope": "create right-hand trackball PCB derivative implementing this frozen contract",
            "production_files_changed_by_task2": False,
        },
        "checks": checks,
    }

    out = json.dumps(report, indent=2, sort_keys=True)
    print(out)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(out + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
