#!/usr/bin/env python3
"""Task 2B: audit GPIO ownership and reversible split/TRRS routing.

This is intentionally read-only. KLOR 1.4 is a reversible PCB: a single
Pro-Micro socket pad number can have different connected nets at mirrored
physical pad instances. The audit therefore records *all* connected alternatives
instead of pretending one pad number maps to one PCB net.
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

GPIO_SOCKET = {
    "GP1": {"pad": "2", "alias": "RX1/D2", "planned": "split-half-duplex"},
    "GP2": {"pad": "5", "alias": "2/D1/SDA", "planned": "PMW3360-SCK"},
    "GP3": {"pad": "6", "alias": "3/D0/SCL", "planned": "PMW3360-MOSI"},
    "GP4": {"pad": "7", "alias": "4/D4", "planned": "PMW3360-MISO"},
    "GP9": {"pad": "12", "alias": "9/B5", "planned": "PMW3360-CS"},
}


def balanced(text: str, start: int) -> str:
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
                return text[start:i + 1]
    raise ValueError(f"unterminated S-expression at {start}")


def blocks(text: str, token: str) -> Iterable[str]:
    pat = re.compile(r"\(" + re.escape(token) + r"(?=\s|\()")
    pos = 0
    while True:
        match = pat.search(text, pos)
        if not match:
            return
        block = balanced(text, match.start())
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


def point(block: str, token: str) -> list[float] | None:
    m = re.search(r"\(" + re.escape(token) + r"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)", block)
    return [float(m.group(1)), float(m.group(2))] if m else None


def parse_pads(fp_block: str) -> list[dict]:
    out = []
    for pb in blocks(fp_block, "pad"):
        h = re.match(r'\(pad\s+"([^"]*)"\s+([^\s()]+)\s+([^\s()]+)', pb)
        if not h:
            continue
        net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pb)
        out.append({
            "number": h.group(1),
            "type": h.group(2),
            "shape": h.group(3),
            "at": first_at(pb),
            "net_id": int(net.group(1)) if net else None,
            "net": net.group(2) if net else None,
        })
    return out


def parse_footprints(text: str) -> list[dict]:
    out = []
    for fb in blocks(text, "footprint"):
        ref = qprop(fb, "Reference")
        if not ref:
            m = re.search(r'\(fp_text\s+reference\s+"?([^"\s()]+)', fb)
            ref = m.group(1) if m else None
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
    groups: dict[tuple, dict] = {}
    for pad in fp["pads"]:
        key = (pad["number"], pad.get("net_id"), pad.get("net"))
        row = groups.setdefault(key, {
            "number": pad["number"],
            "net_id": pad.get("net_id"),
            "net": pad.get("net"),
            "physical_instances": [],
        })
        if pad.get("at") not in row["physical_instances"]:
            row["physical_instances"].append(pad.get("at"))
    return list(groups.values())


def net_index(footprints: list[dict]) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for fp in footprints:
        for pad in electrical_pads(fp):
            if not pad.get("net"):
                continue
            idx.setdefault(pad["net"], []).append({
                "ref": fp["ref"], "value": fp.get("value"),
                "footprint": fp.get("footprint"), "pad": pad["number"],
                "physical_instances": pad["physical_instances"],
            })
    return idx


def component(fp: dict) -> dict:
    return {
        "ref": fp["ref"], "value": fp.get("value"),
        "footprint": fp.get("footprint"), "at": fp.get("at"),
        "pads": electrical_pads(fp),
    }


def active_defines(text: str, name: str) -> list[str]:
    result = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        m = re.match(r"#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", stripped)
        if m:
            result.append((m.group(1) or "true").strip())
    return result


def commented_defines(text: str, name: str) -> list[str]:
    result = []
    for line in text.splitlines():
        m = re.match(r"\s*//\s*#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", line)
        if m:
            result.append((m.group(1) or "true").strip())
    return result


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


def copper(text: str, net_ids: set[int]) -> dict:
    segments = {str(i): [] for i in sorted(net_ids)}
    vias = {str(i): [] for i in sorted(net_ids)}
    for sb in blocks(text, "segment"):
        net = atom(sb, "net")
        if net and net.isdigit() and int(net) in net_ids:
            segments[net].append({
                "start": point(sb, "start"), "end": point(sb, "end"),
                "width": float(atom(sb, "width")) if atom(sb, "width") else None,
                "layer": atom(sb, "layer"),
            })
    for vb in blocks(text, "via"):
        net = atom(vb, "net")
        if net and net.isdigit() and int(net) in net_ids:
            vias[net].append({"at": (first_at(vb) or [])[:2]})
    return {"segments": segments, "vias": vias}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    pcb_text = PCB.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    keyboard_text = KEYBOARD_JSON.read_text(encoding="utf-8")
    fps = parse_footprints(pcb_text)
    by_ref = {fp["ref"]: fp for fp in fps}
    controller = by_ref.get("U1")
    if not controller:
        raise SystemExit("U1 not found")
    idx = net_index(fps)

    gpio = {}
    target_net_ids: set[int] = set()
    for name, spec in GPIO_SOCKET.items():
        alternatives = [p for p in electrical_pads(controller) if p["number"] == spec["pad"] and p.get("net")]
        for alt in alternatives:
            if alt.get("net_id") is not None:
                target_net_ids.add(int(alt["net_id"]))
            alt["peers"] = [peer for peer in idx.get(alt["net"], []) if peer["ref"] != "U1"]
        gpio[name] = {**spec, "controller_pad_alternatives": alternatives}

    local_refs = ["J1", "J2", "J3", "BZ1", "JP16", "JP17", "JP18", "JP19", "JP20", "JP21"]
    local = {ref: component(by_ref[ref]) for ref in local_refs if ref in by_ref}
    jumpers = sorted([component(fp) for fp in fps if fp["ref"].startswith("JP")], key=lambda x: x["ref"])
    claims = firmware_claims(config_text, keyboard_text)

    checks = {
        "elite_pi_selected": claims["development_board"] == "elite_pi",
        "gp1_active_half_duplex": "GP1" in claims["active"]["SERIAL_USART_TX_PIN"],
        "gp2_i2c_sda": "GP2" in claims["active"]["I2C1_SDA_PIN"],
        "gp3_i2c_scl": "GP3" in claims["active"]["I2C1_SCL_PIN"],
        "gp4_full_duplex_option_documented": "GP4" in claims["commented"]["SERIAL_USART_TX_PIN"],
        "gp9_audio": "GP9" in claims["active"]["AUDIO_PIN"],
        "all_target_socket_positions_have_connected_alternatives": all(gpio[g]["controller_pad_alternatives"] for g in GPIO_SOCKET),
        "local_jumpers_present": all(ref in local for ref in ("JP16", "JP17", "JP18", "JP19", "JP20", "JP21")),
        "j3_present": "J3" in local,
        "bz1_present": "BZ1" in local,
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
            "socket": "Pro-Micro-compatible reversible KLOR U1 footprint",
            "gpio_socket_map": GPIO_SOCKET,
            "warning": "A U1 pad number can have more than one connected net on this reversible PCB; use physical/jumper topology to resolve the right-half path.",
        },
        "firmware_claims": claims,
        "controller": component(controller),
        "gpio_socket_alternatives": gpio,
        "local_components": local,
        "all_jumpers": jumpers,
        "target_net_copper": copper(pcb_text, target_net_ids),
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
