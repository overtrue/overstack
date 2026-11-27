"""Validate floors and unchanged functional interface regions against V54."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
new=ROOT/'output/model';old=ROOT/'output/model-v54'
rows=json.loads((new/'checks.json').read_text())['parts'];changed=[]
for r in rows:
 n=r['name']
 if not n.startswith(('2drawers_drawer_','3drawers_drawer_')):continue
 a=trimesh.load_mesh(new/r['file']);b=trimesh.load_mesh(old/r['file'])
 changed.append(n)
 x0,x1=a.bounds[0,0]+6,a.bounds[1,0]-6
 core=box(x0,8,8.5,x1-x0,257,2)
 assert abs(cut(core,a).volume)<.02,('solid floor',n)
 assert abs(cut(core,b).volume)>10,('baseline must fail',n)
 assert overlap(box(x0+.1,8.1,10.501,x1-x0-.2,256.8,.2),a)<.02,('2 mm upper surface',n)
 # Changes confined to the old floor slab inside walls, away from functional grooves.
 allowed=box(x0,8,8.49,x1-x0,257,2.42)
 delta=union([cut(a,b),cut(b,a)])
 assert abs(cut(delta,allowed).volume)<.05,('interface altered',n)
# Side bins already have 2 mm solid floors; verify their full usable footprint.
for n,x in [('standard_1_side_bin_left_1',72),('standard_1_side_bin_right_1',389)]:
 a=trimesh.load_mesh(new/'parts'/(n+'.stl'))
 assert abs(cut(box(x,4,8.5,34,134,2),a).volume)<.02,n
assert len(changed)==5
report={'main_drawers':5,'side_bins':2,'solid_floor_mm':2,'changed_meshes':changed,'functional_interfaces':'unchanged outside floor slab','baseline_negative_control':'V54 lattice rejected'}
(new/'solid-floor-checks.json').write_text(json.dumps(report,indent=2));print('PASS: seven solid-bottom drawers; 2 mm floor; interfaces preserved')
