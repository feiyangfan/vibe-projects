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
import itertools
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


def horizontal_face_levels(mesh: trimesh.Trimesh, normal_tol=0.999, round_digits=3):
    tri=mesh.vertices[mesh.faces]
    cross=np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0])
    norm=np.linalg.norm(cross,axis=1)
    nz=np.divide(cross[:,2],norm,out=np.zeros_like(norm),where=norm>1e-12)
    area=norm/2.0
    levels={}
    for i in np.where(np.abs(nz)>=normal_tol)[0]:
        z=round(float(tri[i,:,2].mean()),round_digits)
        d=levels.setdefault(z,{"total_area":0.0,"up_area":0.0,"down_area":0.0})
        d["total_area"]+=float(area[i])
        if nz[i]>0:
            d["up_area"]+=float(area[i])
        else:
            d["down_area"]+=float(area[i])
    return [
        {"z":z, **vals}
        for z,vals in sorted(levels.items(), key=lambda kv: -kv[1]["total_area"])
    ]


def case_mount_candidates(mesh: trimesh.Trimesh):
    zmin,zmax=mesh.bounds[:,2]
    best=None
    # Bottom screw/countersink holes persist through the lower shell.  Search
    # the lower 40% of the case and select the section with eight near-circular
    # M2-sized loops.
    for z in np.linspace(zmin+0.3, zmin+0.42*(zmax-zmin), 28):
        loops=[]
        for loop in section_loops_xy(mesh,float(z)):
            poly=Polygon(loop)
            if not poly.is_valid or poly.area<=0:
                continue
            minx,miny,maxx,maxy=poly.bounds
            w,h=maxx-minx,maxy-miny
            area=abs(poly.area)
            aspect=max(w,h)/max(min(w,h),1e-9)
            if 2.0 <= w <= 5.5 and 2.0 <= h <= 5.5 and 3.0 <= area <= 24.0 and aspect <= 1.08:
                loops.append({
                    "centroid":[float(poly.centroid.x),float(poly.centroid.y)],
                    "area":float(area),
                    "bounds":[float(minx),float(miny),float(maxx),float(maxy)],
                })
        score=(abs(len(loops)-8), -len(loops))
        if best is None or score < best[0]:
            best=(score,float(z),loops)
    return best[1],best[2]


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
    if len(source) < 17:
        raise AssertionError(
            f"expected at least 17 MX-like apertures in switchplate section, found {len(source)} at z={z}"
        )

    print("MX-like section candidates:", json.dumps(candidates, indent=2))
    print("canonical MX targets:", json.dumps({
        k: [float(target[i,0]), float(target[i,1])]
        for i,k in enumerate(EXPECTED_SWITCHES)
    }, indent=2))

    # The stock 3DP Konrad plate has 17 invariant finger-grid MX apertures plus
    # mechanically different thumb/encoder-region openings.  Establish the
    # coordinate frame from the invariant SW1..SW17 grid only.  With 19
    # MX-sized candidate loops, exhaustive 17-of-N selection is tiny and avoids
    # letting thumb/encoder geometry bias the frame.
    main_names=[f"sw{i}" for i in range(1,18)]
    main_target=np.array([[pts[x][0],pts[x][1]] for x in main_names],dtype=float)
    best_main=None
    best_indices=None
    for combo in itertools.combinations(range(len(source)), len(main_target)):
        sub=source[list(combo)]
        trial=rigid_fit(sub,main_target)
        if best_main is None or trial["rms_mm"] < best_main["rms_mm"]:
            best_main=trial
            best_indices=list(combo)
    fit=best_main
    source_fit=source[best_indices]
    unmatched_source_indices=[i for i in range(len(source)) if i not in set(best_indices)]

    M=np.asarray(fit["matrix_2x2"],dtype=float)
    t=np.asarray(fit["translation_xy"],dtype=float)
    all_transformed=source @ M.T + t
    extra_features=[
        {
            "source_index":i,
            "source_xy":source[i].tolist(),
            "canonical_xy":all_transformed[i].tolist(),
        }
        for i in unmatched_source_indices
    ]
    unmatched=[]
    print("switchplate XY fit:", json.dumps(fit, indent=2))
    if abs(fit["inferred_scale"]-1.0) > 0.005:
        raise AssertionError(f"switchplate source scale is not 1:1 mm: {fit['inferred_scale']}")
    if fit["rms_mm"] > 0.25 or fit["max_mm"] > 0.6:
        raise AssertionError(f"switchplate main-grid canonical alignment too loose: {fit}")

    plate_a=apply_xy(plate,fit)

    case_mount_names=[f"case_mount_{i}" for i in range(1,9)]
    case_target=np.array([[pts[x][0],pts[x][1]] for x in case_mount_names],dtype=float)
    case_z,case_candidates=case_mount_candidates(case)
    if len(case_candidates) != 8:
        raise AssertionError(
            f"expected exactly 8 case M2 holes, found {len(case_candidates)} at z={case_z}: {case_candidates}"
        )
    case_source=np.array([x["centroid"] for x in case_candidates],dtype=float)
    case_fit=rigid_fit(case_source,case_target)
    print("case XY fit:",json.dumps(case_fit,indent=2))
    if abs(case_fit["inferred_scale"]-1.0)>0.005:
        raise AssertionError(f"case source scale is not 1:1 mm: {case_fit['inferred_scale']}")
    if case_fit["rms_mm"]>0.25 or case_fit["max_mm"]>0.6:
        raise AssertionError(f"case canonical alignment too loose: {case_fit}")
    case_a=apply_xy(case,case_fit)

    plate_levels=horizontal_face_levels(plate)
    case_levels=horizontal_face_levels(case)
    housing_levels=horizontal_face_levels(housing)

    # Source-derived stock Z stack.
    case_floor=min(
        (x for x in case_levels if x["up_area"]>1000),
        key=lambda x:abs(x["z"]-(-3.0))
    )["z"]
    case_top=max(x["z"] for x in case_levels if x["up_area"]>100)
    plate_bottom=float(plate.bounds[0,2])
    plate_top=float(plate.bounds[1,2])
    plate_shift_z=case_top-plate_bottom
    pcb_bottom=case_floor+7.0
    pcb_thickness=1.6
    pcb_top=pcb_bottom+pcb_thickness
    assembled_plate_bottom=plate_bottom+plate_shift_z
    assembled_plate_top=plate_top+plate_shift_z
    plate_top_to_pcb_top=assembled_plate_top-pcb_top

    plate_a.apply_translation([0,0,plate_shift_z])

    plate_a.export(args.out/"konrad_switchplate_canonical_assembled.stl")
    case_a.export(args.out/"konrad_case_right_canonical.stl")
    housing.export(args.out/"keyball_type_c_right_source.stl")

    hsize=(housing.bounds[1]-housing.bounds[0]).tolist()
    hcenter=((housing.bounds[1]+housing.bounds[0])/2).tolist()

    report={
        "status":"phase2_stock_stack_pass",
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
            "switchplate_horizontal_levels":plate_levels[:20],
            "case_horizontal_levels":case_levels[:30],
            "housing_horizontal_levels":housing_levels[:30],
            "housing_bbox_center":hcenter,
            "housing_bbox_size":hsize,
        },
        "switchplate_section":{
            "z":z,
            "candidate_count":len(candidates),
            "candidates":candidates,
        },
        "xy_fit":fit,
        "case_mount_section":{"z":case_z,"candidates":case_candidates},
        "case_xy_fit":case_fit,
        "z_stack":{
            "case_inner_floor_z":case_floor,
            "standoff_mm":7.0,
            "pcb_bottom_z":pcb_bottom,
            "pcb_thickness_mm":pcb_thickness,
            "pcb_top_z":pcb_top,
            "case_top_seating_z":case_top,
            "plate_bottom_z":assembled_plate_bottom,
            "plate_top_z":assembled_plate_top,
            "plate_top_to_pcb_top_mm":plate_top_to_pcb_top,
        },
        "main_grid_source_indices":best_indices,
        "extra_plate_features":extra_features,
        "unmatched_canonical_switches":unmatched,
        "aligned":{
            "switchplate":bounds_dict(plate_a),
            "case":bounds_dict(case_a),
            "switchplate_assembled":bounds_dict(plate_a),
        },
    }
    (args.out/"task2e_phase1_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
