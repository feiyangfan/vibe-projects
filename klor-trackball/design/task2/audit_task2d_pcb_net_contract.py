#!/usr/bin/env python3
"""Task 2D: compose the source-backed PMW3360 PCB net contract.

This audit consumes fresh Task 2B and 2C JSON evidence, then checks the stock
KLOR U1 power rails directly. It freezes the target net names that Task 3 must
implement without editing production geometry in Task 2.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_task2b_gpio_trrs import electrical_pads, parse_footprints

ROOT = Path(__file__).resolve().parents[2]
PCB = ROOT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
DEFAULT_2B = ROOT / "design/task2/generated/task2b-gpio-trrs-audit.json"
DEFAULT_2C = ROOT / "design/task2/generated/task2c-kivipallur-connector-audit.json"

CONTRACT = [
    {
        "connector_pin": 1,
        "breakout_signal": "CS",
        "target_pcb_net": "PMW_CS",
        "mcu_gpio": "GP9",
        "u1_pad": "12",
        "stock_source_net": "AUDIO",
        "stock_source_net_id": 2,
        "required_disposition": "disable audio; BZ1 DNP/no active load; repurpose U1 pad 12 to PMW_CS",
    },
    {
        "connector_pin": 2,
        "breakout_signal": "MISO",
        "target_pcb_net": "PMW_MISO",
        "mcu_gpio": "GP4",
        "u1_pad": "7",
        "stock_source_net": "RX",
        "stock_source_net_id": 28,
        "required_disposition": "isolate TRRS J1.3 using the Task 2B-verified F.Cu branch; repurpose U1 pad 7 to PMW_MISO",
    },
    {
        "connector_pin": 3,
        "breakout_signal": "MOSI",
        "target_pcb_net": "PMW_MOSI",
        "mcu_gpio": "GP3",
        "u1_pad": "6",
        "stock_source_net": "SCL",
        "stock_source_net_id": 7,
        "required_disposition": "disable I2C/PAW3204; J2 haptic DNP; keep legacy I2C jumpers open; repurpose U1 pad 6 to PMW_MOSI",
    },
    {
        "connector_pin": 4,
        "breakout_signal": "SCK",
        "target_pcb_net": "PMW_SCK",
        "mcu_gpio": "GP2",
        "u1_pad": "5",
        "stock_source_net": "SDA",
        "stock_source_net_id": 6,
        "required_disposition": "disable I2C/PAW3204; keep legacy I2C jumpers open; repurpose U1 pad 5 to PMW_SCK",
    },
    {
        "connector_pin": 5,
        "breakout_signal": "MOTION",
        "target_pcb_net": None,
        "mcu_gpio": None,
        "u1_pad": None,
        "stock_source_net": None,
        "stock_source_net_id": None,
        "required_disposition": "NC for revision 1; no routed trace, test pad, or MCU assignment; connector pad remains electrically unconnected",
    },
    {
        "connector_pin": 6,
        "breakout_signal": "+3V3",
        "target_pcb_net": "VCC",
        "mcu_gpio": None,
        "mcu_signal": "U1.VCC",
        "u1_pad": "21",
        "stock_source_net": "VCC",
        "stock_source_net_id": 3,
        "required_disposition": "connect directly to the existing KLOR VCC rail; selected Elite-Pi uses this rail as 3.3 V",
    },
    {
        "connector_pin": 7,
        "breakout_signal": "GND",
        "target_pcb_net": "GND",
        "mcu_gpio": None,
        "mcu_signal": "U1.GND",
        "u1_pads": ["3", "4", "23"],
        "stock_source_net": "GND",
        "stock_source_net_id": 1,
        "required_disposition": "connect directly to the existing KLOR ground plane/rail",
    },
]

EXPECTED_2C_RIGHT = {
    "1": "/CS",
    "2": "/MISO",
    "3": "/MOSI",
    "4": "/SCK",
    "5": "unconnected-(J2-Pin_5-Pad5)",
    "6": "+3V3",
    "7": "GND",
}

GPIO_BY_PIN = {
    1: "GP9",
    2: "GP4",
    3: "GP3",
    4: "GP2",
}


def one_pad(controller: dict, number: str) -> dict:
    matches = [p for p in electrical_pads(controller) if p["number"] == number]
    if len(matches) != 1:
        raise ValueError(f"U1 pad {number}: expected one electrical pad, found {len(matches)}")
    return matches[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task2b-json", type=Path, default=DEFAULT_2B)
    ap.add_argument("--task2c-json", type=Path, default=DEFAULT_2C)
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    two_b = json.loads(args.task2b_json.read_text(encoding="utf-8"))
    two_c = json.loads(args.task2c_json.read_text(encoding="utf-8"))

    pcb_text = PCB.read_text(encoding="utf-8")
    footprints = parse_footprints(pcb_text)
    controllers = [fp for fp in footprints if fp["ref"] == "U1"]
    if len(controllers) != 1:
        raise ValueError(f"expected one U1 controller footprint, found {len(controllers)}")
    controller = controllers[0]

    u1_power = {
        "VCC": one_pad(controller, "21"),
        "GND_3": one_pad(controller, "3"),
        "GND_4": one_pad(controller, "4"),
        "GND_23": one_pad(controller, "23"),
    }

    checks: dict[str, bool] = {
        "task2b_dependency_passes": bool(two_b.get("checks")) and all(two_b["checks"].values()),
        "task2c_dependency_passes": bool(two_c.get("checks")) and all(two_c["checks"].values()),
        "elite_pi_selected": two_b.get("firmware_claims", {}).get("development_board") == "elite_pi",
        "task2c_keyboard_pin_order_exact": two_c.get("reference_right", {}).get("pin_map") == EXPECTED_2C_RIGHT,
        "task2c_motion_is_nc": two_c.get("mating", {}).get("motion_revision1") == "NC",
        "stock_u1_vcc_pad21_is_vcc_net3": (
            u1_power["VCC"].get("net") == "VCC"
            and u1_power["VCC"].get("net_id") == 3
        ),
        "stock_u1_ground_pads_are_gnd_net1": all(
            u1_power[name].get("net") == "GND" and u1_power[name].get("net_id") == 1
            for name in ("GND_3", "GND_4", "GND_23")
        ),
    }

    gpio_topology = two_b.get("gpio_topology", {})
    for row in CONTRACT:
        pin = row["connector_pin"]
        gpio = GPIO_BY_PIN.get(pin)
        if not gpio:
            continue
        source = gpio_topology.get(gpio, {})
        checks[f"pin{pin}_{gpio.lower()}_source_matches"] = (
            source.get("pad") == row["u1_pad"]
            and source.get("stock_net") == row["stock_source_net"]
            and source.get("net_id") == row["stock_source_net_id"]
        )

    target_nets = [row["target_pcb_net"] for row in CONTRACT if row["target_pcb_net"]]
    signal_nets = [row["target_pcb_net"] for row in CONTRACT[:4]]
    checks["four_spi_target_nets_unique"] = len(signal_nets) == len(set(signal_nets)) == 4
    checks["motion_has_no_target_net"] = CONTRACT[4]["target_pcb_net"] is None and CONTRACT[4]["mcu_gpio"] is None
    checks["power_uses_stock_vcc_not_invented_3v3_net"] = CONTRACT[5]["target_pcb_net"] == "VCC"
    checks["ground_uses_stock_gnd"] = CONTRACT[6]["target_pcb_net"] == "GND"
    checks["all_seven_connector_pins_accounted_for"] = [row["connector_pin"] for row in CONTRACT] == list(range(1, 8))
    checks["no_duplicate_target_net_except_none"] = len(target_nets) == len(set(target_nets))

    report = {
        "task": "2D",
        "sources": {
            "task2b_json": str(args.task2b_json),
            "task2c_json": str(args.task2c_json),
            "stock_pcb": str(PCB.relative_to(ROOT)),
        },
        "contract": CONTRACT,
        "stock_u1_power": u1_power,
        "naming_rules": {
            "spi_target_nets": ["PMW_CS", "PMW_MISO", "PMW_MOSI", "PMW_SCK"],
            "motion": "NC",
            "breakout_3v3_maps_to_stock_klor_net": "VCC",
            "ground": "GND",
            "rule": "Task 3 must not retain AUDIO/RX/SCL/SDA as semantic names for the reassigned PMW signal nets.",
        },
        "checks": checks,
    }

    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(output + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
