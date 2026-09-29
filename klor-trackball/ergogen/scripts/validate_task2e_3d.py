#!/usr/bin/env python3
"""Task 2E: establish a common 3D frame for the KLOR right-side assembly.

Phase 1 solves the stock Konrad switchplate STL -> Ergogen canonical XY transform
from the actual MX switch apertures.  The same source-CAD XY transform is then
applied to the stock right-case STL.  The script emits an audit report and
aligned meshes; later Task-2E stages consume this transform for relief cutting
and collision checks.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import trimesh
import yaml
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "ergogen" / "config.yaml"
PLATE = ROOT / "klor1.4" / "case" / "3DP" / "konrad" / "switchplate" / "KLOR_konrad_3DP_switchplate.stl"
CASE = ROOT / "klor1.4" / "case" / "3DP" / "konrad" / "regular" / "KLOR_konrad_case_R.stl"
HOUSING = ROOT / "Keyball 25mm Trackball Case Type C - 6719828" / "files" / "keyball_trackball_case_25mm_type_c_right.stl"

EXPECTED_SWITCHES = [
    "sw1","sw2","sw3","sw4","sw5",
    "sw6","sw7","sw8","sw9","sw10","sw11",
    "sw12","sw13","sw14","sw15","sw16","sw17",
    "sw20","sw21","sw22",
]


def load_mesh(path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"{path}: expected Trimesh, got {type(mesh)}")
    return mesh


def canonical_switch_centers(config: dict) -> np.ndarray:
    pts = []
    points = config["points"]["zones"]["source"]["key"]["anchors"]
    # The checked-in config uses explicit named points rather than a zone anchor
    # table at this location in some Ergogen versions. Fall back to recursive
    # named-point extraction below.
    raise RuntimeError("unreachable")


def named_points(config: dict) -> dict[str, tuple[float,float,float]]:
    # Ergogen's source YAML keeps named points under points.zones.*.key.* only
    # after expansion, so for this repository parse the generated point entries
    # from the top-level explicit anchors by walking mappings.
    out = {}

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, dict) and "anchor" in value and isinstance(value["anchor"], dict):
                    a = value["anchor"]
                    if "shift" in a and isinstance(a["shift"], list) and len(a["shift"]) >= 2:
                        out[key] = (
                            float(a["shift"][0]),
                            float(a["shift"][1]),
                            float(a.get("rotate", 0.0)),
                        )
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(config.get("points", {}))
    return out


def section_loops_xy(mesh: trimesh.Trimesh, z: float) -> list[np.ndarray]:
    section = mesh.section(plane_origin=[0,0,z], plane_normal=[0,0,1])
    if section is None:
        return []
    planar, to_3d = section.to_2D()
    loops = []
    for arr in planar.discrete:
        arr = np.asarray(arr, dtype=float)
        if len(arr) < 4:
            continue
        # to_2D coordinates are already the source XY basis for a horizontal
        # section; verify closure and keep only closed rings.
        if np.linalg.norm(arr[0] - arr[-1]) > 0.1:
            continue
        loops.append(arr[:,:2])
    return loops


def switch_hole_candidates(mesh: trimesh.Trimesh) -> tuple[float, list[dict]]:
    zmin, zmax = mesh.bounds[:,2]
    # Avoid coplanar triangle ambiguity by sampling several interior planes.
    zs = np.linspace(zmin + 0.2*(zmax-zmin), zmax - 0.2*(zmax-zmin), 5)
    best = (None, [])
    for z in zs:
        candidates = []
        for loop in section_loops_xy(mesh, float(z)):
            poly = Polygon(loop)
            if not poly.is_valid or poly.area <= 0:
                continue
            minx,miny,maxx,maxy = poly.bounds
            w,h=maxx-minx,maxy-miny
            area=abs(poly.area)
            # MX plate apertures are nominally 14 x 14 mm.  Permit source
            # corner relief and STL tessellation.
            if 11.5 <= w <= 16.5 and 11.5 <= h <= 16.5 and 135 <= area <= 260:
                candidates.append({
                    "centroid": [float(poly.centroid.x), float(poly.centroid.y)],
                    "area": float(area),
                    "bounds": [float(minx),float(miny),float(maxx),float(maxy)],
                })
        if len(candidates) > len(best[1]):
            best = (float(z), candidates)
    return best


def rigid_fit(source: np.ndarray, target: np.ndarray) -> dict:
    """Fit source points to a same-or-larger target set.

    Assignment is solved in absolute coordinates, then the matched subset is
    re-centered for Kabsch rotation.  This avoids centroid bias when one stock
    plate aperture is non-MX-shaped and therefore absent from the source set.
    """
    if len(source) > len(target):
        raise ValueError(f"source has more points than target: {len(source)} > {len(target)}")

    best = None
    seeds = []
    for reflect in (False, True):
        F = np.array([[-1.0,0.0],[0.0,1.0]]) if reflect else np.eye(2)
        for deg in (0,90,180,270):
            a=math.radians(deg)
            R=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
            seeds.append(F @ R)

    for seed in seeds:
        M = seed.copy()
        t = target.mean(axis=0) - source.mean(axis=0) @ M.T
        assignment = None
        for _ in range(30):
            moved = source @ M.T + t
            cost = np.linalg.norm(moved[:,None,:] - target[None,:,:], axis=2)
            rows, cols = linear_sum_assignment(cost)
            order = np.argsort(rows)
            rows, cols = rows[order], cols[order]
            A = source[rows]
            B = target[cols]
            ac, bc = A.mean(axis=0), B.mean(axis=0)
            A0, B0 = A-ac, B-bc
            H = A0.T @ B0
            U,S,Vt = np.linalg.svd(H)
            R = Vt.T @ U.T
            want_det = -1.0 if np.linalg.det(seed) < 0 else 1.0
            if np.linalg.det(R) * want_det < 0:
                Vt[-1,:] *= -1
                R = Vt.T @ U.T
            nt = bc - ac @ R.T
            assignment = cols
            if np.linalg.norm(R-M) < 1e-11 and np.linalg.norm(nt-t) < 1e-9:
                M, t = R, nt
                break
            M, t = R, nt

        moved = source @ M.T + t
        err = np.linalg.norm(moved - target[assignment], axis=1)
        A0 = source - source.mean(axis=0)
        Bmatch = target[assignment]
        B0 = Bmatch - Bmatch.mean(axis=0)
        scale = np.sqrt(
            np.mean(np.sum(B0**2,axis=1)) /
            np.mean(np.sum(A0**2,axis=1))
        )
        result={
            "matrix_2x2":M.tolist(),
            "translation_xy":t.tolist(),
            "rms_mm":float(np.sqrt(np.mean(err**2))),
            "max_mm":float(err.max()),
            "determinant":float(np.linalg.det(M)),
            "inferred_scale":float(scale),
            "assignment":assignment.tolist(),
        }
        if best is None or result["rms_mm"] < best["rms_mm"]:
            best=result
    return best


def apply_xy(mesh: trimesh.Trimesh, fit: dict) -> trimesh.Trimesh:
    out=mesh.copy()
    M=np.asarray(fit["matrix_2x2"],dtype=float)
    t=np.asarray(fit["translation_xy"],dtype=float)
    xy=out.vertices[:,:2] @ M.T + t
    out.vertices[:,:2]=xy
    return out


def bounds_dict(mesh):
    return {
        "min":mesh.bounds[0].tolist(),
        "max":mesh.bounds[1].tolist(),
        "size":(mesh.bounds[1]-mesh.bounds[0]).tolist(),
        "centroid":mesh.centroid.tolist(),
        "watertight":bool(mesh.is_watertight),
        "volume":float(mesh.volume),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    config=yaml.safe_load(CONFIG.read_text())
    pts=named_points(config)
    missing=[x for x in EXPECTED_SWITCHES if x not in pts]
    if missing:
        raise AssertionError(f"missing canonical switch points: {missing}")
    target=np.array([[pts[x][0],pts[x][1]] for x in EXPECTED_SWITCHES],dtype=float)

    plate=load_mesh(PLATE)
    case=load_mesh(CASE)
    housing=load_mesh(HOUSING)

    z,candidates=switch_hole_candidates(plate)
    source=np.array([x["centroid"] for x in candidates],dtype=float)
    if not (18 <= len(source) <= len(target)):
        raise AssertionError(
            f"expected 18..{len(target)} MX-like apertures in switchplate section, found {len(source)} at z={z}; "
            f"areas={[round(x['area'],2) for x in candidates]}"
        )

    fit=rigid_fit(source,target)
    matched={EXPECTED_SWITCHES[i] for i in fit["assignment"]}
    unmatched=[x for x in EXPECTED_SWITCHES if x not in matched]
    print("switchplate XY fit:", json.dumps(fit, indent=2))
    if abs(fit["inferred_scale"]-1.0) > 0.005:
        raise AssertionError(f"switchplate source scale is not 1:1 mm: {fit['inferred_scale']}")
    if fit["rms_mm"] > 0.25 or fit["max_mm"] > 0.6:
        raise AssertionError(f"switchplate canonical alignment too loose: {fit}")

    plate_a=apply_xy(plate,fit)
    case_a=apply_xy(case,fit)

    plate_a.export(args.out/"konrad_switchplate_canonical_xy.stl")
    case_a.export(args.out/"konrad_case_right_canonical_xy.stl")

    hsize=(housing.bounds[1]-housing.bounds[0]).tolist()
    hcenter=((housing.bounds[1]+housing.bounds[0])/2).tolist()

    report={
        "status":"phase1_alignment_pass",
        "source":{
            "switchplate":str(PLATE.relative_to(ROOT)),
            "case":str(CASE.relative_to(ROOT)),
            "housing":str(HOUSING.relative_to(ROOT)),
        },
        "canonical":{
            "switches":{k:list(pts[k]) for k in EXPECTED_SWITCHES},
            "ball_center_xy":[16.5,-28.000147],
            "housing_center_from_ball_xy":[9.165901,0.000812],
        },
        "raw":{
            "switchplate":bounds_dict(plate),
            "case":bounds_dict(case),
            "housing":bounds_dict(housing),
            "housing_bbox_center":hcenter,
            "housing_bbox_size":hsize,
        },
        "switchplate_section":{
            "z":z,
            "candidate_count":len(candidates),
            "candidates":candidates,
        },
        "xy_fit":fit,
        "unmatched_canonical_switches":unmatched,
        "aligned":{
            "switchplate":bounds_dict(plate_a),
            "case":bounds_dict(case_a),
        },
    }
    (args.out/"task2e_phase1_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
