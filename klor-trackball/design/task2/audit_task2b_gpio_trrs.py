#!/usr/bin/env python3
"""Task 2B: audit KLOR GPIO ownership and split/TRRS routing.

Read-only regression audit over the stock KLOR 1.4 PCB and QMK configuration.
It locks the source topology required before GP2/GP3/GP4/GP9 can be reassigned
to the PMW3360 on the right-hand derivative.
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

# Pro-Micro-compatible U1 socket positions used by the configured Elite-Pi.
GPIO_SOCKET = {
    "GP1": {"pad": "2", "stock_net": "TX", "planned": "split-half-duplex"},
    "GP2": {"pad": "5", "stock_net": "SDA", "planned": "PMW3360-SCK"},
    "GP3": {"pad": "6", "stock_net": "SCL", "planned": "PMW3360-MOSI"},
    "GP4": {"pad": "7", "stock_net": "RX", "planned": "PMW3360-MISO"},
    "GP9": {"pad": "12", "stock_net": "AUDIO", "planned": "PMW3360-CS"},
}

# Exact stock branch adjacent to J1.3. Removing this branch on the derivative
# leaves the full-duplex RX contact electrically isolated while preserving J1.4
# for the active GP1 half-duplex split link.
GP4_J1_ISOLATION_SEGMENT = {
    "start": [92.7, 127.025],
    "end": [90.88, 127.025],
    "layer": "F.Cu",
    "width": 0.254,
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
                return text[start:i + 1]
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


def component(fp: dict) -> dict:
    return {
        "ref": fp["ref"],
        "value": fp.get("value"),
        "footprint": fp.get("footprint"),
        "at": fp.get("at"),
        "pads": electrical_pads(fp),
    }


def net_index(footprints: list[dict]) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for fp in footprints:
        for pad in electrical_pads(fp):
            if pad.get("net"):
                idx.setdefault(pad["net"], []).append({
                    "ref": fp["ref"],
                    "pad": pad["number"],
                    "value": fp.get("value"),
                    "footprint": fp.get("footprint"),
                })
    return idx


def defines(text: str, name: str, commented: bool = False) -> list[str]:
    out = []
    for line in text.splitlines():
        if commented:
            m = re.match(r"\s*//\s*#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", line)
        else:
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            m = re.match(r"#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", stripped)
        if m:
            out.append((m.group(1) or "true").strip())
    return out


def first_token(values: list[str]) -> list[str]:
    return [value.split()[0] for value in values if value.split()]


def firmware_claims(config_text: str, keyboard_text: str) -> dict:
    names = [
        "I2C1_SDA_PIN", "I2C1_SCL_PIN", "SERIAL_USART_TX_PIN",
        "SERIAL_USART_RX_PIN", "SERIAL_USART_FULL_DUPLEX", "AUDIO_PIN",
        "PAW3204_SDIO_PIN", "PAW3204_SCLK_PIN",
    ]
    keyboard = json.loads(keyboard_text)
    return {
        "development_board": keyboard.get("development_board"),
        "features": keyboard.get("features", {}),
        "active": {name: defines(config_text, name) for name in names},
        "commented": {name: defines(config_text, name, True) for name in names},
    }


def parse_segments(text: str, net_id: int) -> list[dict]:
    out = []
    for sb in blocks(text, "segment"):
        net = atom(sb, "net")
        if net and net.isdigit() and int(net) == net_id:
            out.append({
                "start": point(sb, "start"),
                "end": point(sb, "end"),
                "layer": atom(sb, "layer"),
                "width": float(atom(sb, "width")) if atom(sb, "width") else None,
            })
    return out


def same_point(a: list[float] | None, b: list[float]) -> bool:
    return bool(a) and len(a) >= 2 and math.isclose(a[0], b[0], abs_tol=1e-6) and math.isclose(a[1], b[1], abs_tol=1e-6)


def segment_matches(segment: dict, expected: dict) -> bool:
    endpoints_match = (
        same_point(segment.get("start"), expected["start"]) and same_point(segment.get("end"), expected["end"])
    ) or (
        same_point(segment.get("start"), expected["end"]) and same_point(segment.get("end"), expected["start"])
    )
    return (
        endpoints_match
        and segment.get("layer") == expected["layer"]
        and math.isclose(segment.get("width") or -1, expected["width"], abs_tol=1e-9)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    pcb_text = PCB.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    keyboard_text = KEYBOARD_JSON.read_text(encoding="utf-8")
    footprints = parse_footprints(pcb_text)
    by_ref = {fp["ref"]: fp for fp in footprints}
    controller = by_ref["U1"]
    idx = net_index(footprints)
    claims = firmware_claims(config_text, keyboard_text)

    gpio = {}
    for name, spec in GPIO_SOCKET.items():
        matches = [
            p for p in electrical_pads(controller)
            if p["number"] == spec["pad"] and p.get("net") == spec["stock_net"]
        ]
        if len(matches) != 1:
            raise SystemExit(f"{name}: expected one U1 pad {spec['pad']} on {spec['stock_net']}, got {len(matches)}")
        pad = matches[0]
        gpio[name] = {
            **spec,
            "net_id": pad["net_id"],
            "physical_instances": pad["physical_instances"],
            "peers": [p for p in idx.get(spec["stock_net"], []) if p["ref"] != "U1"],
        }

    gp4_segments = parse_segments(pcb_text, gpio["GP4"]["net_id"])
    exact_isolation_present = any(segment_matches(seg, GP4_J1_ISOLATION_SEGMENT) for seg in gp4_segments)

    jumper_refs = {
        ref: component(fp) for ref, fp in by_ref.items()
        if ref.startswith("JP")
    }
    i2c_jumpers = {
        ref: row for ref, row in jumper_refs.items()
        if any(p.get("net") in {"SDA", "SCL"} for p in row["pads"])
    }
    all_i2c_jumpers_default_open = all(
        "Open" in str(row.get("footprint") or "") for row in i2c_jumpers.values()
    )

    local_refs = ["J1", "J2", "J3", "BZ1", "JP3", "JP4", "JP5", "JP6", "JP16", "JP17", "JP20", "JP21", "JP27", "JP28"]
    local = {ref: component(by_ref[ref]) for ref in local_refs if ref in by_ref}

    expected_peers = {
        "GP1": {("J1", "4")},
        "GP4": {("J1", "3")},
        "GP9": {("BZ1", "1")},
    }
    peer_pairs = {
        name: {(p["ref"], p["pad"]) for p in gpio[name]["peers"]}
        for name in expected_peers
    }

    checks = {
        "elite_pi_selected": claims["development_board"] == "elite_pi",
        "gp1_active_half_duplex": "GP1" in first_token(claims["active"]["SERIAL_USART_TX_PIN"]),
        "gp2_active_i2c_and_paw3204": (
            "GP2" in first_token(claims["active"]["I2C1_SDA_PIN"])
            and "GP2" in first_token(claims["active"]["PAW3204_SDIO_PIN"])
        ),
        "gp3_active_i2c_and_paw3204": (
            "GP3" in first_token(claims["active"]["I2C1_SCL_PIN"])
            and "GP3" in first_token(claims["active"]["PAW3204_SCLK_PIN"])
        ),
        "gp4_documented_full_duplex_tx_option": "GP4" in first_token(claims["commented"]["SERIAL_USART_TX_PIN"]),
        "gp1_documented_full_duplex_rx_option": "GP1" in first_token(claims["commented"]["SERIAL_USART_RX_PIN"]),
        "gp9_active_audio": "GP9" in first_token(claims["active"]["AUDIO_PIN"]),
        "gp1_only_trrs_j1_pad4": peer_pairs["GP1"] == expected_peers["GP1"],
        "gp4_only_trrs_j1_pad3": peer_pairs["GP4"] == expected_peers["GP4"],
        "gp9_only_buzzer_bz1_pad1": peer_pairs["GP9"] == expected_peers["GP9"],
        "gp4_exact_j1_isolation_segment_present": exact_isolation_present,
        "i2c_jumpers_discovered": bool(i2c_jumpers),
        "i2c_jumpers_default_open": all_i2c_jumpers_default_open,
        "j2_haptic_scl_connection_present": any(p["ref"] == "J2" and p["pad"] == "3" for p in gpio["GP3"]["peers"]),
    }

    report = {
        "task": "2B",
        "sources": {
            "pcb": str(PCB.relative_to(ROOT)),
            "config_h": str(CONFIG.relative_to(ROOT)),
            "keyboard_json": str(KEYBOARD_JSON.relative_to(ROOT)),
        },
        "firmware_claims": claims,
        "gpio_topology": gpio,
        "i2c_jumpers": i2c_jumpers,
        "local_components": local,
        "gp4_trrs_isolation": {
            "stock_net": "RX",
            "trrs_contact": "J1.3",
            "required_trackball_disposition": "J1.3 NC; remove the J1.3-to-RX branch while preserving J1.4/TX for GP1 half-duplex split",
            "exact_stock_segment_to_remove": GP4_J1_ISOLATION_SEGMENT,
            "segment_verified_in_source": exact_isolation_present,
        },
        "locked_dispositions": {
            "GP1": "preserve TX net to J1.4 for half-duplex split serial",
            "GP2": "reassign SDA to PMW3360 SCK; disable I2C/PAW3204; keep legacy I2C jumpers open",
            "GP3": "reassign SCL to PMW3360 MOSI; disable I2C/PAW3204; do not populate J2 haptic module; keep legacy I2C jumpers open",
            "GP4": "reassign RX to PMW3360 MISO; isolate J1.3 by removing the verified adjacent F.Cu branch",
            "GP9": "reassign AUDIO to PMW3360 CS; disable audio and do not populate BZ1; obsolete AUDIO copper may be removed in Task 3",
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
