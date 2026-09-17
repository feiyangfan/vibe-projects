#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[2]
PLATE=ROOT/'klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl'
CASE=ROOT/'klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl'

def mesh(path):
    m=trimesh.load_mesh(path,force='mesh',process=False)
    if isinstance(m,trimesh.Scene):m=trimesh.util.concatenate(tuple(m.dump()))
    return m

def loops(m,z):
    s=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
    if s is None:return []
    out=[]
    for d in s.discrete:
        a=np.asarray(d)[:,:2]
        if len(a)<4:continue
        lo=a.min(0);hi=a.max(0);wh=hi-lo
        out.append({'center':np.round((lo+hi)/2,5).tolist(),'extents':np.round(wh,5).tolist(),'min':np.round(lo,5).tolist(),'max':np.round(hi,5).tolist(),'points':len(a)})
    return sorted(out,key=lambda q:q['extents'][0]*q['extents'][1],reverse=True)

p=mesh(PLATE);c=mesh(CASE)
report={'plate_bounds':np.round(p.bounds,6).tolist(),'case_bounds':np.round(c.bounds,6).tolist()}
report['plate_mid']=loops(p,float(np.mean(p.bounds[:,2])))[:12]
zs=[-4.7,-2,0,2,4,6,7,7.3,7.8,8.2,8.6,8.79]
report['case_sections']={str(z):loops(c,z)[:12] for z in zs}
# horizontal-face area by z
areas={}
for tri,n,a in zip(c.triangles,c.face_normals,c.area_faces):
    if abs(n[2])>.999 and np.ptp(tri[:,2])<1e-4:
        z=round(float(np.mean(tri[:,2])),3);areas[z]=areas.get(z,0)+float(a)
report['case_horizontal_planes']=[{'z':z,'area':round(a,4)} for z,a in sorted(areas.items())]
print(json.dumps(report,indent=2))
