#!/usr/bin/env python3
import json, math
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[2]
PLATE=ROOT/'klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl'
CASE=ROOT/'klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl'

def load(p):
 m=trimesh.load_mesh(p,force='mesh',process=False)
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
  out.append({'center':(lo+hi)/2,'wh':wh,'n':len(a)})
 return out

def small_centers(ls,minw=1.0,maxw=7.0):
 pts=[];meta=[]
 for q in ls:
  w,h=q['wh']
  if minw<=w<=maxw and minw<=h<=maxw and abs(w-h)<=1.5:
   pts.append(q['center']);meta.append({'center':np.round(q['center'],5).tolist(),'wh':np.round(q['wh'],5).tolist(),'n':q['n']})
 return np.array(pts,float),meta

def tf_pair(p1,p2,q1,q2,reflect):
 F=np.array([[-1.,0],[0,1.]]) if reflect else np.eye(2);u=F@(p2-p1);v=q2-q1
 a=math.atan2(v[1],v[0])-math.atan2(u[1],u[0]);C=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
 R=C@F;t=q1-R@p1;return R,t

def score(src,dst,R,t,tol=.4):
 moved=src@R.T+t;tree=cKDTree(dst);d,j=tree.query(moved)
 c=sorted([(float(dd),i,int(jj)) for i,(dd,jj) in enumerate(zip(d,j)) if dd<=tol])
 us=set();ud=set();out=[]
 for dd,i,jj in c:
  if i not in us and jj not in ud:us.add(i);ud.add(jj);out.append((i,jj,dd))
 rms=math.sqrt(sum(x[2]**2 for x in out)/len(out)) if out else 1e9
 return len(out),rms,out

def refine(src,dst,pairs):
 P=np.array([src[i] for i,j,d in pairs]);Q=np.array([dst[j] for i,j,d in pairs]);pc=P.mean(0);qc=Q.mean(0)
 U,S,Vt=np.linalg.svd((P-pc).T@(Q-qc));R=Vt.T@U.T;t=qc-R@pc;return R,t

def solve(src,dst):
 best=None
 for i in range(len(src)):
  for j in range(i+1,len(src)):
   ds=np.linalg.norm(src[j]-src[i])
   if ds<10:continue
   for a in range(len(dst)):
    for b in range(a+1,len(dst)):
     dd=np.linalg.norm(dst[b]-dst[a])
     if abs(ds-dd)>.25:continue
     for qa,qb in [(a,b),(b,a)]:
      for refl in [False,True]:
       R,t=tf_pair(src[i],src[j],dst[qa],dst[qb],refl);n,r,p=score(src,dst,R,t,.5)
       key=(n,-r)
       if best is None or key>best[0]:best=(key,R,t,p)
 if best is None:return None
 R,t=refine(src,dst,best[3]);n,r,p=score(src,dst,R,t,.3)
 return {'R':np.round(R,9).tolist(),'t':np.round(t,6).tolist(),'det':float(np.linalg.det(R)),'matches':n,'rms_mm':r,'pairs':p}

p=load(PLATE);c=load(CASE)
plate_z=float(np.mean(p.bounds[:,2]));pp,pm=small_centers(loops(p,plate_z),1,7)
report={'plate_z':plate_z,'plate_small':pm,'case':{}}
for z in [-4.7,-3.1,-2.9,-2.0,-0.9,-0.7,0.0,2.0,4.0,6.0,7.0,8.0,8.79]:
 cp,cm=small_centers(loops(c,z),1,7)
 sol=solve(pp,cp) if len(cp)>=2 and len(pp)>=2 else None
 report['case'][str(z)]={'small':cm,'solve':sol}
print(json.dumps(report,indent=2))
