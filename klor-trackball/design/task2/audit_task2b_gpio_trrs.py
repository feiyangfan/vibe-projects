#!/usr/bin/env python3
"""Task 2B: audit KLOR GPIO ownership and split/TRRS routing.

Read-only audit over stock KLOR 1.4 KiCad/QMK sources. The stock controller
footprint is reversible and may contain duplicate physical pad instances with
the same electrical pad number; this audit intentionally collapses those to one
electrical endpoint while retaining all physical positions.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PCB = ROOT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
CONFIG = ROOT / "klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/config.h"
KEYBOARD_JSON = ROOT / "klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json"

# Stock KLOR uses a Pro-Micro-compatible controller socket. With the configured
# Elite-Pi/RP2040 Community Edition controller these physical socket positions
# correspond to the listed RP2040 GPIOs.
GPIO_SOCKET = {
    "GP1": {"pad": "2", "alias": "RX1/D2", "planned": "split-half-duplex"},
    "GP2": {"pad": "5", "alias": "2/D1/SDA", "planned": "PMW3360-SCK"},
    "GP3": {"pad": "6", "alias": "3/D0/SCL", "planned": "PMW3360-MOSI"},
    "GP4": {"pad": "7", "alias": "4/D4", "planned": "PMW3360-MISO"},
    "GP9": {"pad": "12", "alias": "9/B5", "planned": "PMW3360-CS"},
}


def balanced_block(text: str, start: int) -> str:
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
                return text[start : i + 1]
    raise ValueError(f"unterminated S-expression at {start}")


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
    m = re.search(r'\(property\s+"' + re.escape(name) + r'"\s+"([^"]*)"', block)
    return m.group(1) if m else None


def atom(block: str, name: str) -> str | None:
    m = re.search(r"\(" + re.escape(name) + r'\s+(?:"([^"]*)"|([^\s()]+))', block)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def first_at(block: str) -> list[float] | None:
    m = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?\)", block)
    return [float(v) for v in m.groups() if v is not None] if m else None


def xy(block: str, token: str) -> list[float] | None:
    m = re.search(r"\(" + re.escape(token) + r"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)", block)
    return [float(m.group(1)), float(m.group(2))] if m else None


def parse_pads(fp_block: str) -> list[dict]:
    pads = []
    for pb in blocks(fp_block, "pad"):
        head = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pb)
        if not head:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pb)
        pinfn = re.search(r'\(pinfunction\s+"([^"]*)"\)', pb)
        pads.append({
            "number": head.group(1),
            "type": head.group(2),
            "shape": head.group(3),
            "at": first_at(pb),
            "net_id": int(net.group(1)) if net else None,
            "net": net.group(2) if net else None,
            "pinfunction": pinfn.group(1) if pinfn else None,
        })
    return pads


def parse_footprints(text: str) -> list[dict]:
    out = []
    for fb in blocks(text, "footprint"):
        ref = qprop(fb, "Reference")
        if not ref:
            fm = re.search(r'\(fp_text\s+reference\s+"?([^"\s()]+)', fb)
            ref = fm.group(1) if fm else None
        if not ref:
            continue
        head = re.match(r'\(footprint\s+"([^"]*)"', fb)
        out.append({
            "ref": ref,
            "value": qprop(fb, "Value"),
            "footprint": head.group(1) if head else None,
            "at": first_at(fb),
            "layer": atom(fb, "layer"),
            "pads": parse_pads(fb),
        })
    return out


def electrical_pads(fp: dict) -> list[dict]:
    """Collapse reversible duplicate pad instances into electrical pads."""
    groups: dict[tuple, dict] = {}
    for pad in fp["pads"]:
        key = (pad["number"], pad.get("net_id"), pad.get("net"), pad.get("pinfunction"))
        if key not in groups:
            groups[key] = {
                "number": pad["number"],
                "net_id": pad.get("net_id"),
                "net": pad.get("net"),
                "pinfunction": pad.get("pinfunction"),
                "physical_instances": [],
            }
        if pad.get("at") not in groups[key]["physical_instances"]:
            groups[key]["physical_instances"].append(pad.get("at"))
    return list(groups.values())


def net_index(footprints: list[dict]) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for fp in footprints:
        for pad in electrical_pads(fp):
            if not pad.get("net"):
                continue
            idx.setdefault(pad["net"], []).append({
                "ref": fp["ref"],
                "value": fp.get("value"),
                "footprint": fp.get("footprint"),
                "pad": pad["number"],
                "pinfunction": pad.get("pinfunction"),
                "physical_instances": pad["physical_instances"],
            })
    return idx


def resolve_controller_pad(controller: dict, pad_number: str) -> dict:
    matches = [p for p in electrical_pads(controller) if p["number"] == pad_number]
    if len(matches) != 1:
        raise SystemExit(f"controller pad {pad_number} has {len(matches)} electrical matches")
    return matches[0]


def parse_copper(text: str, net_ids: set[int]) -> dict:
    segments = {str(n): [] for n in sorted(net_ids)}
    vias = {str(n): [] for n in sorted(net_ids)}
    for sb in blocks(text, "segment"):
        net = atom(sb, "net")
        if net and net.isdigit() and int(net) in net_ids:
            segments[net].append({
                "start": xy(sb, "start"), "end": xy(sb, "end"),
                "width": float(atom(sb, "width")) if atom(sb, "width") else None,
                "layer": atom(sb, "layer"),
            })
    for vb in blocks(text, "via"):
        net = atom(vb, "net")
        if net and net.isdigit() and int(net) in net_ids:
            vias[net].append({
                "at": (first_at(vb) or [None, None])[:2],
                "size": float(atom(vb, "size")) if atom(vb, "size") else None,
                "drill": float(atom(vb, "drill")) if atom(vb, "drill") else None,
            })
    return {"segments": segments, "vias": vias}


def active_defines(text: str, name: str) -> list[str]:
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        m = re.match(r"#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", stripped)
        if m:
            out.append((m.group(1) or "true").strip())
    return out


def commented_defines(text: str, name: str) -> list[str]:
    out = []
    for line in text.splitlines():
        m = re.match(r"\s*//\s*#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", line)
        if m:
            out.append((m.group(1) or "true").strip())
    return out


def firmware_claims(config_text: str, keyboard_text: str) -> dict:
    keyboard = json.loads(keyboard_text)
    names = [
        "I2C1_SDA_PIN", "I2C1_SCL_PIN", "SERIAL_USART_TX_PIN",
        "SERIAL_USART_RX_PIN", "SERIAL_USART_FULL_DUPLEX", "AUDIO_PIN",
        "PAW3204_SDIO_PIN", "PAW3204_SCLK_PIN",
    ]
    return {
        "development_board": keyboard.get("development_board"),
        "features": keyboard.get("features", {}),
        "active": {name: active_defines(config_text, name) for name in names},
        "commented": {name: commented_defines(config_text, name) for name in names},
    }


def component_row(fp: dict) -> dict:
    return {
        "ref": fp["ref"], "value": fp.get("value"),
        "footprint": fp.get("footprint"), "at": fp.get("at"),
        "pads": electrical_pads(fp),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    pcb_text = PCB.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    keyboard_text = KEYBOARD_JSON.read_text(encoding="utf-8")
    footprints = parse_footprints(pcb_text)
    by_ref = {fp["ref"]: fp for fp in footprints}
    if "U1" not in by_ref:
        raise SystemExit("stock controller U1 not found")
    controller = by_ref["U1"]
    idx = net_index(footprints)

    gpio_nets = {}
    target_net_ids = set()
    for gpio, spec in GPIO_SOCKET.items():
        pad = resolve_controller_pad(controller, spec["pad"])
        if pad.get("net_id") is not None:
            target_net_ids.add(int(pad["net_id"]))
        gpio_nets[gpio] = {
            **spec,
            "controller_pad": pad,
            "peers": [p for p in idx.get(pad.get("net"), []) if p["ref"] != "U1"],
        }

    jumpers = [component_row(fp) for fp in footprints if str(fp["ref"]).startswith("JP")]
    peripherals = [
        component_row(fp) for fp in footprints
        if str(fp["ref"]).startswith(("J", "BZ")) and not str(fp["ref"]).startswith("JP")
    ]
    local_refs = ["J1", "J2", "J3", "BZ1", "JP16", "JP17", "JP18", "JP19", "JP20", "JP21"]
    local_components = {ref: component_row(by_ref[ref]) for ref in local_refs if ref in by_ref}
    claims = firmware_claims(config_text, keyboard_text)

    checks = {
        "elite_pi_selected": claims["development_board"] == "elite_pi",
        "gp1_active_half_duplex": "GP1" in claims["active"]["SERIAL_USART_TX_PIN"],
        "gp2_i2c_sda": "GP2" in claims["active"]["I2C1_SDA_PIN"],
        "gp3_i2c_scl": "GP3" in claims["active"]["I2C1_SCL_PIN"],
        "gp4_is_documented_full_duplex_tx_option": "GP4" in claims["commented"]["SERIAL_USART_TX_PIN"],
        "gp9_audio": "GP9" in claims["active"]["AUDIO_PIN"],
        "all_target_nets_resolved": all(gpio_nets[g]["controller_pad"].get("net") for g in GPIO_SOCKET),
        "local_jumpers_found": all(ref in local_components for ref in ("JP16", "JP17", "JP18", "JP19", "JP20", "JP21")),
        "j3_found": "J3" in local_components,
        "bz1_found": "BZ1" in local_components,
    }

    report = {
        "task": "2B",
        "sources": {
            "pcb": str(PCB.relative_to(ROOT)),
            "config_h": str(CONFIG.relative_to(ROOT)),
            "keyboard_json": str(KEYBOARD_JSON.relative_to(ROOT)),
        },
        "mapping_basis": {
            "controller": "Elite-Pi / RP2040 Community Edition",
            "socket": "Pro-Micro-compatible",
            "gpio_socket_map": GPIO_SOCKET,
        },
        "controller": component_row(controller),
        "firmware_claims": claims,
        "gpio_nets": gpio_nets,
        "local_components": local_components,
        "all_jumpers": sorted(jumpers, key=lambda x: x["ref"]),
        "all_connectors_and_buzzer": sorted(peripherals, key=lambda x: x["ref"]),
        "target_net_copper": parse_copper(pcb_text, target_net_ids),
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
