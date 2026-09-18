#!/usr/bin/env python3
"""Task 3C audit: destructive PCB synchronization and preservation checks."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
STOCK_DIR = ROOT / "klor1.4/PCB/klor1_4"
DERIV_DIR = ROOT / "PCB/konrad_trackball"

STOCK_PCB = STOCK_DIR / "klor1_4.kicad_pcb"
STOCK_SCH = STOCK_DIR / "klor1_4.kicad_sch"
DERIV_PCB = DERIV_DIR / "konrad_trackball.kicad_pcb"
DERIV_SCH = DERIV_DIR / "konrad_trackball.kicad_sch"

STOCK_PCB_BLOB = "d16dc2e1e8730500f7844146e7c437db3b8d7b44"
STOCK_SCH_BLOB = "4f68892c9d13ffe4200587708eeb4c43ee2b652b"
TASK3B_SCH_BLOB = "4239dd2f139be30e24ee7109800a5ae9f179aee3"
TASK3C_PCB_BLOB = "9e34c771ed27f5f87d79cd7cc78e41c8ec1bbb74"

J4_UUID = "3c3c0004-0000-4000-8000-000000000001"
RGB_BRIDGE_UUID = "3c3c0005-0000-4000-8000-000000000001"

PMW_NETS = {
    82: "PMW_CS",
    83: "PMW_MISO",
    84: "PMW_MOSI",
    85: "PMW_SCK",
}

REASSIGNED_SEGMENTS = {
    "36294583-05c0-4e50-9170-2b177913f839": (2, 82),
    "5d6e15c1-a2e7-4f4a-add1-dbc9df9b8d66": (2, 82),
    "a3f093e2-c16e-4156-b23e-066cbe9ae5de": (2, 82),
    "7a3b2b66-261f-4ec2-b546-a3e82cffebcb": (6, 85),
    "c5466b86-b18e-49f3-803c-8c74489a47db": (6, 85),
    "12311a20-e55a-463f-b7f4-8ef9976ede32": (6, 85),
    "17833b1a-fc87-4911-9770-0401ac73c6cc": (7, 84),
    "7c09bcda-3ee6-44c6-b4fd-ee25e9a92f62": (7, 84),
    "6d6c8e31-99f5-444b-8c92-30aeb077ef4b": (7, 84),
    "70521ba8-4ec8-4c0d-ae30-79bfd86e52f1": (28, 83),
    "55e98c12-e2ae-4b12-af14-9d9833caa820": (28, 83),
    "57b4d7d1-6efd-48f9-b451-3c739bf53526": (28, 83),
}

EXPLICIT_REMOVED_SEGMENTS = {
    # col1 -> SW22
    "a5c451f8-6dc6-4503-9540-8cf8fe63cdd7",
    "75680178-3284-404f-a108-e0389f8dbc58",
    "f6b50e88-f77d-4ef2-ab08-e02b8dc970cb",
    "3ab35c98-9ef7-4b0f-89b2-a3bb2f546e30",
    "d045974b-73a5-42e6-bd8a-f0b5a26a01f3",
    "af7f3b0e-077b-4029-b1ff-6d9f94464c82",
    "5681bcd8-e9ed-4063-9b6c-1c6b03621ad7",
    "10d4a256-ab56-46d2-9b55-68e384ed4d5a",
    "45a1d391-9e76-4693-ac10-bd1bd5955643",

    # row3 -> D22
    "a8cb1f86-c566-43c9-bb63-acfaaacafd53",
    "da34ce1e-2bb5-482a-8e8b-3b9926147f27",
    "7ea9fc87-3b01-4f26-b0ba-9f8b69f7dd9c",
    "57cc2a0e-0c4a-4c14-99c2-c667fc07b897",
    "2ab6f907-81d3-4cf8-a8fe-cd0d5649e28e",
    "f2ea522f-a304-4f7d-8248-2a11ebe25da5",
    "d1149fd2-9ec5-4c49-a971-e765407c8197",

    # legacy MCU ownership branches
    "d4d0e79b-7ddf-48fe-9ac8-f5ed4856d7dc",
    "2133a1d4-10c1-4006-a67f-58b30de7b9c5",
    "cd508ce5-c991-4809-b47f-01571bf463b5",
    "5d05c776-f12f-43d1-9a26-952e2c749b82",
    "df5dc2f7-11e2-44b6-98d8-184f49b2000f",
    "c363e1b2-cd63-4a4b-8b67-5c9aed97eb60",
    "ea3f5ef2-c8f2-49ac-bc92-e04759288aa2",
    "00d834c7-78ac-4ea5-9695-d1f547fd8520",
    "cf24cc54-dda1-410e-9052-812fd9921276",
    "8600fe76-db9a-450c-88e8-a1eeea8bc3bb",
    "eeb1b5bf-b6b2-4a6a-98cd-41efc54627d9",

    # deleted SW22 RGB tails
    "3a8a28ee-1366-4600-b326-059bf3c7d85b",
    "e4d33aa3-5103-49a2-aff1-18f4b89003d8",
    "a9f862b3-5ae0-46f4-842b-97ca133e0ea3",
    "757b767e-d99a-4f8b-842e-6ebc11b0f5f3",
    "52aff1de-7a34-4f59-879b-6d886437f060",
    "7fa53e4b-664b-4c64-a033-9363eff0039b",
    "cbd0f15f-177f-40db-a878-5206b299951c",
    "38e94825-c2dd-4e38-8583-40b8bee50e4f",
    "1b7c1dc3-0a7c-44c2-9da1-a4a557a0baba",
    "6e4897ff-4c43-4927-a804-c946e12e3e50",
    "da6e708a-f714-483c-aff4-65ffd6d479ae",
    "e6bb7d98-f70e-496d-8c23-6f08b02f0dea",
}

EXPLICIT_REMOVED_VIAS = {
    "782a8894-c746-4fb8-87a7-634db287d06d",
    "436efdef-bd58-43f2-b575-c98bf9be0963",
}

REQUIRED_PMW_SEGMENTS = {
    82: {
        "36294583-05c0-4e50-9170-2b177913f839",
        "5d6e15c1-a2e7-4f4a-add1-dbc9df9b8d66",
        "a3f093e2-c16e-4156-b23e-066cbe9ae5de",
    },
    83: {
        "70521ba8-4ec8-4c0d-ae30-79bfd86e52f1",
        "55e98c12-e2ae-4b12-af14-9d9833caa820",
        "57b4d7d1-6efd-48f9-b451-3c739bf53526",
    },
    84: {
        "17833b1a-fc87-4911-9770-0401ac73c6cc",
        "7c09bcda-3ee6-44c6-b4fd-ee25e9a92f62",
        "6d6c8e31-99f5-444b-8c92-30aeb077ef4b",
    },
    85: {
        "7a3b2b66-261f-4ec2-b546-a3e82cffebcb",
        "c5466b86-b18e-49f3-803c-8c74489a47db",
        "12311a20-e55a-463f-b7f4-8ef9976ede32",
    },
}


@dataclass(frozen=True)
class Segment:
    uuid: str
    start: tuple[float, float]
    end: tuple[float, float]
    width: float
    layer: str
    net: int


@dataclass(frozen=True)
class Via:
    uuid: str
    at: tuple[float, float]
    size: float | None
    drill: float | None
    net: int


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
    raise ValueError("unbalanced s-expression")


def blocks(text: str, token: str) -> list[str]:
    out: list[str] = []
    pos = 0
    while True:
        pos = text.find(token, pos)
        if pos < 0:
            break
        block, end = balanced_block(text, pos)
        out.append(block)
        pos = end
    return out


def uuid(block: str) -> str:
    m = re.search(r'\(uuid "([^"]+)"\)', block)
    if not m:
        raise ValueError("UUID missing")
    return m.group(1)


def ref(block: str) -> str | None:
    m = re.search(r'\(property "Reference" "([^"]+)"', block)
    return m.group(1) if m else None


def top_at(block: str) -> tuple[float, float, float]:
    # First top-level (at ...) after the footprint header. Accept tabs or spaces;
    # the generated J4 block is intentionally formatted independently of stock.
    m = re.search(
        r'^\(footprint "[^"]+"[\s\S]*?\n\s*\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)',
        block,
    )
    if not m:
        raise ValueError(f"footprint at missing for {ref(block)}")
    return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)


def top_layer(block: str) -> str:
    # First layer in a footprint block is the footprint side.
    m = re.search(
        r'^\(footprint "[^"]+"[\s\S]*?\n\s*\(layer "([^"]+)"\)',
        block,
    )
    if not m:
        raise ValueError(f"footprint layer missing for {ref(block)}")
    return m.group(1)


def strip_pad_nets(block: str) -> str:
    return re.sub(r'\n\t\t\t\(net \d+ "[^"]*"\)', "", block)


def parse_segments(text: str) -> dict[str, Segment]:
    result: dict[str, Segment] = {}
    for block in blocks(text, "(segment\n"):
        uid = uuid(block)
        sm = re.search(r"\(start ([\d.-]+) ([\d.-]+)\)", block)
        em = re.search(r"\(end ([\d.-]+) ([\d.-]+)\)", block)
        wm = re.search(r"\(width ([\d.-]+)\)", block)
        lm = re.search(r'\(layer "([^"]+)"\)', block)
        nm = re.search(r"\(net (\d+)\)", block)
        if not all((sm, em, wm, lm, nm)):
            raise ValueError(f"incomplete segment {uid}")
        result[uid] = Segment(
            uid,
            (float(sm.group(1)), float(sm.group(2))),
            (float(em.group(1)), float(em.group(2))),
            float(wm.group(1)),
            lm.group(1),
            int(nm.group(1)),
        )
    return result


def parse_vias(text: str) -> dict[str, Via]:
    result: dict[str, Via] = {}
    for block in blocks(text, "(via\n"):
        uid = uuid(block)
        am = re.search(r"\(at ([\d.-]+) ([\d.-]+)\)", block)
        sm = re.search(r"\(size ([\d.-]+)\)", block)
        dm = re.search(r"\(drill ([\d.-]+)\)", block)
        nm = re.search(r"\(net (\d+)\)", block)
        if not am or not nm:
            raise ValueError(f"incomplete via {uid}")
        result[uid] = Via(
            uid,
            (float(am.group(1)), float(am.group(2))),
            float(sm.group(1)) if sm else None,
            float(dm.group(1)) if dm else None,
            int(nm.group(1)),
        )
    return result


def parse_net_defs(text: str) -> dict[int, str]:
    return {
        int(m.group(1)): m.group(2)
        for m in re.finditer(r'^\t\(net (\d+) "([^"]*)"\)$', text, re.M)
    }


def footprint_map(text: str) -> dict[str, str]:
    result = {}
    for block in blocks(text, "(footprint "):
        r = ref(block)
        if r:
            if r in result:
                raise ValueError(f"duplicate footprint reference {r}")
            result[r] = block
    return result


def pad_blocks(fp: str) -> list[str]:
    return blocks(fp, "(pad ")


def pads_by_number(fp: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for block in pad_blocks(fp):
        m = re.match(r'^\(pad "([^"]*)"', block)
        if not m:
            continue
        result.setdefault(m.group(1), []).append(block)
    return result


def pad_net(block: str) -> tuple[int, str] | None:
    m = re.search(r'\(net (\d+) "([^"]*)"\)', block)
    return (int(m.group(1)), m.group(2)) if m else None


def edge_blocks(text: str) -> list[str]:
    out = []
    for token in ("(gr_line\n", "(gr_rect\n", "(gr_circle\n", "(gr_curve\n", "(gr_poly\n"):
        out.extend(b for b in blocks(text, token) if '(layer "Edge.Cuts")' in b)
    return sorted(out)


def edge_bbox(text: str) -> tuple[float, float, float, float]:
    points: list[tuple[float, float]] = []
    for block in edge_blocks(text):
        for m in re.finditer(
            r"\((?:start|end|mid|center|xy) ([\d.-]+) ([\d.-]+)\)",
            block,
        ):
            points.append((float(m.group(1)), float(m.group(2))))
    if not points:
        raise ValueError("no Edge.Cuts points")
    return (
        min(p[0] for p in points),
        max(p[0] for p in points),
        min(p[1] for p in points),
        max(p[1] for p in points),
    )


def point_eq(a: tuple[float, float], b: tuple[float, float], eps: float = 1e-9) -> bool:
    return math.dist(a, b) <= eps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    stock = STOCK_PCB.read_text(encoding="utf-8")
    deriv = DERIV_PCB.read_text(encoding="utf-8")

    sfp = footprint_map(stock)
    dfp = footprint_map(deriv)
    sseg = parse_segments(stock)
    dseg = parse_segments(deriv)
    svia = parse_vias(stock)
    dvia = parse_vias(deriv)
    snets = parse_net_defs(stock)
    dnets = parse_net_defs(deriv)

    expected_removed_segments = set(EXPLICIT_REMOVED_SEGMENTS)
    expected_removed_segments.update(
        uid for uid, seg in sseg.items()
        if seg.net == 46
    )
    expected_removed_segments.update(
        uid for uid, seg in sseg.items()
        if seg.net == 28 and uid not in REASSIGNED_SEGMENTS
    )

    expected_removed_vias = set(EXPLICIT_REMOVED_VIAS)
    expected_removed_vias.update(
        uid for uid, via in svia.items()
        if via.net in (28, 46)
    )

    # Segment preservation: everything outside the authorized deletion/rename set
    # must retain identical geometry/layer/width.
    segment_geometry_ok = True
    segment_net_ok = True
    for uid, old in sseg.items():
        if uid in expected_removed_segments:
            segment_geometry_ok &= uid not in dseg
            segment_net_ok &= uid not in dseg
            continue

        new = dseg.get(uid)
        if new is None:
            segment_geometry_ok = False
            segment_net_ok = False
            continue

        segment_geometry_ok &= (
            old.start == new.start
            and old.end == new.end
            and old.width == new.width
            and old.layer == new.layer
        )

        if uid in REASSIGNED_SEGMENTS:
            old_net, new_net = REASSIGNED_SEGMENTS[uid]
            segment_net_ok &= old.net == old_net and new.net == new_net
        elif old.net == 77:
            segment_net_ok &= new.net == 76
        else:
            segment_net_ok &= new.net == old.net

    expected_segment_uuid_set = (
        set(sseg) - expected_removed_segments
    ) | {RGB_BRIDGE_UUID}

    # Via preservation follows the same rule; retained net77 via(s) become net76.
    via_geometry_ok = True
    via_net_ok = True
    for uid, old in svia.items():
        if uid in expected_removed_vias:
            via_geometry_ok &= uid not in dvia
            via_net_ok &= uid not in dvia
            continue
        new = dvia.get(uid)
        if new is None:
            via_geometry_ok = False
            via_net_ok = False
            continue
        via_geometry_ok &= (
            old.at == new.at
            and old.size == new.size
            and old.drill == new.drill
        )
        via_net_ok &= new.net == (76 if old.net == 77 else old.net)

    expected_via_uuid_set = set(svia) - expected_removed_vias

    # Footprint preservation.
    stock_refs = set(sfp)
    deriv_refs = set(dfp)
    retained_refs = stock_refs - {"SW22", "D22"}
    footprints_same_placement = all(
        r in dfp
        and top_at(sfp[r]) == top_at(dfp[r])
        and top_layer(sfp[r]) == top_layer(dfp[r])
        for r in retained_refs
    )
    untouched_footprints_byte_equiv = all(
        sfp[r] == dfp[r]
        for r in retained_refs - {"U1", "J1", "SW14"}
    )
    authorized_footprints_geometry_equiv = all(
        strip_pad_nets(sfp[r]) == strip_pad_nets(dfp[r])
        for r in {"U1", "J1", "SW14"}
    )

    # U1 net ownership.
    u1pads = pads_by_number(dfp["U1"])
    expected_u1 = {
        "5": (85, "PMW_SCK"),
        "6": (84, "PMW_MOSI"),
        "7": (83, "PMW_MISO"),
        "12": (82, "PMW_CS"),
    }
    u1_pmw_exact = all(
        len(u1pads.get(pin, [])) == 2
        and all(pad_net(p) == net for p in u1pads[pin])
        for pin, net in expected_u1.items()
    )

    # TRRS contract.
    j1pads = pads_by_number(dfp["J1"])
    j1_3_no_net = (
        len(j1pads.get("3", [])) == 2
        and all(pad_net(p) is None for p in j1pads["3"])
    )
    j1_4_tx = (
        len(j1pads.get("4", [])) == 2
        and all(pad_net(p) == (31, "TX") for p in j1pads["4"])
    )

    # J4 staging footprint and pin contract.
    j4 = dfp.get("J4", "")
    j4pads = pads_by_number(j4) if j4 else {}
    expected_j4 = {
        "1": (82, "PMW_CS"),
        "2": (83, "PMW_MISO"),
        "3": (84, "PMW_MOSI"),
        "4": (85, "PMW_SCK"),
        "5": None,
        "6": (3, "VCC"),
        "7": (1, "GND"),
    }
    j4_pin_contract = all(
        len(j4pads.get(pin, [])) == 1
        and pad_net(j4pads[pin][0]) == net
        for pin, net in expected_j4.items()
    )
    board_bbox = edge_bbox(deriv)
    j4_at = top_at(j4) if j4 else (math.nan, math.nan, math.nan)
    j4_staged_off_board = (
        j4_at == (60.0, 70.0, 0.0)
        and j4_at[0] < board_bbox[0]
        and top_layer(j4) == "F.Cu"
    )

    # RGB topology.
    sw13pads = pads_by_number(dfp["SW13"])
    sw14pads = pads_by_number(dfp["SW14"])
    rgb_pads_merged = (
        len(sw13pads.get("1", [])) == 2
        and all(pad_net(p) == (76, "Net-(SW13B-DOUT)") for p in sw13pads["1"])
        and len(sw14pads.get("3", [])) == 2
        and all(pad_net(p) == (76, "Net-(SW13B-DOUT)") for p in sw14pads["3"])
    )
    bridge = dseg.get(RGB_BRIDGE_UUID)
    rgb_bridge_exact = (
        bridge is not None
        and bridge.net == 76
        and bridge.layer == "B.Cu"
        and bridge.width == 0.254
        and point_eq(bridge.start, (148.115, 131.73))
        and point_eq(bridge.end, (148.109492, 133.815508))
    )

    pmw_segments_exact = all(
        {uid for uid, seg in dseg.items() if seg.net == nid}
        == REQUIRED_PMW_SEGMENTS[nid]
        for nid in PMW_NETS
    )
    pmw_no_vias = all(via.net not in PMW_NETS for via in dvia.values())

    # Power/matrix/split retained endpoints.
    row3_retained = all(
        r in dfp
        for r in ("D18", "D19", "D20", "D21", "U1")
    ) and all(
        pad_net(p) == (38, "row3")
        for r in ("D18", "D19", "D20", "D21")
        for p in pads_by_number(dfp[r]).get("1", [])
    )
    col1_retained = all(
        r in dfp for r in ("SW5", "SW10", "SW16", "U1")
    ) and all(
        pad_net(p) == (17, "col1")
        for r in ("SW5", "SW10", "SW16")
        for p in pads_by_number(dfp[r]).get("5", [])
    )

    legacy_optional_components_retained = all(
        r in dfp for r in ("J2", "OLED1", "BZ1")
    )
    legacy_nets_retained = all(
        dnets.get(nid) == name
        for nid, name in ((2, "AUDIO"), (6, "SDA"), (7, "SCL"))
    )

    expected_nets = dict(snets)
    for nid in (28, 46, 77):
        expected_nets.pop(nid)
    expected_nets.update(PMW_NETS)

    checks = {
        "stock_pcb_blob_locked": git_blob(STOCK_PCB) == STOCK_PCB_BLOB,
        "stock_schematic_blob_locked": git_blob(STOCK_SCH) == STOCK_SCH_BLOB,
        "task3b_schematic_unchanged": git_blob(DERIV_SCH) == TASK3B_SCH_BLOB,
        "task3c_pcb_blob_locked": git_blob(DERIV_PCB) == TASK3C_PCB_BLOB,
        "pcb_parentheses_balanced": deriv[balanced_block(deriv, 0)[1]:].strip() == "",
        "footprint_reference_set_exact": deriv_refs == retained_refs | {"J4"},
        "sw22_removed": "SW22" not in dfp,
        "d22_removed": "D22" not in dfp,
        "retained_footprint_placement_and_side_unchanged": footprints_same_placement,
        "untouched_retained_footprints_exact": untouched_footprints_byte_equiv,
        "u1_j1_sw14_only_pad_net_edits": authorized_footprints_geometry_equiv,
        "net_table_exact": dnets == expected_nets,
        "rx_net_retired": 28 not in dnets,
        "d22_local_net_retired": 46 not in dnets,
        "old_sw14_din_net_retired": 77 not in dnets,
        "pmw_net_names_exact": all(dnets.get(nid) == name for nid, name in PMW_NETS.items()),
        "u1_pmw_pad_ownership_exact": u1_pmw_exact,
        "j1_pin3_no_net": j1_3_no_net,
        "j1_pin4_tx_preserved": j1_4_tx,
        "j4_exactly_one": deriv_refs.count("J4") == 1 if hasattr(deriv_refs, "count") else "J4" in deriv_refs,
        "j4_pin_contract_exact": j4_pin_contract,
        "j4_front_side_staged_off_board": j4_staged_off_board,
        "edge_cuts_exactly_stock": edge_blocks(stock) == edge_blocks(deriv),
        "all_authorized_segment_deletions_exact": set(dseg) == expected_segment_uuid_set,
        "retained_segment_geometry_unchanged": segment_geometry_ok,
        "segment_net_changes_authorized_only": segment_net_ok,
        "all_authorized_via_deletions_exact": set(dvia) == expected_via_uuid_set,
        "retained_via_geometry_unchanged": via_geometry_ok,
        "via_net_changes_authorized_only": via_net_ok,
        "pmw_u1_crossconnect_segments_exact": pmw_segments_exact,
        "pmw_no_vias_before_routing": pmw_no_vias,
        "rgb_pads_merged_to_net76": rgb_pads_merged,
        "rgb_bridge_exact": rgb_bridge_exact,
        "row3_retained_through_d21": row3_retained,
        "col1_retained_on_other_switches": col1_retained,
        "col1_row3_remain_distinct": dnets.get(17) == "col1" and dnets.get(38) == "row3",
        "legacy_optional_components_retained": legacy_optional_components_retained,
        "legacy_optional_nets_retained_but_no_longer_own_u1": legacy_nets_retained and u1_pmw_exact,
        "tx_net_definition_preserved": dnets.get(31) == "TX",
    }

    result = {
        "task": "3C",
        "status": "complete" if all(checks.values()) else "failed",
        "pcb_blob": git_blob(DERIV_PCB),
        "board_edge_bbox_kicad": {
            "min_x": board_bbox[0],
            "max_x": board_bbox[1],
            "min_y": board_bbox[2],
            "max_y": board_bbox[3],
        },
        "removed_footprints": ["SW22", "D22"],
        "connector": {
            "reference": "J4",
            "staging_xy_kicad": [60.0, 70.0],
            "side": "F.Cu",
            "final_xy_owner": "Task 3D",
            "pins": {
                "1": "PMW_CS",
                "2": "PMW_MISO",
                "3": "PMW_MOSI",
                "4": "PMW_SCK",
                "5": "NC/MOTION",
                "6": "VCC",
                "7": "GND",
            },
        },
        "rgb_bypass": {
            "net": "Net-(SW13B-DOUT)",
            "net_id": 76,
            "bridge_uuid": RGB_BRIDGE_UUID,
            "layer": "B.Cu",
            "start": [148.115, 131.73],
            "end": [148.109492, 133.815508],
        },
        "pmw_routing_state": "U1 reversible cross-connect only; J4-to-U1 route deferred to Task 3E",
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
