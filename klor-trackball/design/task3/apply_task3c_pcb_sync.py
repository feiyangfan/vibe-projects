#!/usr/bin/env python3
"""Apply Task 3C to the KLOR trackball derivative PCB.

This is a deterministic one-shot transformation of the Task 3B PCB baseline.
It exists because the board is large enough that the repository connector cannot
reliably replace the full KiCad file in one API request.

Task 3C intentionally does NOT final-place J4, cut the breakout pass-through,
or route J4 to U1. Those belong to Tasks 3D and 3E.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
PCB = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_pcb"

EXPECTED_BASELINE_BLOB = "d16dc2e1e8730500f7844146e7c437db3b8d7b44"

PMW_NETS = {
    82: "PMW_CS",
    83: "PMW_MISO",
    84: "PMW_MOSI",
    85: "PMW_SCK",
}

REMOVE_SEGMENTS = {
    # col1 branch serving only removed SW22, from the retained trunk outward
    "a5c451f8-6dc6-4503-9540-8cf8fe63cdd7",
    "75680178-3284-404f-a108-e0389f8dbc58",
    "f6b50e88-f77d-4ef2-ab08-e02b8dc970cb",
    "3ab35c98-9ef7-4b0f-89b2-a3bb2f546e30",
    "d045974b-73a5-42e6-bd8a-f0b5a26a01f3",
    "af7f3b0e-077b-4029-b1ff-6d9f94464c82",
    "5681bcd8-e9ed-4063-9b6c-1c6b03621ad7",
    "10d4a256-ab56-46d2-9b55-68e384ed4d5a",
    "45a1d391-9e76-4693-ac10-bd1bd5955643",

    # row3 branch serving only removed D22, beginning at retained D21
    "a8cb1f86-c566-43c9-bb63-acfaaacafd53",
    "da34ce1e-2bb5-482a-8e8b-3b9926147f27",
    "7ea9fc87-3b01-4f26-b0ba-9f8b69f7dd9c",
    "57cc2a0e-0c4a-4c14-99c2-c667fc07b897",
    "2ab6f907-81d3-4cf8-a8fe-cd0d5649e28e",
    "f2ea522f-a304-4f7d-8248-2a11ebe25da5",
    "d1149fd2-9ec5-4c49-a971-e765407c8197",

    # legacy MCU ownership branches retired by Task 2/3B
    "d4d0e79b-7ddf-48fe-9ac8-f5ed4856d7dc",  # AUDIO / GP9
    "2133a1d4-10c1-4006-a67f-58b30de7b9c5",
    "cd508ce5-c991-4809-b47f-01571bf463b5",  # SDA / GP2
    "5d05c776-f12f-43d1-9a26-952e2c749b82",
    "df5dc2f7-11e2-44b6-98d8-184f49b2000f",
    "c363e1b2-cd63-4a4b-8b67-5c9aed97eb60",
    "ea3f5ef2-c8f2-49ac-bc92-e04759288aa2",  # SCL / GP3
    "00d834c7-78ac-4ea5-9695-d1f547fd8520",
    "cf24cc54-dda1-410e-9052-812fd9921276",
    "8600fe76-db9a-450c-88e8-a1eeea8bc3bb",
    "eeb1b5bf-b6b2-4a6a-98cd-41efc54627d9",

    # SW13 -> deleted SW22 RGB branch after the retained splice point
    "3a8a28ee-1366-4600-b326-059bf3c7d85b",
    "e4d33aa3-5103-49a2-aff1-18f4b89003d8",
    "a9f862b3-5ae0-46f4-842b-97ca133e0ea3",
    "757b767e-d99a-4f8b-842e-6ebc11b0f5f3",
    "52aff1de-7a34-4f59-879b-6d886437f060",
    "7fa53e4b-664b-4c64-a033-9363eff0039b",
    "cbd0f15f-177f-40db-a878-5206b299951c",
    "38e94825-c2dd-4e38-8583-40b8bee50e4f",

    # SW14 -> deleted SW22 RGB branch after the retained splice point
    "1b7c1dc3-0a7c-44c2-9da1-a4a557a0baba",
    "6e4897ff-4c43-4927-a804-c946e12e3e50",
    "da6e708a-f714-483c-aff4-65ffd6d479ae",
    "e6bb7d98-f70e-496d-8c23-6f08b02f0dea",
}

# Stock RX contains the U1 reversible-socket cross-connect plus the long J1 path.
# Keep only the cross-connect, reassign it to PMW_MISO, and delete everything else.
KEEP_RX_AS_PMW_MISO = {
    "70521ba8-4ec8-4c0d-ae30-79bfd86e52f1",
    "55e98c12-e2ae-4b12-af14-9d9833caa820",
    "57b4d7d1-6efd-48f9-b451-3c739bf53526",
}

REASSIGN_SEGMENTS = {
    # GP9 / PMW_CS
    "36294583-05c0-4e50-9170-2b177913f839": (2, 82),
    "5d6e15c1-a2e7-4f4a-add1-dbc9df9b8d66": (2, 82),
    "a3f093e2-c16e-4156-b23e-066cbe9ae5de": (2, 82),

    # GP2 / PMW_SCK
    "7a3b2b66-261f-4ec2-b546-a3e82cffebcb": (6, 85),
    "c5466b86-b18e-49f3-803c-8c74489a47db": (6, 85),
    "12311a20-e55a-463f-b7f4-8ef9976ede32": (6, 85),

    # GP3 / PMW_MOSI
    "17833b1a-fc87-4911-9770-0401ac73c6cc": (7, 84),
    "7c09bcda-3ee6-44c6-b4fd-ee25e9a92f62": (7, 84),
    "6d6c8e31-99f5-444b-8c92-30aeb077ef4b": (7, 84),

    # GP4 / PMW_MISO
    "70521ba8-4ec8-4c0d-ae30-79bfd86e52f1": (28, 83),
    "55e98c12-e2ae-4b12-af14-9d9833caa820": (28, 83),
    "57b4d7d1-6efd-48f9-b451-3c739bf53526": (28, 83),
}

REMOVE_VIAS = {
    "782a8894-c746-4fb8-87a7-634db287d06d",  # deleted col1 -> SW22 branch
    "436efdef-bd58-43f2-b575-c98bf9be0963",  # deleted RGB -> SW22 branch
}

RGB_SPLICE_UUID = "3c3c0005-0000-4000-8000-000000000001"
J4_UUID = "3c3c0004-0000-4000-8000-000000000001"


@dataclass(frozen=True)
class Block:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Patch:
    start: int
    end: int
    text: str
    label: str


def git_blob(path: Path) -> str:
    p = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
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
    raise ValueError("unbalanced KiCad s-expression")


def root_blocks(text: str, token: str) -> list[Block]:
    out: list[Block] = []
    pos = 0
    while True:
        pos = text.find(token, pos)
        if pos < 0:
            break
        expr, expr_end = balanced_block(text, pos)
        line_start = text.rfind("\n", 0, pos) + 1
        line_end = expr_end + (1 if expr_end < len(text) and text[expr_end] == "\n" else 0)
        out.append(Block(line_start, line_end, expr))
        pos = expr_end
    return out


def ref(block: str) -> str | None:
    m = re.search(r'\(property "Reference" "([^"]+)"', block)
    return m.group(1) if m else None


def uuid(block: str) -> str | None:
    m = re.search(r'\(uuid "([^"]+)"\)', block)
    return m.group(1) if m else None


def net_id(block: str) -> int | None:
    m = re.search(r"\(net (\d+)\)", block)
    return int(m.group(1)) if m else None


def replacement(block: Block, new_expr: str, label: str) -> Patch:
    return Patch(block.start, block.end, "\t" + new_expr + "\n", label)


def remove(block: Block, label: str) -> Patch:
    return Patch(block.start, block.end, "", label)


def j4_footprint() -> str:
    # Deliberately staged completely outside the stock Edge.Cuts. Task 3D owns
    # production XY/rotation. At rotation 0 the row is parallel to KiCad Y and,
    # after the locked KiCad->Gerber Y reflection, pin 1 is the negative-global-Y end.
    return r'''(footprint "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"
        (layer "F.Cu")
        (uuid "3c3c0004-0000-4000-8000-000000000001")
        (at 60 70)
        (descr "Through hole straight pin header, 1x07, 2.54mm pitch, single row")
        (tags "Through hole pin header THT 1x07 2.54mm single row")
        (property "Reference" "J4"
            (at 0 2.33 0)
            (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000002")
            (effects (font (size 1 1) (thickness 0.15)))
        )
        (property "Value" "PMW3360 Kivipallur"
            (at 0 -17.57 0)
            (layer "F.Fab")
            (uuid "3c3c0004-0000-4000-8000-000000000003")
            (effects (font (size 1 1) (thickness 0.15)))
        )
        (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"
            (at 0 0 0)
            (layer "F.Fab")
            (hide yes)
            (uuid "3c3c0004-0000-4000-8000-000000000004")
            (effects (font (size 1.27 1.27) (thickness 0.15)))
        )
        (property "Datasheet" "~"
            (at 0 0 0)
            (layer "F.Fab")
            (hide yes)
            (uuid "3c3c0004-0000-4000-8000-000000000005")
            (effects (font (size 1.27 1.27) (thickness 0.15)))
        )
        (property "Description" "KLOR keyboard-side mate for Kivipallur PMW3360 breakout"
            (at 0 0 0)
            (layer "F.Fab")
            (hide yes)
            (uuid "3c3c0004-0000-4000-8000-000000000006")
            (effects (font (size 1.27 1.27) (thickness 0.15)))
        )
        (path "/3b3b0004-0000-4000-8000-000000000001")
        (sheetfile "konrad_trackball.kicad_sch")
        (attr through_hole)
        (fp_line (start -1.33 -16.57) (end 1.33 -16.57)
            (stroke (width 0.12) (type solid)) (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000011"))
        (fp_line (start -1.33 -16.57) (end -1.33 -1.27)
            (stroke (width 0.12) (type solid)) (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000012"))
        (fp_line (start 1.33 -16.57) (end 1.33 -1.27)
            (stroke (width 0.12) (type solid)) (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000013"))
        (fp_line (start -1.33 -1.27) (end 1.33 -1.27)
            (stroke (width 0.12) (type solid)) (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000014"))
        (fp_line (start -1.33 1.33) (end 0 1.33)
            (stroke (width 0.12) (type solid)) (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000015"))
        (fp_line (start -1.33 0) (end -1.33 1.33)
            (stroke (width 0.12) (type solid)) (layer "F.SilkS")
            (uuid "3c3c0004-0000-4000-8000-000000000016"))
        (fp_rect (start -1.8 -17.05) (end 1.8 1.8)
            (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd")
            (uuid "3c3c0004-0000-4000-8000-000000000017"))
        (fp_rect (start -1.27 -16.51) (end 1.27 1.27)
            (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab")
            (uuid "3c3c0004-0000-4000-8000-000000000018"))
        (fp_text user "${REFERENCE}"
            (at 0 -7.62 90)
            (layer "F.Fab")
            (uuid "3c3c0004-0000-4000-8000-000000000019")
            (effects (font (size 1 1) (thickness 0.15)))
        )
        (pad "1" thru_hole rect
            (at 0 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no) (net 82 "PMW_CS")
            (pinfunction "Pin_1") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000101"))
        (pad "2" thru_hole oval
            (at 0 -2.54) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no) (net 83 "PMW_MISO")
            (pinfunction "Pin_2") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000102"))
        (pad "3" thru_hole oval
            (at 0 -5.08) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no) (net 84 "PMW_MOSI")
            (pinfunction "Pin_3") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000103"))
        (pad "4" thru_hole oval
            (at 0 -7.62) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no) (net 85 "PMW_SCK")
            (pinfunction "Pin_4") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000104"))
        (pad "5" thru_hole oval
            (at 0 -10.16) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (pinfunction "Pin_5") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000105"))
        (pad "6" thru_hole oval
            (at 0 -12.7) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no) (net 3 "VCC")
            (pinfunction "Pin_6") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000106"))
        (pad "7" thru_hole oval
            (at 0 -15.24) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")
            (remove_unused_layers no) (net 1 "GND")
            (pinfunction "Pin_7") (pintype "passive")
            (uuid "3c3c0004-0000-4000-8000-000000000107"))
    )'''


def main() -> int:
    baseline = git_blob(PCB)
    if baseline != EXPECTED_BASELINE_BLOB:
        raise SystemExit(
            f"refusing to transform unexpected PCB blob {baseline}; "
            f"expected {EXPECTED_BASELINE_BLOB}"
        )

    text = PCB.read_text(encoding="utf-8")
    footprints = root_blocks(text, "(footprint ")
    segments = root_blocks(text, "(segment\n")
    vias = root_blocks(text, "(via\n")
    patches: list[Patch] = []

    # Components removed by the locked R34 deletion.
    for wanted in ("SW22", "D22"):
        matches = [b for b in footprints if ref(b.text) == wanted]
        if len(matches) != 1:
            raise SystemExit(f"{wanted}: expected one footprint, got {len(matches)}")
        patches.append(remove(matches[0], f"remove {wanted}"))

    # Reassign MCU socket pads to semantic PMW nets.
    u1 = next((b for b in footprints if ref(b.text) == "U1"), None)
    if u1 is None:
        raise SystemExit("U1 footprint not found")
    new_u1 = u1.text
    for old, new, expected in (
        ('(net 6 "SDA")', '(net 85 "PMW_SCK")', 2),
        ('(net 7 "SCL")', '(net 84 "PMW_MOSI")', 2),
        ('(net 28 "RX")', '(net 83 "PMW_MISO")', 2),
        ('(net 2 "AUDIO")', '(net 82 "PMW_CS")', 2),
    ):
        count = new_u1.count(old)
        if count != expected:
            raise SystemExit(f"U1 {old}: expected {expected}, got {count}")
        new_u1 = new_u1.replace(old, new)
    patches.append(replacement(u1, new_u1, "U1 PMW ownership"))

    # J1.3 becomes physically isolated/no-net. J1.4/TX is unchanged.
    j1 = next((b for b in footprints if ref(b.text) == "J1"), None)
    if j1 is None:
        raise SystemExit("J1 footprint not found")
    if j1.text.count('(net 28 "RX")') != 2:
        raise SystemExit("J1.3 duplicated RX pad assignment not as expected")
    new_j1 = re.sub(r'\n\t\t\t\(net 28 "RX"\)', "", j1.text)
    patches.append(replacement(j1, new_j1, "J1.3 no-net"))

    # SW14 DIN is merged into the retained SW13 DOUT net.
    sw14 = next((b for b in footprints if ref(b.text) == "SW14"), None)
    if sw14 is None:
        raise SystemExit("SW14 footprint not found")
    if sw14.text.count('(net 77 "Net-(SW14B-DIN)")') != 2:
        raise SystemExit("SW14 DIN duplicated pad assignment not as expected")
    new_sw14 = sw14.text.replace(
        '(net 77 "Net-(SW14B-DIN)")',
        '(net 76 "Net-(SW13B-DOUT)")',
    )
    patches.append(replacement(sw14, new_sw14, "SW14 DIN -> RGB bypass net"))

    remove_segments = set(REMOVE_SEGMENTS)

    # The complete local switch/diode net is obsolete with SW22/D22 removed.
    remove_segments.update(
        uuid(b.text) for b in segments if net_id(b.text) == 46
    )

    # Retire the entire J1/RX path; keep only the U1 reversible cross-connect.
    remove_segments.update(
        uuid(b.text)
        for b in segments
        if net_id(b.text) == 28 and uuid(b.text) not in KEEP_RX_AS_PMW_MISO
    )

    seen_removed: set[str] = set()
    seen_reassigned: set[str] = set()

    for block in segments:
        uid = uuid(block.text)
        nid = net_id(block.text)
        if uid in remove_segments:
            patches.append(remove(block, f"remove segment {uid}"))
            seen_removed.add(uid)
        elif uid in REASSIGN_SEGMENTS:
            old_id, new_id = REASSIGN_SEGMENTS[uid]
            if nid != old_id:
                raise SystemExit(
                    f"{uid}: expected net {old_id} before reassignment, got {nid}"
                )
            patches.append(
                replacement(
                    block,
                    block.text.replace(f"(net {old_id})", f"(net {new_id})"),
                    f"reassign segment {uid}",
                )
            )
            seen_reassigned.add(uid)
        elif nid == 77:
            patches.append(
                replacement(
                    block,
                    block.text.replace("(net 77)", "(net 76)"),
                    f"merge RGB segment {uid}",
                )
            )

    missing = remove_segments - seen_removed
    if missing:
        raise SystemExit(f"expected removable segments not found: {sorted(missing)}")
    missing = set(REASSIGN_SEGMENTS) - seen_reassigned
    if missing:
        raise SystemExit(f"expected reassigned segments not found: {sorted(missing)}")

    remove_vias = set(REMOVE_VIAS)
    remove_vias.update(uuid(b.text) for b in vias if net_id(b.text) in (28, 46))
    seen_removed_vias: set[str] = set()

    for block in vias:
        uid = uuid(block.text)
        nid = net_id(block.text)
        if uid in remove_vias:
            patches.append(remove(block, f"remove via {uid}"))
            seen_removed_vias.add(uid)
        elif nid == 77:
            patches.append(
                replacement(
                    block,
                    block.text.replace("(net 77)", "(net 76)"),
                    f"merge RGB via {uid}",
                )
            )

    missing = remove_vias - seen_removed_vias
    if missing:
        raise SystemExit(f"expected removable vias not found: {sorted(missing)}")

    # Retire obsolete nets; keep AUDIO/SDA/SCL as isolated legacy optional nets.
    for nid, name in (
        (28, "RX"),
        (46, "Net-(D22-A)"),
        (77, "Net-(SW14B-DIN)"),
    ):
        needle = f'\t(net {nid} "{name}")\n'
        pos = text.find(needle)
        if pos < 0:
            raise SystemExit(f"net definition missing: {nid} {name}")
        patches.append(Patch(pos, pos + len(needle), "", f"remove net {nid}"))

    anchor = '\t(net 81 "col5")\n'
    pos = text.find(anchor)
    if pos < 0:
        raise SystemExit("net 81 anchor not found")
    insert_at = pos + len(anchor)
    patches.append(
        Patch(
            insert_at,
            insert_at,
            "".join(f'\t(net {nid} "{name}")\n' for nid, name in PMW_NETS.items()),
            "add PMW semantic nets",
        )
    )

    # Introduce J4, but park it outside the board. 3D owns final mechanical XY.
    if any(ref(b.text) == "J4" for b in footprints):
        raise SystemExit("J4 unexpectedly already present")
    last_fp = footprints[-1]
    patches.append(
        Patch(last_fp.end, last_fp.end, "\t" + j4_footprint() + "\n", "add staged J4")
    )

    # Join retained SW13 route to retained SW14 route at x ~= 148.1, safely on
    # the non-slot side of the future breakout datum x ~= 143.111.
    first_via = vias[0]
    bypass = '''\t(segment
        (start 148.115 131.73)
        (end 148.109492 133.815508)
        (width 0.254)
        (layer "B.Cu")
        (net 76)
        (uuid "3c3c0005-0000-4000-8000-000000000001")
    )
'''
    patches.append(Patch(first_via.start, first_via.start, bypass, "RGB bypass splice"))

    # Replacements must not overlap.
    ordered = sorted(patches, key=lambda p: (p.start, p.end))
    for prev, cur in zip(ordered, ordered[1:]):
        if (
            prev.end > cur.start
            and prev.start != prev.end
            and cur.start != cur.end
        ):
            raise SystemExit(f"overlapping patches: {prev.label} / {cur.label}")

    out = text
    for patch in sorted(patches, key=lambda p: (p.start, p.end), reverse=True):
        out = out[: patch.start] + patch.text + out[patch.end :]

    # Hard postconditions before writing the generated board.
    required = (
        '(net 82 "PMW_CS")',
        '(net 83 "PMW_MISO")',
        '(net 84 "PMW_MOSI")',
        '(net 85 "PMW_SCK")',
        '(property "Reference" "J4"',
        '(at 60 70)',
        '(start 148.115 131.73)',
        '(end 148.109492 133.815508)',
        f'(uuid "{RGB_SPLICE_UUID}")',
        f'(uuid "{J4_UUID}")',
    )
    for needle in required:
        if needle not in out:
            raise SystemExit(f"postcondition missing: {needle}")

    forbidden = (
        '(property "Reference" "SW22"',
        '(property "Reference" "D22"',
        '\t(net 28 "RX")',
        '\t(net 46 "Net-(D22-A)")',
        '\t(net 77 "Net-(SW14B-DIN)")',
    )
    for needle in forbidden:
        if needle in out:
            raise SystemExit(f"retired item remains: {needle}")

    for uid in remove_segments | remove_vias:
        if uid and uid in out:
            raise SystemExit(f"removed UUID remains: {uid}")

    # Basic structural validation.
    balanced_block(out, 0)
    if out.count("(") != out.count(")"):
        raise SystemExit("generated board has mismatched parentheses")

    PCB.write_text(out, encoding="utf-8")

    print("Task 3C PCB synchronization applied")
    print(f"baseline blob: {baseline}")
    print(f"removed segments: {len(remove_segments)}")
    print(f"removed vias: {len(remove_vias)}")
    print("J4 staging position: (60, 70) F.Cu; final placement deferred to 3D")
    print("RGB splice: B.Cu (148.115,131.73) -> (148.109492,133.815508)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
