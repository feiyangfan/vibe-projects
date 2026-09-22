#!/usr/bin/env python3
"""Task 3F preservation audit for the routed Konrad trackball derivative."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
STOCK_PCB = ROOT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb"
DERIV_PCB = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_pcb"
DERIV_SCH = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_sch"
REL_PCB = "klor-trackball/PCB/konrad_trackball/konrad_trackball.kicad_pcb"

STOCK_PCB_BLOB = "3dea93bc4266541e9ca85eebc70e4b8c851afc11"
TASK3B_SCH_BLOB = "4239dd2f139be30e24ee7109800a5ae9f179aee3"
TASK3D_COMMIT = "57eca64b31ed46b43c3112a20a4270e6bc127206"
TASK3D_PCB_BLOB = "4272f9c3895fd46c0688b3eb530fc7299b540727"
TASK3E_PCB_BLOB = "cdc63c3081881861bdcba8f0c6bc03a5b242baed"

PMW_NETS = {82:"PMW_CS",83:"PMW_MISO",84:"PMW_MOSI",85:"PMW_SCK"}
STRUCTURAL = {f"MH{i}" for i in range(1,10)}
PROTECTED = STRUCTURAL | {"SW18","U1","J1"}


def git_blob(path: Path) -> str:
    return subprocess.run(
        ["git","hash-object",str(path)],cwd=REPO,check=True,
        text=True,capture_output=True,
    ).stdout.strip()


def git_show(commit: str, path: str) -> str:
    return subprocess.run(
        ["git","show",f"{commit}:{path}"],cwd=REPO,check=True,
        text=True,capture_output=True,
    ).stdout


def balanced(text: str, start: int) -> tuple[str,int]:
    depth=0; quoted=False; escaped=False
    for i in range(start,len(text)):
        ch=text[i]
        if quoted:
            if escaped: escaped=False
            elif ch=="\\": escaped=True
            elif ch=='"': quoted=False
            continue
        if ch=='"': quoted=True
        elif ch=="(": depth+=1
        elif ch==")":
            depth-=1
            if depth==0: return text[start:i+1],i+1
    raise ValueError("unbalanced KiCad expression")


def blocks(text: str, token: str) -> list[str]:
    out=[]; pos=0; needle="("+token
    while True:
        pos=text.find(needle,pos)
        if pos<0: return out
        b,end=balanced(text,pos); out.append(b); pos=end


def ref(block: str) -> str | None:
    m=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',block)
    if not m:
        m=re.search(r'\(fp_text\s+reference\s+"([^"]+)"',block)
    return None if not m else m.group(1)


def footprint_map(text: str) -> dict[str,str]:
    return {r:b for b in blocks(text,"footprint") if (r:=ref(b))}


def top_at(block: str) -> tuple[float,float,float]:
    m=re.search(r'^\(footprint\s+"[^"]+"[\s\S]*?\n\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)',block)
    if not m: raise ValueError(f"footprint at missing: {ref(block)}")
    return float(m.group(1)),float(m.group(2)),float(m.group(3) or 0.0)


def top_layer(block: str) -> str:
    m=re.search(r'^\(footprint\s+"[^"]+"[\s\S]*?\n\s*\(layer\s+"([^"]+)"\)',block)
    if not m: raise ValueError(f"footprint layer missing: {ref(block)}")
    return m.group(1)


def footprint_name(block: str) -> str:
    m=re.match(r'^\(footprint\s+"([^"]+)"',block)
    return "" if not m else m.group(1)


def edge_blocks(text: str) -> list[str]:
    out=[]
    for kind in ("gr_line","gr_curve","gr_rect","gr_circle","gr_poly","gr_arc"):
        out.extend(b for b in blocks(text,kind) if '(layer "Edge.Cuts")' in b)
    return sorted(out)


def net_defs(text: str) -> dict[int,str]:
    return {int(n):name for n,name in re.findall(r'^\s*\(net\s+(\d+)\s+"([^"]*)"\)$',text,re.M)}


def pad_blocks(fp: str) -> list[str]:
    return blocks(fp,"pad")


def pads_by_number(fp: str) -> dict[str,list[str]]:
    out={}
    for p in pad_blocks(fp):
        m=re.match(r'^\(pad\s+"([^"]*)"',p)
        if m: out.setdefault(m.group(1),[]).append(p)
    return out


def pad_net(pad: str):
    m=re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)',pad)
    return None if not m else (int(m.group(1)),m.group(2))


def parse_segments(text: str):
    out=[]
    for b in blocks(text,"segment"):
        a=re.search(r'\(start\s+([-\d.]+)\s+([-\d.]+)\)',b)
        z=re.search(r'\(end\s+([-\d.]+)\s+([-\d.]+)\)',b)
        n=re.search(r'\(net\s+(\d+)\)',b)
        if a and z and n:
            out.append(((float(a.group(1)),float(a.group(2))),
                        (float(z.group(1)),float(z.group(2))),int(n.group(1))))
    return out


def parse_vias(text: str):
    out=[]
    for b in blocks(text,"via"):
        a=re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\)',b)
        n=re.search(r'\(net\s+(\d+)\)',b)
        if a and n: out.append(((float(a.group(1)),float(a.group(2))),int(n.group(1))))
    return out


def segment_hits_open_rect(a,b,r):
    xl,yt,xr,yb=r
    inside=lambda p: xl<p[0]<xr and yt<p[1]<yb
    if inside(a) or inside(b): return True
    def orient(p,q,rp): return (q[0]-p[0])*(rp[1]-p[1])-(q[1]-p[1])*(rp[0]-p[0])
    def hit(p,q,u,v): return orient(p,q,u)*orient(p,q,v)<0 and orient(u,v,p)*orient(u,v,q)<0
    edges=[((xl,yt),(xr,yt)),((xr,yt),(xr,yb)),((xr,yb),(xl,yb)),((xl,yb),(xl,yt))]
    return any(hit(a,b,u,v) for u,v in edges)


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--json-output",type=Path); args=ap.parse_args()
    stock=STOCK_PCB.read_text(encoding="utf-8")
    cur=DERIV_PCB.read_text(encoding="utf-8")
    task3d=git_show(TASK3D_COMMIT,REL_PCB)

    sfp,cfp=footprint_map(stock),footprint_map(cur)
    stock_refs=set(sfp); cur_refs=set(cfp)
    retained=stock_refs-{"SW22","D22"}

    placement_checks={}
    for r in sorted(retained):
        placement_checks[r]=(
            r in cfp and
            top_at(sfp[r])==top_at(cfp[r]) and
            top_layer(sfp[r])==top_layer(cfp[r]) and
            footprint_name(sfp[r])==footprint_name(cfp[r])
        )

    switch_refs={r for r in retained if r.startswith("SW")}
    structural_checks={r:placement_checks.get(r,False) for r in sorted(STRUCTURAL)}

    nets=net_defs(cur)
    j1=pads_by_number(cfp["J1"])
    u1=pads_by_number(cfp["U1"])
    j4=pads_by_number(cfp["J4"])

    expected_j4={
        "1":(82,"PMW_CS"),"2":(83,"PMW_MISO"),"3":(84,"PMW_MOSI"),
        "4":(85,"PMW_SCK"),"5":None,"6":(3,"VCC"),"7":(1,"GND"),
    }
    j4_ok=all(
        len(j4.get(pin,[]))==1 and pad_net(j4[pin][0])==expected
        for pin,expected in expected_j4.items()
    )
    u1_expected={"5":(85,"PMW_SCK"),"6":(84,"PMW_MOSI"),"7":(83,"PMW_MISO"),"12":(82,"PMW_CS")}
    u1_ok=all(
        len(u1.get(pin,[]))==2 and all(pad_net(p)==expected for p in u1[pin])
        for pin,expected in u1_expected.items()
    )
    j1_3_nc=len(j1.get("3",[]))==2 and all(pad_net(p) is None for p in j1["3"])
    j1_4_tx=len(j1.get("4",[]))==2 and all(pad_net(p)==(31,"TX") for p in j1["4"])

    slot=(142.111043,123.747997,144.111043,145.747997)
    segs=parse_segments(cur); vias=parse_vias(cur)
    slot_segments=[x for x in segs if segment_hits_open_rect(x[0],x[1],slot)]
    xl,yt,xr,yb=slot
    slot_vias=[x for x in vias if xl<x[0][0]<xr and yt<x[0][1]<yb]

    checks={
        "stock_pcb_blob_locked":git_blob(STOCK_PCB)==STOCK_PCB_BLOB,
        "task3e_pcb_blob_locked":git_blob(DERIV_PCB)==TASK3E_PCB_BLOB,
        "task3b_schematic_locked":git_blob(DERIV_SCH)==TASK3B_SCH_BLOB,
        "task3d_snapshot_blob_locked":subprocess.run(
            ["git","rev-parse",f"{TASK3D_COMMIT}:{REL_PCB}"],cwd=REPO,check=True,
            text=True,capture_output=True,
        ).stdout.strip()==TASK3D_PCB_BLOB,
        "zone_fill_cache_stripped":"(filled_polygon" not in cur,
        "footprint_reference_delta_exact":cur_refs==retained|{"J4"},
        "all_retained_stock_footprints_same_position_side_and_type":all(placement_checks.values()),
        "all_retained_switches_same_position_side_and_type":all(placement_checks[r] for r in switch_refs),
        "right_encoder_preserved":placement_checks["SW18"],
        "mcu_preserved":placement_checks["U1"],
        "trrs_preserved":placement_checks["J1"],
        "all_structural_mounts_preserved":all(structural_checks.values()),
        "task3d_edge_cuts_preserved_exact":edge_blocks(cur)==edge_blocks(task3d),
        "pmw_net_names_exact":all(nets.get(n)==name for n,name in PMW_NETS.items()),
        "legacy_rx_net_retired":"RX" not in nets.values(),
        "deleted_d22_local_net_retired":"Net-(D22-A)" not in nets.values(),
        "j4_pin_contract_and_motion_nc":j4_ok,
        "u1_pmw_ownership_exact":u1_ok,
        "j1_3_nc":j1_3_nc,
        "j1_4_tx_split_preserved":j1_4_tx,
        "matrix_col1_and_row3_distinct":nets.get(17)=="col1" and nets.get(38)=="row3" and 17!=38,
        "pass_through_has_no_tracks":not slot_segments,
        "pass_through_has_no_vias":not slot_vias,
    }

    result={
        "task":"3F-preservation",
        "status":"complete" if all(checks.values()) else "failed",
        "pcb_blob":git_blob(DERIV_PCB),
        "protected_footprints":sorted(PROTECTED),
        "structural_mounts":structural_checks,
        "retained_switch_count":len(switch_refs),
        "checks":checks,
    }
    rendered=json.dumps(result,indent=2,sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True,exist_ok=True)
        args.json_output.write_text(rendered+"\n",encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__=="__main__":
    raise SystemExit(main())
