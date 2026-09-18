#!/usr/bin/env python3
"""Task 3B audit: verify the derivative schematic implements Task 2F.

Task 3B is schematic-only. The derivative PCB must remain byte-identical to
stock until Task 3C synchronizes/removes/reroutes the physical board.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
STOCK = ROOT / "klor1.4/PCB/klor1_4"
DERIV = ROOT / "PCB/konrad_trackball"
TASK2F = ROOT / "design/task2/TASK2F_RESULT.md"

STOCK_SCH_OBJECT = "4f68892c9d13ffe4200587708eeb4c43ee2b652b"
STOCK_PCB_OBJECT = "d16dc2e1e8730500f7844146e7c437db3b8d7b44"

REMOVED_WIRE_UUIDS = {
    # removed-key matrix branches
    "d5c00d5c-5baa-455a-917e-331f422518b1",
    "9a6c13cf-0ccb-4f42-89f4-3c341340e792",
    # old SW13 -> SW22 and SW22 -> SW14 data path
    "957d453f-df09-4026-a853-0bdd375aba6e",
    "3851de7d-4376-48fd-b483-b2c81f21328f",
    "ee10175d-3408-4b35-8ba5-a1cb04f0a687",
    "ce11c102-f9cc-4ee3-a186-b357c116d05d",
    "cc4e0961-c84b-4d27-aa7a-a01ed564ac49",
    # deleted SW22 power stubs
    "c3024910-c6ab-41f3-a94a-10bcb2de5eae",
    "119adc0b-3c4a-4ad4-b938-ed6dae9e95cc",
    # J1.3 RX branch
    "430a1979-61a9-409d-8619-8f4ea15220d2",
}

U1_LABELS = {
    ("32.004", "36.576"): "PMW_SCK",
    ("32.004", "39.116"): "PMW_MOSI",
    ("32.004", "41.656"): "PMW_MISO",
    ("32.004", "54.356"): "PMW_CS",
}

J4_LABELS = {
    ("90.17", "64.77"): "PMW_CS",
    ("90.17", "67.31"): "PMW_MISO",
    ("90.17", "69.85"): "PMW_MOSI",
    ("90.17", "72.39"): "PMW_SCK",
    ("90.17", "77.47"): "VCC",
    ("90.17", "80.01"): "GND",
}


def git_object(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    p = subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if p.returncode:
        raise RuntimeError(f"git rev-parse failed for {rel}: {p.stderr.strip()}")
    return p.stdout.strip()


def balanced_block(text: str, start: int) -> tuple[str, int]:
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
                return text[start : i + 1], i + 1
    raise ValueError("unbalanced s-expression")


def blocks(text: str, token: str, start_offset: int = 0) -> list[str]:
    out: list[str] = []
    pos = 0
    while True:
        pos = text.find(token, pos)
        if pos < 0:
            break
        start = pos + start_offset
        block, end = balanced_block(text, start)
        out.append(block)
        pos = end
    return out


def top_symbol_blocks(text: str) -> list[str]:
    return [
        block
        for block in blocks(text, "\n\t(symbol\n", 2)
        if "(lib_id " in block
    ]


def ref_block(text: str, ref: str) -> list[str]:
    needle = f'(property "Reference" "{ref}"'
    return [b for b in top_symbol_blocks(text) if needle in b]


def global_label_records(text: str) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    for block in blocks(text, "\n\t(global_label ", 2):
        m = re.match(
            r'^\(global_label "([^"]+)"[\s\S]*?\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)',
            block,
        )
        if m:
            recs.append(
                {
                    "name": m.group(1),
                    "x": m.group(2),
                    "y": m.group(3),
                    "rotation": m.group(4),
                    "block": block,
                }
            )
    return recs


def wire_records(text: str) -> list[dict[str, object]]:
    out = []
    for block in blocks(text, "\n\t(wire\n", 2):
        pts = re.findall(r"\(xy ([\d.-]+) ([\d.-]+)\)", block)
        uid = re.search(r'\(uuid "([^"]+)"\)', block)
        out.append({"pts": pts, "uuid": uid.group(1) if uid else None, "block": block})
    return out


def parens_balanced(text: str) -> bool:
    depth = 0
    quoted = False
    escaped = False
    for ch in text:
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
            if depth < 0:
                return False
    return depth == 0 and not quoted


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    sch_path = DERIV / "konrad_trackball.kicad_sch"
    pcb_path = DERIV / "konrad_trackball.kicad_pcb"
    stock_sch = STOCK / "klor1_4.kicad_sch"
    stock_pcb = STOCK / "klor1_4.kicad_pcb"

    sch = sch_path.read_text(encoding="utf-8")
    stock_sch_text = stock_sch.read_text(encoding="utf-8")
    task2f = TASK2F.read_text(encoding="utf-8")

    symbols = top_symbol_blocks(sch)
    labels = global_label_records(sch)
    wires = wire_records(sch)
    wire_uuids = {w["uuid"] for w in wires}

    label_at = {(r["x"], r["y"]): r["name"] for r in labels}
    label_counts: dict[str, int] = {}
    for r in labels:
        label_counts[r["name"]] = label_counts.get(r["name"], 0) + 1

    checks: dict[str, bool] = {
        "schematic_parentheses_balanced": parens_balanced(sch),
        "stock_schematic_object_locked": git_object(stock_sch) == STOCK_SCH_OBJECT,
        "stock_pcb_object_locked": git_object(stock_pcb) == STOCK_PCB_OBJECT,
        "derivative_schematic_changed_from_stock": sch != stock_sch_text,
        "derivative_pcb_still_exact_stock": pcb_path.read_bytes() == stock_pcb.read_bytes(),
        "sw22_removed_from_schematic": len(ref_block(sch, "SW22")) == 0,
        "d22_removed_from_schematic": len(ref_block(sch, "D22")) == 0,
        "col1_label_preserved": label_counts.get("col1", 0) >= 1,
        "row3_label_preserved": label_counts.get("row3", 0) >= 1,
        "u1_pmw_labels_exact": all(label_at.get(xy) == name for xy, name in U1_LABELS.items()),
        "pmw_signal_labels_pairwise": all(label_counts.get(name, 0) == 2 for name in ("PMW_CS", "PMW_MISO", "PMW_MOSI", "PMW_SCK")),
        "legacy_rx_global_label_retired": label_counts.get("RX", 0) == 0,
        "j1_pin3_no_connect": "(no_connect\n\t\t(at 123.19 44.704)" in sch,
        "j1_pin4_tx_wire_preserved": "(xy 123.19 35.814) (xy 129.286 35.814)" in sch,
        "j1_pin4_tx_label_preserved": label_at.get(("129.286", "35.814")) == "TX",
        "rgb_bypass_exact": "(xy 214.63 136.398) (xy 227.584 136.398)" in sch,
        "all_obsolete_branch_uuids_removed": not (REMOVED_WIRE_UUIDS & wire_uuids),
        "j4_exactly_one_symbol": len(ref_block(sch, "J4")) == 1,
        "j4_uses_1x07_symbol": len(ref_block(sch, "J4")) == 1 and '(lib_id "Connector_Generic:Conn_01x07")' in ref_block(sch, "J4")[0],
        "j4_footprint_exact": len(ref_block(sch, "J4")) == 1 and 'Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical' in ref_block(sch, "J4")[0],
        "j4_value_identifies_kivipallur": len(ref_block(sch, "J4")) == 1 and '(property "Value" "PMW3360 Kivipallur"' in ref_block(sch, "J4")[0],
        "j4_signal_labels_exact": all(label_at.get(xy) == name for xy, name in J4_LABELS.items()),
        "j4_motion_pin5_no_connect": "(no_connect\n\t\t(at 90.17 74.93)" in sch,
        "j2_haptic_marked_dnp": len(ref_block(sch, "J2")) == 1 and "(dnp yes)" in ref_block(sch, "J2")[0],
        "oled1_marked_dnp": len(ref_block(sch, "OLED1")) == 1 and "(dnp yes)" in ref_block(sch, "OLED1")[0],
        "bz1_marked_dnp": len(ref_block(sch, "BZ1")) == 1 and "(dnp yes)" in ref_block(sch, "BZ1")[0],
        "legacy_sda_not_on_u1": label_at.get(("32.004", "36.576")) != "SDA",
        "legacy_scl_not_on_u1": label_at.get(("32.004", "39.116")) != "SCL",
        "legacy_audio_not_on_u1": label_at.get(("32.004", "54.356")) != "AUDIO",
        "task2f_contract_source_present": all(
            token in task2f
            for token in ("PMW_CS", "PMW_MISO", "PMW_MOSI", "PMW_SCK", "MOTION", "VCC", "GND")
        ),
        "pcb_j4_not_yet_present_before_3c": 'Reference" "J4"' not in pcb_path.read_text(encoding="utf-8", errors="ignore"),
    }

    result = {
        "task": "3B",
        "status": "complete" if all(checks.values()) else "failed",
        "scope": "derivative schematic only",
        "connector": {
            "reference": "J4",
            "symbol": "Connector_Generic:Conn_01x07",
            "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
            "pin_contract": {
                "1": "PMW_CS",
                "2": "PMW_MISO",
                "3": "PMW_MOSI",
                "4": "PMW_SCK",
                "5": "NC/MOTION",
                "6": "VCC",
                "7": "GND",
            },
        },
        "u1_reassignments": {
            "GP2": "PMW_SCK",
            "GP3": "PMW_MOSI",
            "GP4": "PMW_MISO",
            "GP9": "PMW_CS",
        },
        "dnp_revision1": ["J2", "OLED1", "BZ1"],
        "rgb_bypass": "SW13 DOUT -> SW14 DIN",
        "trrs": {"J1.3": "NC", "J1.4": "TX/GP1 preserved"},
        "pcb_synchronization": "deferred to Task 3C",
        "checks": checks,
    }

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
