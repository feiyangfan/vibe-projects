#!/usr/bin/env python3
"""Final Task 1 geometry audit.

Uses checked-in STL/KiCad/Excellon sources to solve all coordinate transforms,
place the Type-C housing, and evaluate conservative retained-component/service
clearances. Production CAD is never modified.
"""
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
P={
 "pcb":PROJECT/"klor1.4/PCB/klor1_4/klor1_4.kicad_pcb",
 "drill":PROJECT/"klor1.4/PCB/klor1_4/gerbers/klor1_4-NPTH.drl",
 "plate":PROJECT/"klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl",
 "case":PROJECT/"klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl",
 "step":PROJECT/"Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c.stp",
 "housing":PROJECT/"Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl",
 "left_housing":PROJECT/"Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_left.stl",
 "breakout":PROJECT/"klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb",
}
EXPECTED={
 "step":"79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c",
 "housing":"9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565",
 "left_housing":"5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58",
}
# Canonical placement is in KLOR manufacturing/drill coordinates.
BALL_G=np.array([162.323,-134.748])
SCREW_MID_G=np.array([156.111,-134.748])
BREAKOUT_G=np.array([143.111,-134.748])
DELETED_G=np.array([143.025,-128.770])
HOUSING_MOUNT_LOCAL_Z=-18.0

def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def load(path):
 m=trimesh.load_mesh(path,force="mesh",process=False)
 if isinstance(m,trimesh.Scene):m=trimesh.util.concatenate(tuple(m.dump()))
 return m

def blocks(text,keys):
 starts=[]
 for key in keys:
  p=0
  while True:
   i=text.find(key,p)
   if i<0:break
   starts.append(i);p=i+len(key)
 for s in sorted(starts):
  d=0;ins=False;esc=False
  for j in range(s,len(text)):
   c=text[j]
   if ins:
    if esc:esc=False
    elif c=="\\":esc=True
    elif c=='"':ins=False
    continue
   if c=='"':ins=True
   elif c=='(':d+=1
   elif c==')':
    d-=1
    if d==0:yield text[s:j+1];break

def footprints(text):
 out=[]
 for b in blocks(text,["(footprint","(module"]):
  mn=re.match(r'\((?:footprint|module)\s+"?([^"\s\)]+)',b); name=mn.group(1) if mn else ""
  mr=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',b) or re.search(r'\(fp_text\s+reference\s+"?([^"\s\)]+)',b)
  ma=re.search(r'\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?',b)
  if ma:out.append({"ref":mr.group(1) if mr else "","name":name,"x":float(ma.group(1)),"y":float(ma.group(2)),"rot":float(ma.group(3) or 0)})
 return out

def switches(fps):
 rows=[]
 for f in fps:
  n=(f["name"]+" "+f["ref"]).lower()
  if "encoder" in n or "rotary" in n:continue
  if f["ref"].upper().startswith("SW") or any(k in n for k in ["mx","hotswap","kailh","switch"]):rows.append(f)
 return np.array([[f["x"],f["y"]] for f in rows],float),rows

def section_loops(mesh,z):
 sec=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
 if sec is None:return []
 p,_=sec.to_2D();out=[]
 for d in p.discrete:
  a=np.asarray(d)[:,:2]
  if len(a)<4:continue
  lo=a.min(0);hi=a.max(0);out.append({"pts":a,"lo":lo,"hi":hi,"wh":hi-lo,"center":(lo+hi)/2})
 return out

def plate_features(mesh):
 z=float(np.mean(mesh.bounds[:,2]));ls=section_loops(mesh,z)
 mx=[];mount=[]
 for q in ls:
  w,h=q["wh"]
  if 12.5<=w<=16.5 and 12.5<=h<=16.5 and abs(w-h)<=2:mx.append(q["center"])
  if 1.5<=w<=6 and 1.5<=h<=6:mount.append(q["center"])
 outer=max(ls,key=lambda q:np.prod(q["wh"]))
 def uniq(xs):
  u=[]
  for x in xs:
   if not u or min(np.linalg.norm(x-y) for y in u)>.5:u.append(x)
  return np.array(u,float)
 return uniq(mx),uniq(mount),outer,z

def tf_pair(p1,p2,q1,q2,reflect):
 F=np.array([[-1.,0],[0,1.]]) if reflect else np.eye(2);u=F@(p2-p1);v=q2-q1
 a=math.atan2(v[1],v[0])-math.atan2(u[1],u[0]);C=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
 R=C@F;t=q1-R@p1;return R,t

def score(src,dst,R,t,tol=.35):
 mov=src@R.T+t;tree=cKDTree(dst);ds,ii=tree.query(mov)
 cand=sorted([(float(d),i,int(j)) for i,(d,j) in enumerate(zip(ds,ii)) if d<=tol])
 us=set();ud=set();keep=[]
 for d,i,j in cand:
  if i not in us and j not in ud:us.add(i);ud.add(j);keep.append((i,j,d))
 rms=math.sqrt(sum(d*d for _,_,d in keep)/len(keep)) if keep else 1e9
 return len(keep),rms,keep

def refine(src,dst,pairs):
 P=np.array([src[i] for i,j,d in pairs]);Q=np.array([dst[j] for i,j,d in pairs]);pc=P.mean(0);qc=Q.mean(0)
 U,S,Vt=np.linalg.svd((P-pc).T@(Q-qc));R=Vt.T@U.T;t=qc-R@pc;return R,t

def solve(src,dst,tol=.25):
 best=None
 sp=[(i,j,np.linalg.norm(src[j]-src[i])) for i in range(len(src)) for j in range(i+1,len(src))]
 dp=[(i,j,np.linalg.norm(dst[j]-dst[i])) for i in range(len(dst)) for j in range(i+1,len(dst))]
 for i,j,ds in sp:
  if ds<8:continue
  for a,b,dd in dp:
   if abs(ds-dd)>.2:continue
   for qa,qb in [(a,b),(b,a)]:
    for refl in [False,True]:
     R,t=tf_pair(src[i],src[j],dst[qa],dst[qb],refl);n,r,pairs=score(src,dst,R,t,.4)
     key=(n,-r)
     if best is None or key>best[0]:best=(key,R,t,pairs)
 if best is None:raise RuntimeError("no rigid point-set transform")
 R,t=refine(src,dst,best[3]);n,r,pairs=score(src,dst,R,t,tol)
 return R,t,n,r,pairs

def parse_drill_centers(text):
 diam={int(a):float(b) for a,b in re.findall(r'T(\d+)C([0-9.]+)',text)};tool=None;pts={}
 for line in text.splitlines():
  m=re.fullmatch(r'T(\d+)',line.strip())
  if m:tool=int(m.group(1));continue
  m=re.match(r'X(-?[0-9.]+)Y(-?[0-9.]+)',line.strip())
  if m and tool is not None:pts.setdefault(tool,[]).append(np.array([float(m.group(1)),float(m.group(2))]))
 # MX center pin-pair is the 1.7 mm NPTH tool, 9.0 mm apart.
 tool17=min(diam,key=lambda k:abs(diam[k]-1.7));a=pts[tool17];mids=[]
 for i in range(len(a)):
  for j in range(i+1,len(a)):
   if abs(np.linalg.norm(a[j]-a[i])-9.0)<.03:mids.append((a[i]+a[j])/2)
 # de-duplicate accidental pairings
 u=[]
 for x in mids:
  if not u or min(np.linalg.norm(x-y) for y in u)>.25:u.append(x)
 return np.array(u,float),{"tool":tool17,"diameter":diam[tool17],"raw_points":len(a),"centers":len(u)}

def rms_shape(A,B):
 ta=cKDTree(A);tb=cKDTree(B);d1=tb.query(A)[0];d2=ta.query(B)[0]
 return math.sqrt((np.mean(d1*d1)+np.mean(d2*d2))/2)

def best_plate_case(plate_outer,case):
 pc=plate_outer["center"];P0=plate_outer["pts"]-pc
 Os=[np.eye(2),np.array([[-1.,0],[0,1.]]),np.array([[1.,0],[0,-1.]]),-np.eye(2)]
 zmin,zmax=case.bounds[:,2];zs=np.linspace(zmin+.05,zmax-.05,70)
 best=None
 for z in zs:
  for q in section_loops(case,float(z)):
   if np.max(np.abs(q["wh"]-plate_outer["wh"]))>10:continue
   qc=q["center"]
   for O in Os:
    A=P0@O.T+qc;rr=rms_shape(A,q["pts"])
    key=rr
    if best is None or key<best[0]:best=(key,O,qc-O@pc,z,q["wh"])
 if best is None:raise RuntimeError("no case loop compatible with plate outline")
 return best

def horizontal_planes(mesh):
 out={}
 for tri,n,a in zip(mesh.triangles,mesh.face_normals,mesh.area_faces):
  if abs(n[2])>.999 and np.ptp(tri[:,2])<1e-4:
   z=round(float(np.mean(tri[:,2])),3);out[z]=out.get(z,0)+float(a)
 return sorted([{"z":z,"area":area} for z,area in out.items()],key=lambda x:x["z"])

def fp_candidates(fps,needles):
 out=[]
 for f in fps:
  n=(f["name"]+" "+f["ref"]).lower()
  if any(k in n for k in needles):out.append(f)
 return out

def gap_rect(hlo,hhi,c,half):
 lo=c-np.array(half);hi=c+np.array(half);dx=max(hlo[0]-hi[0],lo[0]-hhi[0],0);dy=max(hlo[1]-hi[1],lo[1]-hhi[1],0);return math.hypot(dx,dy)

def edge_extents(text):
 pts=[]
 for b in blocks(text,["(gr_line","(gr_rect","(gr_arc"]):
  if 'Edge.Cuts' not in b:continue
  for m in re.finditer(r'\((?:start|end|mid)\s+(-?[0-9.]+)\s+(-?[0-9.]+)',b):pts.append([float(m.group(1)),float(m.group(2))])
 if not pts:return None
 a=np.array(pts);return a.min(0),a.max(0)

def main():
 r={"task":1,"status":"final-audit","errors":[]}
 for k,p in P.items():
  if not p.exists():r["errors"].append(f"missing {k}")
 r["hashes"]={k:{"actual":sha(P[k]),"expected":EXPECTED[k],"matches":sha(P[k])==EXPECTED[k]} for k in EXPECTED}
 plate=load(P["plate"]);case=load(P["case"]);housing=load(P["housing"])
 pb=np.asarray(plate.bounds);cb=np.asarray(case.bounds)
 mx,mount,outer,zsec=plate_features(plate)
 pcbtxt=P["pcb"].read_text(errors="ignore");fps=footprints(pcbtxt);sw,swrows=switches(fps)
 Rp,tp,np_match,rp,pairs=solve(sw,mx)
 drill,di=parse_drill_centers(P["drill"].read_text(errors="ignore"));Rg,tg,ng,rg,gpairs=solve(sw,drill)
 r["frames"]={
  "kicad_to_gerber":{"R":np.round(Rg,9).tolist(),"t":np.round(tg,6).tolist(),"matches":ng,"rms_mm":round(rg,6),"drill":di},
  "kicad_to_switchplate":{"R":np.round(Rp,9).tolist(),"t":np.round(tp,6).tolist(),"matches":np_match,"rms_mm":round(rp,6)},
 }
 # canonical gerber -> kicad
 def g2k(v):return Rg.T@(v-tg)
 ball_k=g2k(BALL_G);deleted_k=g2k(DELETED_G);breakout_k=g2k(BREAKOUT_G);screw_k=g2k(SCREW_MID_G)
 ball_p=Rp@ball_k+tp;deleted_p=Rp@deleted_k+tp;breakout_p=Rp@breakout_k+tp
 # plate -> case frame from matching outline cross sections
 shape_r,Rc,tc,zmatch,casewh=best_plate_case(outer,case)
 plate_thick=float(pb[1,2]-pb[0,2]);plate_z_case=float(cb[1,2]-pb[1,2]) # plate top flush to case top
 planes=horizontal_planes(case);seat_expected=plate_z_case+pb[0,2];nearest_plane=min(planes,key=lambda q:abs(q["z"]-seat_expected))
 case_frame_ok=shape_r<1.5 and abs(nearest_plane["z"]-seat_expected)<.12
 r["frames"]["switchplate_to_case"]={"R":np.round(Rc,9).tolist(),"t_xy":np.round(tc,6).tolist(),"t_z":round(plate_z_case,6),"outline_rms_mm":round(shape_r,4),"matched_case_section_z":round(float(zmatch),4),"case_loop_extents":np.round(casewh,4).tolist(),"expected_plate_bottom_case_z":round(seat_expected,4),"nearest_horizontal_plane":nearest_plane,"verified":case_frame_ok}
 # Housing orientation: gerber differential is diag(-1,+1), then gerber->kicad->plate.
 M_g=np.diag([-1.,1.]);M_k=Rg.T@M_g;A=Rp@M_k
 plate_top=float(pb[1,2]);zshift=plate_top-HOUSING_MOUNT_LOCAL_Z
 H=np.eye(4);H[:2,:2]=A;H[:2,3]=ball_p;H[2,3]=zshift
 hp=housing.copy();hp.apply_transform(H);hb=np.asarray(hp.bounds)
 C=np.eye(4);C[:2,:2]=Rc;C[:2,3]=tc;C[2,3]=plate_z_case
 hc=hp.copy();hc.apply_transform(C)
 # exact stock-case triangle collision (expected to identify local relief, not move placement)
 collision=None
 try:
  cm=trimesh.collision.CollisionManager();cm.add_object("stock_case",case);collision=bool(cm.in_collision_single(hc))
 except Exception as e:r["errors"].append("collision-manager: "+str(e))
 r["placement"]={"ball_gerber":BALL_G.tolist(),"ball_kicad":np.round(ball_k,6).tolist(),"ball_switchplate":np.round(ball_p,6).tolist(),"deleted_switch_kicad":np.round(deleted_k,6).tolist(),"deleted_switch_plate":np.round(deleted_p,6).tolist(),"breakout_plate":np.round(breakout_p,6).tolist(),"housing_transform_to_switchplate":np.round(H,9).tolist(),"housing_bounds_switchplate":np.round(hb,5).tolist(),"housing_bounds_case":np.round(hc.bounds,5).tolist(),"stock_case_mesh_collision":collision}
 # validate deleted switch center exists in source switch set
 dists=np.linalg.norm(sw-deleted_k,axis=1);idel=int(np.argmin(dists));r["placement"]["deleted_switch_source"]={"ref":swrows[idel]["ref"],"name":swrows[idel]["name"],"xy":np.round(sw[idel],5).tolist(),"error_mm":round(float(dists[idel]),5)}
 # Retained keycap gaps: conservative 18x18 mm XY envelope. nearest two after removing deleted switch are R33/R32 by geometry.
 hlo,hhi=hb[0,:2],hb[1,:2];near=[]
 for i,p0 in enumerate(sw):
  if i==idel:continue
  pp=Rp@p0+tp;near.append((gap_rect(hlo,hhi,pp,(9,9)),i,p0,pp))
 near.sort(key=lambda x:x[0]);r["retained_switch_clearance"]=[]
 for label,x in zip(["R33-nearest","R32-next"],near[:2]):
  gap,i,p0,pp=x;r["retained_switch_clearance"].append({"label":label,"ref":swrows[i]["ref"],"pcb_kicad":np.round(p0,4).tolist(),"switchplate":np.round(pp,4).tolist(),"18mm_keycap_xy_gap_mm":round(float(gap),4)})
 # Encoder, MCU, TRRS conservative envelopes.
 groups={
  "encoder":(fp_candidates(fps,["encoder","rotary"]),(11,11)),
  "mcu":(fp_candidates(fps,["promicro","pro_micro","nice!nano","rp2040"]),(10,18)),
  "trrs":(fp_candidates(fps,["trrs","mj-4","mj4","pj320","pj-320","audiojack"]),(7,4)),
 }
 r["component_clearance"]={}
 for name,(rows,half) in groups.items():
  vals=[]
  for f in rows:
   pp=Rp@np.array([f["x"],f["y"]])+tp;vals.append({"ref":f["ref"],"name":f["name"],"switchplate":np.round(pp,4).tolist(),"housing_xy_gap_mm":round(gap_rect(hlo,hhi,pp,half),4)})
  r["component_clearance"][name]=vals
 # Breakout board dimensions and 2x22 insertion slot clearance.
 ex=edge_extents(P["breakout"].read_text(errors="ignore"));breakout_dims=None
 if ex:
  breakout_dims=np.sort(ex[1]-ex[0]).tolist()
 slot_lo=breakout_p+np.array([-1.,-11.]);slot_hi=breakout_p+np.array([1.,11.])
 path_gaps=[]
 for gap,i,p0,pp in near[:8]:path_gaps.append(gap_rect(slot_lo,slot_hi,pp,(9,9)))
 r["breakout"]={"edgecut_sorted_extents_mm":np.round(breakout_dims,4).tolist() if breakout_dims else None,"slot_center_switchplate":np.round(breakout_p,4).tolist(),"slot_size_xy_mm":[2,22],"nearest_retained_keycap_gap_mm":round(float(min(path_gaps)),4)}
 # Existing small plate mounting features vs housing local relief region.
 mount_d=[]
 for q in mount:
  mount_d.append(gap_rect(hlo,hhi,q,(1.5,1.5)))
 r["case_and_mounting"]={"plate_small_feature_count":int(len(mount)),"nearest_plate_mount_feature_to_housing_xy_gap_mm":round(float(min(mount_d)),4) if mount_d else None,"stock_case_collision_requires_local_relief":collision,"case_frame_verified":case_frame_ok}
 # Ball exposure and mounting-plane relation from verified source model.
 ball_top=plate_top+30.5;housing_top=float(hb[1,2]);r["vertical"]={"switchplate_top_z":plate_top,"housing_mount_plane_z":float(hb[0,2]),"ball_top_z":ball_top,"housing_top_z":housing_top,"rim_above_ball_mm":round(housing_top-ball_top,4),"mount_plane_aligned":abs(float(hb[0,2])-plate_top)<.01,"ball_exposure_understood":0<=housing_top-ball_top<=2.0}
 # Gates. Stock case collision is an expected local-relief requirement and is resolved for placement if no retained/mount feature is inside the housing envelope.
 src_ok=all(v["matches"] for v in r["hashes"].values())
 gerber_ok=ng>=18 and rg<.05 and np.linalg.det(Rg)<0
 plate_ok=np_match>=18 and rp<.05
 key_ok=all(q["18mm_keycap_xy_gap_mm"]>0 for q in r["retained_switch_clearance"])
 enc_ok=all(q["housing_xy_gap_mm"]>0 for q in r["component_clearance"]["encoder"])
 mcu_ok=all(q["housing_xy_gap_mm"]>0 for q in r["component_clearance"]["mcu"])
 trrs_ok=bool(r["component_clearance"]["trrs"]) and all(q["housing_xy_gap_mm"]>0 for q in r["component_clearance"]["trrs"])
 breakout_ok=r["breakout"]["nearest_retained_keycap_gap_mm"]>0
 mount_ok=(r["case_and_mounting"]["nearest_plate_mount_feature_to_housing_xy_gap_mm"] is None or r["case_and_mounting"]["nearest_plate_mount_feature_to_housing_xy_gap_mm"]>0)
 vertical_ok=r["vertical"]["mount_plane_aligned"] and r["vertical"]["ball_exposure_understood"]
 gates={"source_hashes_verified":src_ok,"gerber_kicad_frame_verified":gerber_ok,"pcb_switchplate_frame_verified":plate_ok,"switchplate_case_frame_verified":case_frame_ok,"r32_r33_collision_free":key_ok,"encoder_collision_free":enc_ok,"mcu_collision_free":mcu_ok,"trrs_collision_free":trrs_ok,"breakout_service_path_clear_of_retained_keys":breakout_ok,"case_critical_mount_features_clear":mount_ok,"housing_mounting_plane_verified":r["vertical"]["mount_plane_aligned"],"ball_exposure_verified":r["vertical"]["ball_exposure_understood"],"stock_case_local_relief_required":bool(collision)}
 gates["placement_locked"]=all(v for k,v in gates.items() if k not in ["stock_case_local_relief_required"])
 r["completion_gate"]=gates
 print(json.dumps(r,indent=2));return 0 if gates["placement_locked"] and not r["errors"] else 2
if __name__=="__main__":sys.exit(main())
