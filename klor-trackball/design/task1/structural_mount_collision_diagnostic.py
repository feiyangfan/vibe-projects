#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
import trimesh
import mechanical_reference_audit_v3 as audit

# Reuse the verified source/transform solving from v3, but emit a focused exact
# fastener/housing collision diagnostic in the native switchplate frame.
plate = audit.load_mesh(audit.PATHS["switchplate"])
case = audit.load_mesh(audit.PATHS["case"])
housing = audit.load_mesh(audit.PATHS["housing_right"])
pcb_text = audit.PATHS["pcb"].read_text(errors="ignore")
fps = audit.parse_footprints(pcb_text)
sw_pts, sw_rows = audit.switch_footprints(fps)
plate_mx, plate_small, _, _ = audit.switchplate_features(plate)
drill_centers, _ = audit.parse_drill_switch_centers(audit.PATHS["drill"].read_text(errors="ignore"))
Rkg,tkg,_,_,_ = audit.solve_pointsets(sw_pts,drill_centers,final_tolerance=.01)
Rkp,tkp,_,_,_ = audit.solve_pointsets(sw_pts,plate_mx,final_tolerance=.10)
Rpc,tpc,_,_,_,plate_axes,case_axes,_ = audit.structural_case_axes(case,plate_small)

def g2k(xy): return Rkg.T @ (np.asarray(xy)-tkg)
def k2p(xy): return Rkp @ np.asarray(xy)+tkp
ball_p=k2p(g2k(audit.BALL_G))
M=np.diag([-1.,1.])
A=Rkp @ Rkg.T @ M
H=np.eye(4);H[:2,:2]=A;H[:2,3]=ball_p;H[2,3]=audit.PLATE_THICKNESS_MM-audit.HOUSING_MOUNT_LOCAL_Z
housing.apply_transform(H)

# Conservative generic M2 pan/button-head envelope: 4.5 mm diameter, 2.0 mm
# above the plate surface. This is intentionally larger than a typical M2 head.
# Also test a 6.1 mm diameter column below the plate matching the measured case
# boss OD; it should not collide because it terminates at the plate underside.
manager=trimesh.collision.CollisionManager();manager.add_object('housing',housing)
rows=[]
for i,axis in enumerate(plate_axes):
    screw=trimesh.creation.cylinder(radius=2.25,height=2.0,sections=64)
    screw.apply_translation([axis[0],axis[1],audit.PLATE_THICKNESS_MM+1.0])
    screw_hit=bool(manager.in_collision_single(screw))
    boss=trimesh.creation.cylinder(radius=3.05,height=7.0,sections=64)
    boss.apply_translation([axis[0],axis[1],-3.5])
    boss_hit=bool(manager.in_collision_single(boss))
    # Minimum point-to-axis radial distance for housing vertices in the first
    # 3 mm above the plate gives an independent local clearance diagnostic.
    v=np.asarray(housing.vertices)
    band=v[(v[:,2]>=audit.PLATE_THICKNESS_MM-1e-4)&(v[:,2]<=audit.PLATE_THICKNESS_MM+3.0)]
    radial=float(np.min(np.linalg.norm(band[:,:2]-axis,axis=1))) if len(band) else None
    rows.append({
        'index':i,
        'axis_switchplate_native':np.round(axis,5).tolist(),
        'conservative_m2_head_collision':screw_hit,
        'below_plate_6p1mm_boss_collision':boss_hit,
        'nearest_housing_vertex_radial_mm_in_0_to_3mm_above_plate':radial,
    })
print(json.dumps({'fastener_envelope':{'head_diameter_mm':4.5,'head_height_mm':2.0,'boss_diameter_mm':6.1},'mounts':rows,'all_fastener_heads_clear':all(not x['conservative_m2_head_collision'] for x in rows),'all_below_plate_bosses_clear':all(not x['below_plate_6p1mm_boss_collision'] for x in rows)},indent=2))
