#!/usr/bin/env python3
"""Task 2B: audit KLOR GPIO ownership and split/TRRS routing.

Read-only audit over the stock KLOR 1.4 KiCad PCB and QMK configuration.
It resolves the Elite-Pi/RP2040 GPIOs proposed for the PMW3360 against the
Pro-Micro-compatible controller footprint, reports every PCB endpoint sharing
those nets, inventories jumper/connector/buzzer topology, and records stock
firmware claims.

This script does not modify production PCB or firmware files.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PCB = ROOT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
CONFIG = ROOT / "klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/config.h"
KEYBOARD_JSON = ROOT / "klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json"

# Elite-Pi uses the RP2040 Community Edition / Pro-Micro-compatible pinout.
# These are the Pro Micro socket aliases represented by the stock KLOR U1
# symbol/footprint. Only the pins needed by Task 2B are enumerated here.
GPIO_TO_PROMICRO_ALIAS = {
    "GP1": ("RX1/D2", "D2"),
    "GP2": ("2/D1/SDA", "D1/SDA", "SDA"),
    "GP3": ("3/D0/SCL", "D0/SCL", "SCL"),
    "GP4": ("4/D4", "D4"),
    "GP9": ("9/B5", "B5"),
}

TARGET_GPIOS = ("GP1", "GP2", "GP3", "GP4", "GP9")


def balanced_block(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError(f"unterminated S-expression at offset {start}")


def blocks(text: str, token: str) -> Iterable[str]:
    pat = re.compile(r"\(" + re.escape(token) + r"(?=\s|\()")
    pos = 0
    while True:
        match = pat.search(text, pos)
        if not match:
            return
        block = balanced_block(text, match.start())
        yield block
        pos = match.start() + len(block)


def qprop(block: str, name: str) -> str | None:
    match = re.search(r'\(property\s+"' + re.escape(name) + r'"\s+"([^"]*)"', block)
    return match.group(1) if match else None


def atom(block: str, name: str) -> str | None:
    match = re.search(r"\(" + re.escape(name) + r'\s+(?:"([^"]*)"|([^\s()]+))', block)
    if not match:
        return None
    return match.group(1) if match.group(1) is not None else match.group(2)


def first_at(block: str) -> list[float] | None:
    match = re.search(
        r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?\)",
        block,
    )
    if not match:
        return None
    return [float(v) for v in match.groups() if v is not None]


def xy(block: str, name: str) -> list[float] | None:
    match = re.search(
        r"\(" + re.escape(name) + r"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)",
        block,
    )
    return [float(match.group(1)), float(match.group(2))] if match else None


def absolute_pad_xy(fp_at: list[float] | None, pad_at: list[float] | None) -> list[float] | None:
    if not fp_at or not pad_at:
        return None
    theta = math.radians(fp_at[2] if len(fp_at) > 2 else 0.0)
    x, y = pad_at[0], pad_at[1]
    return [
        round(fp_at[0] + x * math.cos(theta) - y * math.sin(theta), 6),
        round(fp_at[1] + x * math.sin(theta) + y * math.cos(theta), 6),
    ]


def parse_pads(fp_block: str, fp_at: list[float] | None) -> list[dict]:
    out = []
    for pad_block in blocks(fp_block, "pad"):
        match = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pad_block)
        if not match:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pad_block)
        pinfunction = re.search(r'\(pinfunction\s+"([^"]*)"\)', pad_block)
        pintype = re.search(r'\(pintype\s+"([^"]*)"\)', pad_block)
        pad_at = first_at(pad_block)
        out.append(
            {
                "number": match.group(1),
                "type": match.group(2),
                "shape": match.group(3),
                "at": pad_at,
                "absolute_xy": absolute_pad_xy(fp_at, pad_at),
                "net_id": int(net.group(1)) if net else None,
                "net": net.group(2) if net else None,
                "pinfunction": pinfunction.group(1) if pinfunction else None,
                "pintype": pintype.group(1) if pintype else None,
            }
        )
    return out


def parse_footprints(text: str) -> list[dict]:
    result = []
    for fp_block in blocks(text, "footprint"):
        ref = qprop(fp_block, "Reference")
        if not ref:
            ref_match = re.search(r'\(fp_text\s+reference\s+"?([^"\s()]+)', fp_block)
            ref = ref_match.group(1) if ref_match else None
        if not ref:
            continue
        head = re.match(r'\(footprint\s+"([^"]*)"', fp_block)
        fp_at = first_at(fp_block)
        result.append(
            {
                "ref": ref,
                "value": qprop(fp_block, "Value"),
                "footprint": head.group(1) if head else None,
                "at": fp_at,
                "layer": atom(fp_block, "layer"),
                "pads": parse_pads(fp_block, fp_at),
            }
        )
    return result


def unique_pad_rows(fp: dict) -> list[dict]:
    seen = set()
    rows = []
    for pad in fp["pads"]:
        key = (pad["number"], pad.get("net"), pad.get("pinfunction"), tuple(pad.get("absolute_xy") or []))
        if key in seen:
            continue
        seen.add(key)
        rows.append(pad)
    return rows


def net_index(footprints: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for fp in footprints:
        for pad in unique_pad_rows(fp):
            if not pad.get("net"):
                continue
            index.setdefault(pad["net"], []).append(
                {
                    "ref": fp["ref"],
                    "value": fp["value"],
                    "footprint": fp["footprint"],
                    "pad": pad["number"],
                    "pinfunction": pad.get("pinfunction"),
                    "xy": pad.get("absolute_xy"),
                }
            )
    return index


def pinfunction_matches(pinfunction: str | None, aliases: tuple[str, ...]) -> bool:
    if not pinfunction:
        return False
    normalized = pinfunction.upper().replace(" ", "")
    return any(alias.upper().replace(" ", "") in normalized for alias in aliases)


def find_controller(footprints: list[dict]) -> dict:
    exact = [fp for fp in footprints if fp["ref"] == "U1"]
    if exact:
        return exact[0]
    candidates = [
        fp for fp in footprints
        if "promicro" in str(fp.get("value", "")).lower()
        or "promicro" in str(fp.get("footprint", "")).lower()
        or "elite" in str(fp.get("value", "")).lower()
    ]
    if len(candidates) != 1:
        raise SystemExit(f"unable to resolve controller footprint; candidates={len(candidates)}")
    return candidates[0]


def resolve_gpio_pads(controller: dict) -> dict[str, dict]:
    resolved = {}
    pads = unique_pad_rows(controller)
    for gpio, aliases in GPIO_TO_PROMICRO_ALIAS.items():
        matches = [pad for pad in pads if pinfunction_matches(pad.get("pinfunction"), aliases)]
        if len(matches) != 1:
            # KLOR's controller footprint may omit pinfunction metadata. Fall back
            # to the stock Pro Micro pad numbering represented by its schematic.
            fallback_pad_numbers = {"GP1": "2", "GP2": "5", "GP3": "6", "GP4": "7", "GP9": "12"}
            matches = [pad for pad in pads if pad["number"] == fallback_pad_numbers[gpio]]
        if len(matches) != 1:
            raise SystemExit(f"unable to resolve {gpio} on {controller['ref']}; matches={len(matches)}")
        resolved[gpio] = matches[0]
    return resolved


def parse_segments(text: str, net_ids: set[int]) -> dict[str, list[dict]]:
    result = {str(net): [] for net in sorted(net_ids)}
    for segment_block in blocks(text, "segment"):
        net = atom(segment_block, "net")
        if not net or not net.isdigit() or int(net) not in net_ids:
            continue
        result[net].append(
            {
                "start": xy(segment_block, "start"),
                "end": xy(segment_block, "end"),
                "width": float(atom(segment_block, "width")) if atom(segment_block, "width") else None,
                "layer": atom(segment_block, "layer"),
            }
        )
    return result


def parse_vias(text: str, net_ids: set[int]) -> dict[str, list[dict]]:
    result = {str(net): [] for net in sorted(net_ids)}
    for via_block in blocks(text, "via"):
        net = atom(via_block, "net")
        if not net or not net.isdigit() or int(net) not in net_ids:
            continue
        result[net].append(
            {
                "at": (first_at(via_block) or [None, None])[:2],
                "size": float(atom(via_block, "size")) if atom(via_block, "size") else None,
                "drill": float(atom(via_block, "drill")) if atom(via_block, "drill") else None,
            }
        )
    return result


def firmware_claims(config_text: str, keyboard_json_text: str) -> dict:
    keyboard = json.loads(keyboard_json_text)

    def active_define(name: str) -> list[str]:
        values = []
        for line in config_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            match = re.match(r"#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", stripped)
            if match:
                values.append((match.group(1) or "true").strip())
        return values

    def commented_define(name: str) -> list[str]:
        values = []
        for line in config_text.splitlines():
            match = re.match(r"\s*//\s*#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", line)
            if match:
                values.append((match.group(1) or "true").strip())
        return values

    return {
        "active": {
            "I2C1_SDA_PIN": active_define("I2C1_SDA_PIN"),
            "I2C1_SCL_PIN": active_define("I2C1_SCL_PIN"),
            "SERIAL_USART_TX_PIN": active_define("SERIAL_USART_TX_PIN"),
            "SERIAL_USART_RX_PIN": active_define("SERIAL_USART_RX_PIN"),
            "SERIAL_USART_FULL_DUPLEX": active_define("SERIAL_USART_FULL_DUPLEX"),
            "AUDIO_PIN": active_define("AUDIO_PIN"),
            "PAW3204_SDIO_PIN": active_define("PAW3204_SDIO_PIN"),
            "PAW3204_SCLK_PIN": active_define("PAW3204_SCLK_PIN"),
        },
        "commented": {
            "SERIAL_USART_TX_PIN": commented_define("SERIAL_USART_TX_PIN"),
            "SERIAL_USART_RX_PIN": commented_define("SERIAL_USART_RX_PIN"),
            "SERIAL_USART_FULL_DUPLEX": commented_define("SERIAL_USART_FULL_DUPLEX"),
        },
        "features": keyboard.get("features", {}),
        "development_board": keyboard.get("development_board"),
    }


def jumper_inventory(footprints: list[dict]) -> list[dict]:
    rows = []
    for fp in footprints:
        ref = str(fp["ref"])
        value = str(fp.get("value") or "")
        footprint = str(fp.get("footprint") or "")
        if ref.startswith("JP") or "jumper" in value.lower() or "jumper" in footprint.lower():
            rows.append(
                {
                    "ref": ref,
                    "value": fp.get("value"),
                    "footprint": fp.get("footprint"),
                    "at": fp.get("at"),
                    "pads": unique_pad_rows(fp),
                }
            )
    return sorted(rows, key=lambda row: row["ref"])


def peripheral_inventory(footprints: list[dict]) -> list[dict]:
    wanted_prefixes = ("J", "BZ", "OLED", "H")
    rows = []
    for fp in footprints:
        if not str(fp["ref"]).startswith(wanted_prefixes):
            continue
        rows.append(
            {
                "ref": fp["ref"],
                "value": fp.get("value"),
                "footprint": fp.get("footprint"),
                "at": fp.get("at"),
                "pads": unique_pad_rows(fp),
            }
        )
    return sorted(rows, key=lambda row: row["ref"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    pcb_text = PCB.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    keyboard_json_text = KEYBOARD_JSON.read_text(encoding="utf-8")

    footprints = parse_footprints(pcb_text)
    by_ref = {fp["ref"]: fp for fp in footprints}
    index = net_index(footprints)
    controller = find_controller(footprints)
    gpio_pads = resolve_gpio_pads(controller)

    gpio_report = {}
    target_net_ids = set()
    for gpio in TARGET_GPIOS:
        pad = gpio_pads[gpio]
        if pad.get("net_id") is not None:
            target_net_ids.add(int(pad["net_id"]))
        gpio_report[gpio] = {
            "promicro_aliases": list(GPIO_TO_PROMICRO_ALIAS[gpio]),
            "controller_ref": controller["ref"],
            "controller_pad": pad,
            "peers": [peer for peer in index.get(pad.get("net"), []) if peer["ref"] != controller["ref"]],
        }

    jumpers = jumper_inventory(footprints)
    peripherals = peripheral_inventory(footprints)

    # Explicitly retain the locally relevant references discovered in 2A even if
    # they do not match a broad prefix filter in a future source revision.
    local_refs = ["J1", "J2", "J3", "BZ1", "JP16", "JP17", "JP18", "JP19", "JP20", "JP21"]
    local_components = {
        ref: {
            "value": by_ref[ref].get("value"),
            "footprint": by_ref[ref].get("footprint"),
            "at": by_ref[ref].get("at"),
            "pads": unique_pad_rows(by_ref[ref]),
        }
        for ref in local_refs
        if ref in by_ref
    }

    segments = parse_segments(pcb_text, target_net_ids)
    vias = parse_vias(pcb_text, target_net_ids)

    claims = firmware_claims(config_text, keyboard_json_text)

    checks = {
        "development_board_is_elite_pi": claims["development_board"] == "elite_pi",
        "gp1_active_half_duplex": "GP1" in claims["active"]["SERIAL_USART_TX_PIN"],
        "gp2_active_i2c_sda": "GP2" in claims["active"]["I2C1_SDA_PIN"],
        "gp3_active_i2c_scl": "GP3" in claims["active"]["I2C1_SCL_PIN"],
        "gp4_documented_full_duplex_option": "GP4" in claims["commented"]["SERIAL_USART_TX_PIN"],
        "gp9_active_audio": "GP9" in claims["active"]["AUDIO_PIN"],
        "target_controller_nets_resolved": all(gpio_report[g]["controller_pad"].get("net") for g in TARGET_GPIOS),
        "jumpers_discovered": bool(jumpers),
        "local_followup_refs_discovered": any(ref in local_components for ref in ("J3", "JP16", "JP17", "JP18", "JP19", "JP20", "JP21", "BZ1")),
    }

    report = {
        "task": "2B",
        "sources": {
            "pcb": str(PCB.relative_to(ROOT)),
            "config_h": str(CONFIG.relative_to(ROOT)),
            "keyboard_json": str(KEYBOARD_JSON.relative_to(ROOT)),
        },
        "elite_pi_mapping_basis": {
            "interface": "RP2040 Community Edition / Pro-Micro-compatible socket",
            "mapping_used": {gpio: list(aliases) for gpio, aliases in GPIO_TO_PROMICRO_ALIAS.items()},
        },
        "controller": {
            "ref": controller["ref"],
            "value": controller.get("value"),
            "footprint": controller.get("footprint"),
            "at": controller.get("at"),
        },
        "firmware_claims": claims,
        "gpio_nets": gpio_report,
        "jumpers": jumpers,
        "peripherals": peripherals,
        "local_components": local_components,
        "target_net_copper": {
            "segments": segments,
            "vias": vias,
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
