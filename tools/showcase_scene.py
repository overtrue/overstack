"""Build display-only scenes from exports; no change to printable geometry."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from surfaces import illustrative_plate
D=ROOT/'models/ams2pro+ht';OUT=ROOT/'output/showcase';OUT.mkdir(parents=True,exist_ok=True)
rows=json.loads((D/'parts.json').read_text())
for key,layout in [('full',[(0,0),(1,40),(2,100),(3,160),(4,220),(5,280)]),('compact',[(0,0),(3,40),(5,100)])]:
 scene=trimesh.Scene();world=[]
 def add(name,m):
  world.append((name,m.copy()));m=m.copy();m.apply_scale(.001);m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));scene.add_geometry(m,node_name=name)
 for layer,z in layout:
  for r in rows:
   if r['layer']==layer:add(r['id'],move(trimesh.load_mesh(D/r['packaged_file']),[0,0,z]))
  if layer in [0,1]:
   for i in range(5 if layer==0 else 8):
    add(f'plate-{layer}-{i}',extrude(illustrative_plate(),z+7.5+i*6,.7))
 # Check the displayed stack, including plates, against volumetric intersections.
 for i,(an,a) in enumerate(world):
  for bn,b in world[i+1:]:
   if np.all(a.bounds[1]>=b.bounds[0]) and np.all(b.bounds[1]>=a.bounds[0]):
    assert overlap(a,b)<.03,(key,an,bn)
 scene.export(OUT/(key+'.glb'))
 print(key,len(world),'parts/plates; no volumetric interference')
