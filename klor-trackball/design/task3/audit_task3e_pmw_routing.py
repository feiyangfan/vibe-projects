#!/usr/bin/env python3
"""Audit Task 3E PMW3360 routing against the frozen Task 3D PCB."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
PCB = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_pcb"
SCH = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_sch"
REL_PCB = "klor-trackball/PCB/konrad_trackball/konrad_trackball.kicad_pcb"

BASE_COMMIT = "57eca64b31ed46b43c3112a20a4270e6bc127206"
BASE_PCB_BLOB = "4272f9c3895fd46c0688b3eb530fc7299b540727"
RESULT_PCB_BLOB = "cdc63c3081881861bdcba8f0c6bc03a5b242baed"
SCHEMATIC_BLOB = "4239dd2f139be30e24ee7109800a5ae9f179aee3"

PMW = {
    82: ("PMW_CS",   (105.318815,85.975745), (147.724665,142.367997), 44, 11, 167.1343042958396),
    83: ("PMW_MISO", (105.318815,73.275745), (147.724665,139.827997), 27,  2,  98.4559336198129),
    84: ("PMW_MOSI", (105.318815,70.735745), (147.724665,137.287997), 37,  4, 126.1123778795571),
    85: ("PMW_SCK",  (105.318815,68.195745), (147.724665,134.747997), 30, 10, 120.2791144175412),
}
POWER = {
    3: ("VCC", (147.724665,129.667997), (145.840675,127.985612), 1, 0, 2.5258340421186),
    1: ("GND", (147.724665,127.127997), (149.555000,117.370000), 5, 0, 10.6791938318832),
}

def git_blob(path: Path) -> str:
    return subprocess.run(["git","hash-object",str(path)],cwd=REPO,check=True,text=True,capture_output=True).stdout.strip()

def git_show(commit: str, path: str) -> str:
    return subprocess.run(["git","show",f"{commit}:{path}"],cwd=REPO,check=True,text=True,capture_output=True).stdout

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
        block,end=balanced(text,pos); out.append(block); pos=end

def uid(block: str):
    m=re.search(r'\(uuid\s+"([^"]+)"\)',block)
    return None if not m else m.group(1)

def point(block: str, atom: str):
    m=re.search(rf'\({atom}\s+([-\d.]+)\s+([-\d.]+)\)',block)
    return None if not m else (float(m.group(1)),float(m.group(2)))

def top_at(block: str):
    m=re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)',block)
    return None if not m else (float(m.group(1)),float(m.group(2)),float(m.group(3) or 0.0))

def ref(block: str):
    m=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',block)
    if not m: m=re.search(r'\(fp_text\s+reference\s+"([^"]+)"',block)
    return None if not m else m.group(1)

def footprints(text: str):
    return {r:b for b in blocks(text,"footprint") if (r:=ref(b))}

def net_of(block: str):
    m=re.search(r'\(net\s+(\d+)(?:\s+"([^"]*)")?\)',block)
    return None if not m else (int(m.group(1)),m.group(2))

def parse_segments(text: str):
    out={}
    for b in blocks(text,"segment"):
        u=uid(b); a,z=point(b,"start"),point(b,"end")
        w=re.search(r'\(width\s+([-\d.]+)\)',b)
        layer=re.search(r'\(layer\s+"([^"]+)"\)',b)
        net=net_of(b)
        if u and a and z and w and layer and net:
            out[u]={"a":a,"b":z,"width":float(w.group(1)),"layer":layer.group(1),"net":net[0],"text":b}
    return out

def parse_vias(text: str):
    out={}
    for b in blocks(text,"via"):
        u=uid(b); at=top_at(b)
        size=re.search(r'\(size\s+([-\d.]+)\)',b)
        drill=re.search(r'\(drill\s+([-\d.]+)\)',b)
        net=net_of(b)
        if u and at and size and drill and net:
            out[u]={"p":(at[0],at[1]),"size":float(size.group(1)),"drill":float(drill.group(1)),"net":net[0],"text":b}
    return out

def nets(text: str):
    return {int(n):name for n,name in re.findall(r'^\s*\(net\s+(\d+)\s+"([^"]+)"\)',text,re.M)}

def close(a,b,eps=1e-6):
    return math.dist(a,b)<=eps

def key(p):
    return (round(p[0],6),round(p[1],6))

def connected(segments,vias,net,start,end):
    graph=defaultdict(set)
    def node(p,layer): return (key(p),layer)
    for s in segments.values():
        if s["net"]!=net: continue
        a,b=node(s["a"],s["layer"]),node(s["b"],s["layer"])
        graph[a].add(b); graph[b].add(a)
    for v in vias.values():
        if v["net"]!=net: continue
        a,b=node(v["p"],"F.Cu"),node(v["p"],"B.Cu")
        graph[a].add(b); graph[b].add(a)
    for p in (start,end):
        a,b=node(p,"F.Cu"),node(p,"B.Cu")
        graph[a].add(b); graph[b].add(a)
    q=deque([node(start,"F.Cu"),node(start,"B.Cu")]); seen=set(q)
    goals={node(end,"F.Cu"),node(end,"B.Cu")}
    while q:
        u=q.popleft()
        if u in goals: return True
        for v in graph[u]:
            if v not in seen: seen.add(v); q.append(v)
    return False

def pad_contract(fp,expected):
    rows=defaultdict(list)
    for p in blocks(fp,"pad"):
        m=re.match(r'\(pad\s+"([^"]+)"',p)
        if m: rows[m.group(1)].append(net_of(p))
    return all(len(rows[n])>=1 and all(v==want for v in rows[n]) for n,want in expected.items())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--json-output",type=Path); args=ap.parse_args()
    current=PCB.read_text(encoding="utf-8"); base=git_show(BASE_COMMIT,REL_PCB)
    bseg,cseg=parse_segments(base),parse_segments(current)
    bvia,cvia=parse_vias(base),parse_vias(current)
    bfp,cfp=footprints(base),footprints(current)
    bn,cn=nets(base),nets(current)
    new_seg={u:s for u,s in cseg.items() if u not in bseg}
    new_via={u:v for u,v in cvia.items() if u not in bvia}

    route_stats={}
    for net,(name,start,end,expect_s,expect_v,expect_len) in {**PMW,**POWER}.items():
        ss=[s for s in new_seg.values() if s["net"]==net]
        vv=[v for v in new_via.values() if v["net"]==net]
        length=sum(math.dist(s["a"],s["b"]) for s in ss)
        route_stats[name]={"net_id":net,"segments":len(ss),"vias":len(vv),"length_mm":length,"connected":connected(cseg,cvia,net,start,end)}

    j4_expected={"1":(82,"PMW_CS"),"2":(83,"PMW_MISO"),"3":(84,"PMW_MOSI"),"4":(85,"PMW_SCK"),"5":None,"6":(3,"VCC"),"7":(1,"GND")}
    u1_expected={"5":(85,"PMW_SCK"),"6":(84,"PMW_MOSI"),"7":(83,"PMW_MISO"),"12":(82,"PMW_CS")}

    slot=(142.111043,123.747997,144.111043,145.747997); xl,yt,xr,yb=slot
    def in_slot(p): return xl<p[0]<xr and yt<p[1]<yb
    def orient(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def hit(a,b,c,d): return orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0
    edges=[((xl,yt),(xr,yt)),((xr,yt),(xr,yb)),((xr,yb),(xl,yb)),((xl,yb),(xl,yt))]
    slot_segments=[u for u,s in new_seg.items() if in_slot(s["a"]) or in_slot(s["b"]) or any(hit(s["a"],s["b"],a,b) for a,b in edges)]
    slot_vias=[u for u,v in new_via.items() if in_slot(v["p"])]

    edge_current=[b for k in ("gr_line","gr_curve","gr_rect") for b in blocks(current,k) if '(layer "Edge.Cuts")' in b]
    edge_base=[b for k in ("gr_line","gr_curve","gr_rect") for b in blocks(base,k) if '(layer "Edge.Cuts")' in b]

    checks={
        "task3d_base_pcb_blob_locked": subprocess.run(["git","rev-parse",f"{BASE_COMMIT}:{REL_PCB}"],cwd=REPO,check=True,text=True,capture_output=True).stdout.strip()==BASE_PCB_BLOB,
        "task3e_pcb_blob_locked": git_blob(PCB)==RESULT_PCB_BLOB,
        "task3b_schematic_preserved": git_blob(SCH)==SCHEMATIC_BLOB,
        "zone_fill_cache_stripped":"(filled_polygon" not in current,
        "net_table_unchanged":cn==bn,
        "pmw_semantic_net_names_exact":all(cn.get(n)==spec[0] for n,spec in PMW.items()),
        "footprints_exactly_preserved":cfp==bfp,
        "edge_cuts_exactly_preserved":edge_current==edge_base,
        "zones_exactly_preserved":blocks(current,"zone")==blocks(base,"zone"),
        "all_base_segments_exactly_preserved":set(bseg).issubset(cseg) and all(cseg[u]["text"]==bseg[u]["text"] for u in bseg),
        "all_base_vias_exactly_preserved":set(bvia).issubset(cvia) and all(cvia[u]["text"]==bvia[u]["text"] for u in bvia),
        "new_copper_only_authorized_nets":({s["net"] for s in new_seg.values()}|{v["net"] for v in new_via.values()})=={1,3,82,83,84,85},
        "j4_pin_contract_and_motion_nc":pad_contract(cfp["J4"],j4_expected),
        "u1_pmw_pad_contract_preserved":pad_contract(cfp["U1"],u1_expected),
        "pass_through_remains_track_free":not slot_segments,
        "pass_through_remains_via_free":not slot_vias,
    }
    for net,(name,start,end,es,ev,el) in {**PMW,**POWER}.items():
        rs=route_stats[name]
        checks[f"{name.lower()}_route_connected"]=rs["connected"]
        checks[f"{name.lower()}_route_count_exact"]=rs["segments"]==es and rs["vias"]==ev
        checks[f"{name.lower()}_route_length_exact"]=abs(rs["length_mm"]-el)<1e-6
    checks["all_four_pmw_signals_routed"]=all(route_stats[PMW[n][0]]["connected"] for n in PMW)
    checks["vcc_and_gnd_routed"]=all(route_stats[POWER[n][0]]["connected"] for n in POWER)
    motion=(147.724665,132.207997)
    checks["motion_has_no_route"]=all(not close(s["a"],motion) and not close(s["b"],motion) for s in new_seg.values())

    result={"task":"3E","status":"complete" if all(checks.values()) else "failed","pcb_blob":git_blob(PCB),"new_segments":len(new_seg),"new_vias":len(new_via),"routes":route_stats,"motion":"J4.5 NC","full_kicad_drc":"deferred-to-task-3F","checks":checks}
    rendered=json.dumps(result,indent=2,sort_keys=True); print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True,exist_ok=True); args.json_output.write_text(rendered+"\n",encoding="utf-8")
    return 0 if all(checks.values()) else 2

if __name__=="__main__":
    raise SystemExit(main())
