#!/usr/bin/env python3
"""Mechanical reference audit for KLOR Konrad + Type-C trackball Task 1.

This script is intentionally read-only with respect to production CAD. It consumes
checked-in source geometry, solves the PCB->switchplate rigid XY transform from
physical MX openings, inspects the stock case/switchplate frame relationship, and
runs conservative clearance checks for the current Type-C placement.

The output is JSON so the exact evidence used to lock Task 1 can be retained.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

TASK1 = Path(__file__).resolve().parent
PROJECT = TASK1.parents[1]

PATHS = {
    "pcb": PROJECT / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb",
    "switchplate_stl": PROJECT / "klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl",
    "case_stl": PROJECT / "klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl",
    "housing_step": PROJECT / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c.stp",
    "housing_right_stl": PROJECT / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl",
    "housing_left_stl": PROJECT / "Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_left.stl",
    "breakout": PROJECT / "klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb",
}

EXPECTED = {
    "housing_step": "79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c",
    "housing_right_stl": "9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565",
    "housing_left_stl": "5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58",
}

BALL_PCB = np.array([162.323, -134.748], dtype=float)
SCREW_MID_PCB = np.array([156.111, -134.748], dtype=float)
BREAKOUT_PCB = np.array([143.111, -134.748], dtype=float)
DELETED_SWITCH_PCB = np.array([143.025, -128.770], dtype=float)
HOUSING_LOCAL_MOUNT_Z = -18.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mesh_info(path: Path) -> tuple[trimesh.Trimesh, dict]:
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.dump()))
    info = {
        "bounds": np.asarray(mesh.bounds).round(6).tolist(),
        "extents": np.asarray(mesh.extents).round(6).tolist(),
        "center": np.asarray(mesh.bounding_box.centroid).round(6).tolist(),
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
    }
    return mesh, info


def paren_blocks(text: str, keys=("(footprint", "(module")):
    starts = []
    for key in keys:
        pos = 0
        while True:
            i = text.find(key, pos)
            if i < 0:
                break
            starts.append(i)
            pos = i + len(key)
    for start in sorted(starts):
        depth = 0
        in_str = False
        esc = False
        for j in range(start, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    yield text[start:j+1]
                    break


def parse_footprints(text: str):
    out = []
    for b in paren_blocks(text):
        mname = re.match(r"\((?:footprint|module)\s+\"?([^\"\s\)]+)\"?", b)
        name = mname.group(1) if mname else ""
        mref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', b)
        if not mref:
            mref = re.search(r'\(fp_text\s+reference\s+"?([^\"\s\)]+)', b)
        ref = mref.group(1) if mref else ""
        mat = re.search(r"\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?", b)
        if not mat:
            continue
        x, y = float(mat.group(1)), float(mat.group(2))
        rot = float(mat.group(3) or 0.0)
        out.append({"ref": ref, "name": name, "x": x, "y": y, "rot": rot})
    return out


def classify_switches(fps):
    pts = []
    rows = []
    for f in fps:
        n = (f["name"] + " " + f["ref"]).lower()
        if "encoder" in n or "rotary" in n:
            continue
        switchish = (
            f["ref"].upper().startswith("SW")
            or "mx" in n
            or "hotswap" in n
            or "kailh" in n
            or "switch" in n
        )
        if switchish:
            pts.append([f["x"], f["y"]])
            rows.append(f)
    return np.asarray(pts, float), rows


def section_loops(mesh: trimesh.Trimesh):
    z = float(np.mean(mesh.bounds[:, 2]))
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return [], z
    planar, _ = sec.to_2D()
    loops = []
    for d in planar.discrete:
        a = np.asarray(d)[:, :2]
        if len(a) < 4:
            continue
        lo, hi = a.min(0), a.max(0)
        wh = hi - lo
        center = (lo + hi) / 2
        loops.append({"center": center, "wh": wh, "n": len(a)})
    return loops, z


def detect_mx_openings(mesh):
    loops, z = section_loops(mesh)
    cands = []
    for x in loops:
        w, h = x["wh"]
        # KLOR MX plate openings are approximately 14 mm square; allow tabs/tolerance.
        if 12.5 <= w <= 16.5 and 12.5 <= h <= 16.5 and abs(w-h) <= 2.0:
            cands.append(x["center"])
    # de-duplicate section contours that trace the same opening twice
    uniq = []
    for c in cands:
        if not uniq or min(np.linalg.norm(c-u) for u in uniq) > 0.5:
            uniq.append(c)
    return np.asarray(uniq, float), {"section_z": z, "raw_loops": len(loops), "mx_candidates": len(uniq)}


def transform_from_pair(p1, p2, q1, q2, reflect=False):
    u = p2 - p1
    v = q2 - q1
    if reflect:
        F = np.array([[-1.0, 0.0], [0.0, 1.0]])
        u0 = F @ u
    else:
        F = np.eye(2)
        u0 = u
    au = math.atan2(u0[1], u0[0])
    av = math.atan2(v[1], v[0])
    a = av - au
    C = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    R = C @ F
    t = q1 - R @ p1
    return R, t


def score_transform(src, dst, R, t, tol=0.35):
    moved = src @ R.T + t
    tree = cKDTree(dst)
    dist, idx = tree.query(moved, k=1)
    accepted = [(i, int(j), float(d)) for i,(j,d) in enumerate(zip(idx,dist)) if d <= tol]
    # enforce one-to-one matches by greedy distance
    accepted.sort(key=lambda x: x[2])
    used_s, used_d, keep = set(), set(), []
    for i,j,d in accepted:
        if i not in used_s and j not in used_d:
            used_s.add(i); used_d.add(j); keep.append((i,j,d))
    rms = math.sqrt(sum(d*d for _,_,d in keep)/len(keep)) if keep else 1e9
    return len(keep), rms, keep


def refine_rigid(src, dst, pairs, allow_reflection=True):
    P = np.asarray([src[i] for i,j,d in pairs])
    Q = np.asarray([dst[j] for i,j,d in pairs])
    pc, qc = P.mean(0), Q.mean(0)
    X, Y = P-pc, Q-qc
    U,S,Vt = np.linalg.svd(X.T @ Y)
    R = Vt.T @ U.T
    if not allow_reflection and np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    t = qc - R @ pc
    return R, t


def solve_pointset_transform(src, dst):
    if len(src) < 3 or len(dst) < 3:
        raise RuntimeError(f"insufficient points: src={len(src)} dst={len(dst)}")
    best = None
    # pair candidates restricted by invariant pair distance
    spairs = [(i,j,np.linalg.norm(src[j]-src[i])) for i in range(len(src)) for j in range(i+1,len(src))]
    dpairs = [(i,j,np.linalg.norm(dst[j]-dst[i])) for i in range(len(dst)) for j in range(i+1,len(dst))]
    for i,j,ds in spairs:
        if ds < 10:
            continue
        for a,b,dd in dpairs:
            if abs(ds-dd) > 0.20:
                continue
            for qa,qb in ((a,b),(b,a)):
                for reflect in (False, True):
                    R,t = transform_from_pair(src[i],src[j],dst[qa],dst[qb],reflect)
                    n,rms,pairs = score_transform(src,dst,R,t)
                    key = (n, -rms)
                    if best is None or key > best[0]:
                        best = (key,R,t,pairs)
    if best is None:
        raise RuntimeError("no PCB->plate transform candidate")
    _,R,t,pairs = best
    R2,t2 = refine_rigid(src,dst,pairs,allow_reflection=True)
    n,rms,pairs2 = score_transform(src,dst,R2,t2,tol=0.25)
    moved = src @ R2.T + t2
    return {
        "R": R2,
        "t": t2,
        "det": float(np.linalg.det(R2)),
        "matches": n,
        "rms_mm": rms,
        "pairs": pairs2,
        "moved": moved,
    }


def bbox_xy(mesh):
    b = np.asarray(mesh.bounds)
    return b[:, :2]


def nearest_footprints(fps, xy, needles):
    rows=[]
    for f in fps:
        n=(f["name"]+" "+f["ref"]).lower()
        if any(k in n for k in needles):
            d=float(np.linalg.norm(np.array([f["x"],f["y"]])-xy))
            rows.append((d,f))
    return [dict(distance_mm=round(d,3), **f) for d,f in sorted(rows,key=lambda x:x[0])[:8]]


def aabb_gap_2d(a_lo,a_hi,b_lo,b_hi):
    dx=max(a_lo[0]-b_hi[0], b_lo[0]-a_hi[0], 0.0)
    dy=max(a_lo[1]-b_hi[1], b_lo[1]-a_hi[1], 0.0)
    return math.hypot(dx,dy)


def main():
    report={"task":1,"status":"audit","errors":[]}
    for k,p in PATHS.items():
        if not p.exists(): report["errors"].append(f"missing {k}: {p}")
    report["hashes"]={}
    for k in ("housing_step","housing_right_stl","housing_left_stl"):
        actual=sha256(PATHS[k]) if PATHS[k].exists() else None
        report["hashes"][k]={"actual":actual,"expected":EXPECTED[k],"matches":actual==EXPECTED[k]}

    plate, plate_info=mesh_info(PATHS["switchplate_stl"])
    case, case_info=mesh_info(PATHS["case_stl"])
    housing, housing_info=mesh_info(PATHS["housing_right_stl"])
    report["meshes"]={"switchplate":plate_info,"case_right":case_info,"housing_right":housing_info}

    pcb_text=PATHS["pcb"].read_text(errors="ignore")
    fps=parse_footprints(pcb_text)
    sw_pts, sw_rows=classify_switches(fps)
    report["pcb"]={
        "footprints_parsed":len(fps),
        "switch_candidates":len(sw_pts),
        "encoder_candidates":nearest_footprints(fps,BALL_PCB,["encoder","rotary"]),
        "trrs_candidates":nearest_footprints(fps,BALL_PCB,["trrs","audiojack","jack"]),
        "mcu_candidates":nearest_footprints(fps,BALL_PCB,["promicro","pro_micro","rp2040","nice!nano","mcu"]),
    }

    plate_pts,detect_info=detect_mx_openings(plate)
    report["switchplate_detection"]=detect_info
    report["switchplate_detection"]["centers"] = np.round(plate_pts,4).tolist()

    sol=solve_pointset_transform(sw_pts,plate_pts)
    R,t=sol["R"],sol["t"]
    report["pcb_to_switchplate"]={
        "R":np.round(R,9).tolist(),"t":np.round(t,6).tolist(),"det":round(sol["det"],9),
        "matches":sol["matches"],"rms_mm":round(sol["rms_mm"],6),
    }

    # Common-export frame evidence for switchplate <-> stock case.
    pb=np.asarray(plate.bounds); cb=np.asarray(case.bounds)
    pxy=(pb[0,:2]+pb[1,:2])/2; cxy=(cb[0,:2]+cb[1,:2])/2
    report["switchplate_case_frame"]={
        "plate_xy_center":np.round(pxy,6).tolist(),"case_xy_center":np.round(cxy,6).tolist(),
        "center_delta_mm":np.round(cxy-pxy,6).tolist(),
        "plate_xy_extents":np.round(pb[1,:2]-pb[0,:2],6).tolist(),
        "case_xy_extents":np.round(cb[1,:2]-cb[0,:2],6).tolist(),
        "plate_z_bounds":np.round(pb[:,2],6).tolist(),"case_z_bounds":np.round(cb[:,2],6).tolist(),
    }

    # Candidate housing in plate coordinates. Prior audited orientation is PCB XY = ball + diag(-1,+1)*housing XY.
    M=np.array([[-1.0,0.0],[0.0,1.0]])
    A=R @ M
    ball_plate=R @ BALL_PCB + t
    plate_top=float(pb[1,2])
    z_shift=plate_top - HOUSING_LOCAL_MOUNT_Z
    H=np.eye(4); H[:2,:2]=A; H[:2,3]=ball_plate; H[2,3]=z_shift
    h2=housing.copy(); h2.apply_transform(H)
    hb=np.asarray(h2.bounds)
    report["housing_placement"]={
        "ball_center_plate_xy":np.round(ball_plate,6).tolist(),
        "mount_plane_plate_z":plate_top,
        "z_translation":round(z_shift,6),
        "transform_4x4":np.round(H,9).tolist(),
        "bounds_in_plate_frame":np.round(hb,6).tolist(),
    }

    # Identify mapped switch centers nearest the known deleted R34 center, then the next two closest to housing.
    mapped=sol["moved"]
    all_sw=[]
    for idx,p in enumerate(sw_pts):
        ddel=float(np.linalg.norm(p-DELETED_SWITCH_PCB))
        all_sw.append((ddel,idx,p,mapped[idx]))
    all_sw.sort(key=lambda x:x[0])
    report["deleted_switch_match"]={"pcb_xy":np.round(all_sw[0][2],4).tolist(),"distance_to_known_mm":round(all_sw[0][0],4)}

    # Conservative 18 mm square keycap prisms for nearest retained switches.
    # Find switches by 2D gap to housing XY AABB, excluding deleted switch.
    hlo,hhi=hb[0,:2],hb[1,:2]
    candidates=[]
    for ddel,idx,p,pp in all_sw:
        if ddel < 2.0:
            continue
        lo=pp-9.0; hi=pp+9.0
        gap=aabb_gap_2d(hlo,hhi,lo,hi)
        candidates.append((gap,idx,p,pp))
    candidates.sort(key=lambda x:x[0])
    report["nearest_retained_switches"]=[]
    for gap,idx,p,pp in candidates[:4]:
        report["nearest_retained_switches"].append({
            "pcb_xy":np.round(p,4).tolist(),"plate_xy":np.round(pp,4).tolist(),
            "conservative_18mm_keycap_xy_gap_mm":round(gap,4)
        })

    # Encoder/TRRS/MCU conservative distance checks in XY, reported from parsed footprint candidates.
    def add_gap(rows, half_xy):
        out=[]
        for row in rows:
            ppcb=np.array([row["x"],row["y"]]); pp=R@ppcb+t
            lo=pp-np.array(half_xy); hi=pp+np.array(half_xy)
            out.append({**row,"plate_xy":np.round(pp,4).tolist(),"housing_xy_gap_mm":round(aabb_gap_2d(hlo,hhi,lo,hi),4)})
        return out
    report["clearance_candidates"]={
        "encoder":add_gap(report["pcb"]["encoder_candidates"],(8.0,8.0)),
        "trrs":add_gap(report["pcb"]["trrs_candidates"],(7.0,4.0)),
        "mcu":add_gap(report["pcb"]["mcu_candidates"],(10.0,18.0)),
    }

    # Case relationship: housing may require local case relief; quantify current stock-shell overlap conservatively.
    # `contains` on meshes can fail for non-watertight exports, so evaluate AABB and nearest-point evidence only here.
    report["stock_case_overlap"]={
        "housing_vs_case_xy_aabb_gap_mm":round(aabb_gap_2d(hb[0,:2],hb[1,:2],cb[0,:2],cb[1,:2]),4),
        "housing_z_range":np.round(hb[:,2],4).tolist(),"case_z_range":np.round(cb[:,2],4).tolist(),
        "requires_exact_mesh_intersection_check":True,
    }

    # Gate evidence, intentionally strict. Exact mesh collision is required before lock.
    source_ok=all(v["matches"] for v in report["hashes"].values())
    transform_ok=sol["matches"] >= 18 and sol["rms_mm"] <= 0.15
    retained_gap=min([x[0] for x in candidates[:2]], default=-1)
    report["gate_evidence"]={
        "source_hashes_verified":source_ok,
        "pcb_switchplate_transform_verified":transform_ok,
        "pcb_switchplate_match_count":sol["matches"],
        "nearest_retained_keycap_xy_gap_mm":round(retained_gap,4),
        "case_frame_needs_exact_validation":True,
        "placement_locked":False,
    }

    print(json.dumps(report,indent=2))
    return 0 if not report["errors"] and source_ok and transform_ok else 2

if __name__=="__main__":
    sys.exit(main())
