#!/usr/bin/env python3
"""Task 3B production-footprint qualification gate."""

from __future__ import annotations

import math
import re
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
KLOR = HERE.parents[2]

CONTRACT = ERGOGEN / "task3/task3b-footprints.yaml"
TASK3A = ERGOGEN / "task3/task3a-electrical-contract.yaml"
TASK2D = ERGOGEN / "task2/task2d-freeze.yaml"
STOCK_PRETTY = KLOR / "klor1.4/PCB/klor1_4/KLOR.pretty"
STOCK_PCB = KLOR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"

TOL = 1e-6

MODULE_FILES = [
    "klor_key.js",
    "klor_diode.js",
    "helios_host.js",
    "klor_trrs.js",
    "klor_ec11.js",
    "klor_reset.js",
    "pmw_header.js",
    "mounting_hole.js",
]


def balanced_blocks(text: str, token: str) -> list[str]:
    out = []
    needle = "(" + token
    pos = 0
    while True:
        start = text.find(needle, pos)
        if start < 0:
            return out
        depth = 0
        quoted = False
        escaped = False
        end = None
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
                    end = i + 1
                    break
        if end is None:
            raise AssertionError(f"unbalanced {token} block")
        out.append(text[start:end])
        pos = end


def fp_blocks(text: str) -> list[str]:
    return balanced_blocks(text, "footprint") + balanced_blocks(text, "module")


def footprint_name(block: str) -> str:
    m = re.match(r'\((?:footprint|module)\s+"?([^"\s\)]+)"?', block)
    if not m:
        raise AssertionError("footprint/module name missing")
    return m.group(1)


def at_xy(block: str):
    m = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)", block)
    return (float(m.group(1)), float(m.group(2))) if m else None


def pad_info(block: str):
    head = re.match(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))\s+(\S+)\s+(\S+)', block)
    if not head:
        raise AssertionError(f"bad pad block: {block[:120]}")
    number = head.group(1) if head.group(1) is not None else head.group(2)
    typ, shape = head.group(3), head.group(4)

    at = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)", block)
    size = re.search(r"\(size\s+([-\d.]+)\s+([-\d.]+)\)", block)
    drill = re.search(r"\(drill(?:\s+oval)?\s+([-\d.]+)(?:\s+([-\d.]+))?\)", block)
    layers = re.search(r"\(layers\s+([^\)]+)\)", block)
    net = re.search(r'\(net\s+\d+\s+"([^"]*)"\)', block)

    return {
        "number": number,
        "type": typ,
        "shape": shape,
        "at": (float(at.group(1)), float(at.group(2))) if at else (0.0, 0.0),
        "size": (float(size.group(1)), float(size.group(2))) if size else None,
        "drill": (
            (float(drill.group(1)), float(drill.group(2) or drill.group(1)))
            if drill else None
        ),
        "layers": tuple(x.strip('"') for x in layers.group(1).split()) if layers else (),
        "net": net.group(1) if net else "",
    }


def pads(block: str):
    return [pad_info(x) for x in balanced_blocks(block, "pad")]


def assert_pair(name, actual, expected, tol=TOL):
    if len(actual) != len(expected) or any(abs(a-e) > tol for a, e in zip(actual, expected)):
        raise AssertionError(f"{name}: {actual} != {expected}")


def find_instance(all_fps, name, x):
    matches = [fp for fp in all_fps if footprint_name(fp) == name and at_xy(fp) and abs(at_xy(fp)[0] - x) < TOL]
    if len(matches) != 1:
        raise AssertionError(f"{name}@{x}: expected 1 instance, got {len(matches)}")
    return matches[0]


def source_footprint(path: Path):
    fs = fp_blocks(path.read_text(encoding="utf-8"))
    if len(fs) != 1:
        raise AssertionError(f"{path}: expected one footprint, got {len(fs)}")
    return fs[0]


def select_pad(plist, number, layer=None):
    found = [p for p in plist if p["number"] == str(number)]
    if layer:
        found = [p for p in found if layer in p["layers"]]
    if len(found) != 1:
        raise AssertionError(f"pad {number} layer={layer}: got {len(found)}")
    return found[0]


def compare_pad_geometry(name, actual, expected):
    assert_pair(name + ".at", actual["at"], expected["at"])
    assert_pair(name + ".size", actual["size"], expected["size"])


def parse_stock_positions(text: str):
    result = {}
    for fp in balanced_blocks(text, "footprint"):
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', fp)
        at = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", fp)
        if ref and at:
            result[ref.group(1)] = (float(at.group(1)), float(at.group(2)), float(at.group(3) or 0))
    return result


def bbox_gap_to_square(lo, hi, center, half):
    b_lo = (center[0]-half, center[1]-half)
    b_hi = (center[0]+half, center[1]+half)
    dx = max(lo[0]-b_hi[0], b_lo[0]-hi[0], 0.0)
    dy = max(lo[1]-b_hi[1], b_lo[1]-hi[1], 0.0)
    return math.hypot(dx, dy)


def main():
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    task3a = yaml.safe_load(TASK3A.read_text(encoding="utf-8"))
    task2d = yaml.safe_load(TASK2D.read_text(encoding="utf-8"))

    if contract["status"] not in {"task3b_candidate", "task3b_qualified"}:
        raise AssertionError("unexpected Task-3B status")
    if task3a["status"] != "task3a_frozen":
        raise AssertionError("Task 3A must be frozen")
    if not str(task2d["status"]).startswith("task2d_frozen"):
        raise AssertionError("Task 2D must remain frozen")

    for name in MODULE_FILES:
        path = ERGOGEN / "footprints" / name
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing local production footprint module: {path}")
    print("PASS eight local production footprint modules exist")

    generated = Path(__import__("sys").argv[1]) if len(__import__("sys").argv) > 1 else None
    if generated is None:
        raise AssertionError("usage: validate_task3b.py GENERATED_DIR")
    pcb_path = generated / "pcbs/task3b_footprint_fixture.kicad_pcb"
    if not pcb_path.is_file():
        raise AssertionError(f"missing qualification fixture: {pcb_path}")
    all_fps = fp_blocks(pcb_path.read_text(encoding="utf-8"))

    fixture = contract["fixture"]["instances"]

    # MX hotswap + SK6812 source audit, both selectable sides.
    key_src = pads(source_footprint(STOCK_PRETTY / "SK6812MINI_and_cherry.kicad_mod"))
    expected_nets = {1:"RGB_OUT", 2:"GND", 3:"RGB_IN", 4:"RAW_5V", 5:"COL_TEST", 6:"KEY_TO_DIODE"}
    for side, key in (("B","key_B"),("F","key_F")):
        fp = find_instance(all_fps, "KLOR_MX_HOTSWAP_SK6812MINI_E", fixture[key][0])
        gp = pads(fp)
        for n in range(1, 7):
            actual = select_pad(gp, n, side + ".Cu")
            source = select_pad(key_src, n, side + ".Cu")
            compare_pad_geometry(f"key_{side}.pad{n}", actual, source)
            if actual["net"] != expected_nets[n]:
                raise AssertionError(f"key_{side}.pad{n} net {actual['net']} != {expected_nets[n]}")
        npth_actual = [
            p for p in gp if p["number"] == "" and p["type"] == "np_thru_hole"
        ]
        npth_source = [
            p for p in key_src if p["number"] == "" and p["type"] == "np_thru_hole"
        ]
        if len(npth_actual) != 5:
            raise AssertionError(f"key_{side}: expected 5 selected-side NPTHs")
        for actual_hole in npth_actual:
            matches = [
                source_hole for source_hole in npth_source
                if math.dist(actual_hole["at"], source_hole["at"]) <= 2e-6
                and actual_hole["drill"] == source_hole["drill"]
            ]
            if not matches:
                raise AssertionError(
                    f"key_{side}: NPTH {actual_hole['at']} / {actual_hole['drill']} "
                    "is not source-derived"
                )
        if "(fp_rect (start -1.75 3.25) (end 1.75 7.75) (layer Edge.Cuts)" not in fp:
            raise AssertionError("reverse-mount LED cutout changed")
    print("PASS non-reversible MX hotswap + SK6812 geometry derives from stock KLOR")

    # SOD-123: same source centers/sizes, ordinary single-side SMD lands.
    diode_src = pads(source_footprint(STOCK_PRETTY / "Diode_SOD123.kicad_mod"))
    for side, key in (("B","diode_B"),("F","diode_F")):
        fp = find_instance(all_fps, "KLOR_D_SOD123", fixture[key][0])
        gp = pads(fp)
        for n, net in ((1,"ROW_TEST"),(2,"KEY_TO_DIODE")):
            actual = select_pad(gp, n, side + ".Cu")
            source = select_pad(diode_src, n)
            compare_pad_geometry(f"diode_{side}.pad{n}", actual, source)
            if actual["type"] != "smd" or actual["drill"] is not None:
                raise AssertionError("production SOD-123 lands must be drill-free SMD")
            if actual["net"] != net:
                raise AssertionError(f"diode_{side}.pad{n}: wrong net")
    print("PASS SOD-123 production land geometry qualified")

    # Helios host: standard KLOR ProMicro grid + Helios pad 32.
    helios = find_instance(all_fps, "KLOR_HELIOS_REV1_HOST", fixture["helios"][0])
    hp = pads(helios)
    hp_nums = {int(p["number"]) for p in hp if p["number"]}
    expected_nums = set(range(2,14)) | set(range(19,31)) | {32}
    if hp_nums != expected_nums:
        raise AssertionError(f"Helios hosted pads changed: {sorted(hp_nums)}")

    promicro_src = pads(source_footprint(STOCK_PRETTY / "ProMicro.kicad_mod"))
    for old in range(1,13):
        src = select_pad(promicro_src, old, "F.SilkS")
        actual = select_pad(hp, old+1)
        assert_pair(f"Helios left pad {old+1}", actual["at"], src["at"])
    for old in range(13,25):
        src = select_pad(promicro_src, old, "F.SilkS")
        actual = select_pad(hp, old+6)
        assert_pair(f"Helios right pad {old+6}", actual["at"], src["at"])
    p32 = select_pad(hp, 32)
    assert_pair("Helios pad32.at", p32["at"], tuple(contract["footprints"]["controller"]["extra_required_contact"]["host_local"]))
    assert_pair("Helios pad32.size", p32["size"], (1.7,1.7))
    assert_pair("Helios pad32.drill", p32["drill"], (1.0,1.0))
    if p32["net"] != "RGB_DATA_5V":
        raise AssertionError("Helios pad32 must own level-shifted RGB data")

    # Source-derived body-envelope clearance at frozen U1 position.
    pos = parse_stock_positions(STOCK_PCB.read_text(encoding="utf-8"))
    u1 = pos["U1"]
    env = contract["footprints"]["controller"]["body_envelope_at_host_origin"]
    lo = (u1[0]+env["min"][0], u1[1]+env["min"][1])
    hi = (u1[0]+env["max"][0], u1[1]+env["max"][1])
    retained_keys = [*(f"SW{i}" for i in range(1,18)), "SW20", "SW21", "SW22"]
    gaps = [(bbox_gap_to_square(lo, hi, pos[r], 9.0), r) for r in retained_keys]
    gap, ref = min(gaps)
    if ref != "SW6" or gap < 6.45:
        raise AssertionError(f"Helios frozen-U1 key clearance regressed: {ref} {gap}")
    print(f"PASS Helios host grid + pad32 + frozen-U1 key clearance ({gap:.3f} mm)")

    # TRRS side-selectable source subsets.
    trrs_src = pads(source_footprint(STOCK_PRETTY / "MJ-4PP-9.kicad_mod"))
    trrs_nets = {1:"RAW_5V",2:"GND",3:"",4:"SPLIT_DATA"}
    for side,key in (("F","trrs_F"),("B","trrs_B")):
        fp=find_instance(all_fps,"KLOR_MJ_4PP_9",fixture[key][0])
        gp=pads(fp)
        for n in range(1,5):
            actual=select_pad(gp,n)
            source=select_pad(trrs_src,n,side+".SilkS")
            compare_pad_geometry(f"trrs_{side}.pad{n}",actual,source)
            if actual["net"] != trrs_nets[n]:
                raise AssertionError(f"TRRS {side} pin {n} net changed")
    print("PASS MJ-4PP-9 one-side-at-a-time variants derive from stock footprint")

    # EC11 must be source-identical electrically/mechanically.
    enc_src=pads(source_footprint(STOCK_PRETTY / "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm-keebio_modified.kicad_mod"))
    enc=find_instance(all_fps,"KLOR_EC11E",fixture["encoder"][0])
    enc_p=pads(enc)
    for n in ("A","B","C","S1","S2"):
        compare_pad_geometry("EC11."+n,select_pad(enc_p,n),select_pad(enc_src,n))
    for n in ("A","B","C","S1","S2"):
        if select_pad(enc_p,n)["drill"] != select_pad(enc_src,n)["drill"]:
            raise AssertionError(f"EC11 drill changed for {n}")
    print("PASS EC11 retained source geometry qualified")

    # Reset: same source centers/sizes, single-side SMD, no reversible drills.
    rst_src=pads(source_footprint(STOCK_PRETTY / "SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010_both_sides.kicad_mod"))
    for side,key in (("F","reset_F"),("B","reset_B")):
        fp=find_instance(all_fps,"KLOR_SKRTLAE010_RESET",fixture[key][0])
        gp=pads(fp)
        for n in ("1","2","MP"):
            actual=[p for p in gp if p["number"]==n]
            source=[p for p in rst_src if p["number"]==n]
            if sorted((p["at"],p["size"]) for p in actual) != sorted((p["at"],p["size"]) for p in source):
                raise AssertionError(f"reset {side} {n}: source geometry changed")
            if any(p["type"]!="smd" or p["drill"] is not None for p in actual):
                raise AssertionError("reset production lands must be ordinary SMD")
    print("PASS reset footprint de-reversibilized without changing land geometry")

    # PMW header is frozen Task-2D mechanical/electrical contract.
    pmw=find_instance(all_fps,"KLOR_PMW_1X07_P2_54",fixture["pmw_header"][0])
    pp=pads(pmw)
    pin_order={int(k):v for k,v in contract["footprints"]["pmw_header"]["pin_order"].items()}
    ys=contract["footprints"]["pmw_header"]["local_pin_y"]
    for n in range(1,8):
        p=select_pad(pp,n)
        assert_pair(f"PMW pin{n}.at",p["at"],(0.0,float(ys[n-1])))
        if n==5:
            if p["net"]!="":
                raise AssertionError("PMW MOTION position must remain NC")
        elif p["net"]!=pin_order[n]:
            raise AssertionError(f"PMW pin {n} net changed: {p['net']}")
    print("PASS frozen PMW 1x7 physical/electrical footprint contract")

    # Stock mounting holes.
    m3=find_instance(all_fps,"KLOR_MOUNTING_HOLE",fixture["m3"][0])
    m2=find_instance(all_fps,"KLOR_MOUNTING_HOLE",fixture["m2"][0])
    if select_pad(pads(m3),"")["drill"] != (3.2,3.2):
        raise AssertionError("M3 drill changed")
    if select_pad(pads(m2),"")["drill"] != (2.2,2.2):
        raise AssertionError("M2 drill changed")
    print("PASS stock 3.2 mm M3 and 2.2 mm M2 mounting holes qualified")

    if contract["policy"]["routing"] != "forbidden_until_task4":
        raise AssertionError("Task 3B accidentally claimed routing")
    if not contract["task3c_handoff"]["left_board_must_not_use_builtin_generic_production_footprints"]:
        raise AssertionError("Task 3C must consume local qualified footprint modules")

    print("Task 3B production-footprint qualification passed")


if __name__ == "__main__":
    main()
