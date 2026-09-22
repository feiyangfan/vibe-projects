#!/usr/bin/env python3
"""Deterministically apply Task 3D geometry to the Task 3C PCB baseline."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
PCB = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_pcb"

BASELINE_BLOB = "c3fefdb583d653a836d2ab99a9d94126ea331a3b"
RESULT_BLOB = "4272f9c3895fd46c0688b3eb530fc7299b540727"

J4_UUID = "3c3c0004-0000-4000-8000-000000000001"
OLD_EDGE_UUID = "6a8d966a-c3bb-40c7-938f-b720f86fa562"
CURVE_UUID = "b693c5db-8f44-4066-8000-0f32a9cfada9"

EDGE_UUIDS = [
    "3d3d0001-0000-4000-8000-000000000001",
    "3d3d0001-0000-4000-8000-000000000002",
    "3d3d0001-0000-4000-8000-000000000003",
    "3d3d0001-0000-4000-8000-000000000004",
    "3d3d0001-0000-4000-8000-000000000005",
    "3d3d0001-0000-4000-8000-000000000006",
]


def git_blob(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=REPO, check=True, text=True, capture_output=True,
    ).stdout.strip()


def balanced(text: str, start: int) -> tuple[str, int]:
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
                return text[start:i + 1], i + 1
    raise ValueError("unbalanced KiCad expression")


def blocks(text: str, token: str) -> list[str]:
    result = []
    pos = 0
    needle = "(" + token
    while True:
        pos = text.find(needle, pos)
        if pos < 0:
            return result
        block, end = balanced(text, pos)
        result.append(block)
        pos = end


def by_uuid(text: str, token: str, uid: str) -> str:
    found = [b for b in blocks(text, token) if f'(uuid "{uid}")' in b]
    if len(found) != 1:
        raise ValueError(f"{token} {uid}: expected 1 block, found {len(found)}")
    return found[0]


def replace_uuid(text: str, token: str, uid: str, replacement: str) -> str:
    old = by_uuid(text, token, uid)
    return text.replace(old, replacement, 1)


def remove_uuid(text: str, token: str, uid: str) -> str:
    return replace_uuid(text, token, uid, "")


def segment(a, b, width, layer, net, uid) -> str:
    return (
        f'(segment\n\t\t(start {a[0]} {a[1]})\n'
        f'\t\t(end {b[0]} {b[1]})\n'
        f'\t\t(width {width})\n\t\t(layer "{layer}")\n'
        f'\t\t(net {net})\n\t\t(uuid "{uid}")\n\t)'
    )


def gr_line(a, b, uid) -> str:
    return (
        f'(gr_line\n\t\t(start {a[0]} {a[1]})\n'
        f'\t\t(end {b[0]} {b[1]})\n\t\t(stroke\n'
        f'\t\t\t(width 0.01)\n\t\t\t(type solid)\n\t\t)\n'
        f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uid}")\n\t)'
    )


def main() -> int:
    if git_blob(PCB) != BASELINE_BLOB:
        raise SystemExit("Task 3D apply script requires the exact Task 3C PCB baseline")

    text = PCB.read_text(encoding="utf-8")

    j4 = by_uuid(text, "footprint", J4_UUID)
    if "(at 60 70)" not in j4:
        raise ValueError("J4 staging coordinate changed")
    text = replace_uuid(
        text, "footprint", J4_UUID,
        j4.replace("(at 60 70)", "(at 147.724665 142.367997)", 1),
    )

    curve = by_uuid(text, "gr_curve", CURVE_UUID)
    curve = re.sub(
        r"\(pts[\s\S]*?\)\n\t\t\(stroke",
        "(pts\n\t\t\t(xy 124.598127 141.714517) "
        "(xy 130.470110 140.137470) "
        "(xy 136.469818 139.294864) "
        "(xy 142.111043 139.186691)\n\t\t)\n\t\t(stroke",
        curve,
        count=1,
    )
    text = replace_uuid(text, "gr_curve", CURVE_UUID, curve)

    edges = [
        gr_line(("142.111043", "139.186691"), ("142.111043", "123.747997"), EDGE_UUIDS[0]),
        gr_line(("142.111043", "123.747997"), ("144.111043", "123.747997"), EDGE_UUIDS[1]),
        gr_line(("144.111043", "123.747997"), ("144.111043", "144.250000"), EDGE_UUIDS[2]),
        gr_line(("144.111043", "144.250000"), ("150.000000", "144.250000"), EDGE_UUIDS[3]),
        gr_line(("150.000000", "144.250000"), ("150.000000", "139.175891"), EDGE_UUIDS[4]),
        gr_line(("150.000000", "139.175891"), ("152.769828", "139.175891"), EDGE_UUIDS[5]),
    ]
    text = replace_uuid(text, "gr_line", OLD_EDGE_UUID, "\n\t".join(edges))
    quoted = f'"{OLD_EDGE_UUID}"'
    if text.count(quoted) != 1:
        raise ValueError("unexpected Edge.Cuts group state")
    text = text.replace(quoted, " ".join(f'"{u}"' for u in EDGE_UUIDS), 1)

    for uid in (
        "b6e262ab-112a-4aec-a375-10baa529f63e",
        "4ddd41fb-2b70-431a-ac03-133940fe8c9b",
    ):
        text = remove_uuid(text, "segment", uid)

    vcc_notch = [
        segment(("136.695","131.61"),("141.5","131.61"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000001"),
        segment(("141.5","131.61"),("141.5","123.15"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000002"),
        segment(("141.5","123.15"),("144.72","123.15"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000003"),
        segment(("143.03","120.1"),("144.72","121.79"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000004"),
        segment(("144.72","121.79"),("144.72","123.15"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000005"),
        segment(("144.72","123.15"),("144.72","126.861786"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000006"),
        segment(("144.72","126.861786"),("144.8905","127.032286"),"0.381","F.Cu",3,"3d3d0002-0000-4000-8000-000000000007"),
    ]
    text = replace_uuid(
        text, "segment", "c992ed9d-871b-4175-8587-7aea69a149d8",
        "\n\t".join(vcc_notch),
    )

    for uid in (
        "61201bf3-5d7a-4139-9a00-918afa211305",
        "ad3afa37-5d1c-4f74-863c-60814b2ce7c9",
    ):
        text = remove_uuid(text, "segment", uid)
    text = remove_uuid(text, "via", "9e118286-0035-495c-8cfe-b4182667bbd8")

    relocated = "\n\t".join([
        segment(("146.443984","133.06"),("145.3","133.81"),"0.381","F.Cu",3,"3d3d0003-0000-4000-8000-000000000001"),
        '(via\n\t\t(at 145.3 133.81)\n\t\t(size 0.4)\n\t\t(drill 0.3)\n'
        '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net 3)\n'
        '\t\t(uuid "3d3d0003-0000-4000-8000-000000000003")\n\t)',
        segment(("145.3","133.81"),("145.701524","134.560002"),"0.381","B.Cu",3,"3d3d0003-0000-4000-8000-000000000002"),
    ])
    text = replace_uuid(
        text, "segment", "7292750a-d8ce-4ae7-af47-971813d11a90", relocated
    )

    text = remove_uuid(text, "segment", "2317eaaf-21e6-4023-b6db-ca58196bac19")
    text = remove_uuid(text, "segment", "6820dad4-1b71-4728-a8f1-85c254ada3a2")
    text = remove_uuid(text, "via", "46d54c98-0f16-4fbd-80d5-7c4789c1229e")
    text = replace_uuid(
        text, "segment", "3c3c0005-0000-4000-8000-000000000001",
        segment(("151.129969","128.715031"),("151.705","130.22"),"0.254","B.Cu",76,
                "3d3d0004-0000-4000-8000-000000000001"),
    )

    if "(filled_polygon" in text:
        raise ValueError("generated zone-fill cache must stay stripped")

    PCB.write_text(text, encoding="utf-8")
    actual = git_blob(PCB)
    if actual != RESULT_BLOB:
        raise SystemExit(f"Task 3D output blob mismatch: {actual}")
    print(f"Task 3D PCB generated: {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
