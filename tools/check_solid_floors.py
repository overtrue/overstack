"""Validate V55 floors and unchanged functional interface regions against V54."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
new=ROOT/'output/model-v55';old=ROOT/'output/model-v54'
rows=json.loads((new/'checks.json').read_text())['parts'];changed=[]
for r in rows:
 n=r['name'];a=trimesh.load_mesh(new/r['file']);b=trimesh.load_mesh(old/r['file'])
 is_main=n.startswith('standard_2_drawer_') or (n.startswith(('2drawers_drawer_','3drawers_drawer_')))
 if not is_main:
  assert abs(a.volume-b.volume)<.02 and np.allclose(a.bounds,b.bounds,atol=.0001),n
  assert overlap(a,b)>a.volume-.03,n
  continue
 changed.append(n)
 x0,x1=a.bounds[0,0]+6,a.bounds[1,0]-6
 ys=[(8,119),(152,265)] if n.startswith('standard') else [(8,265)]
 for y0,y1 in ys:
  y0=max(y0,a.bounds[0,1]);y1=min(y1,a.bounds[1,1])
  if y1<=y0:continue
  core=box(x0,y0,8.5,x1-x0,y1-y0,2)
  assert abs(cut(core,a).volume)<.02,('solid floor',n)
  assert abs(cut(core,b).volume)>10,('baseline must fail',n)
  assert overlap(box(x0+.1,y0+.1,10.501,x1-x0-.2,y1-y0-.2,.2),a)<.02,('2 mm upper surface',n)
 # Changes confined to the old floor slab inside walls, away from functional grooves.
 allowed=box(x0,8,8.49,x1-x0,257,2.42)
 delta=union([cut(a,b),cut(b,a)])
 assert abs(cut(delta,allowed).volume)<.05,('interface altered',n)
# Side bins already have 2 mm solid floors; verify their full usable footprint.
for n,x in [('standard_1_side_bin_left_1',72),('standard_1_side_bin_right_1',389)]:
 a=trimesh.load_mesh(new/'parts'/(n+'.stl'))
 assert abs(cut(box(x,4,8.5,34,134,2),a).volume)<.02,n
assert len(changed)==7
report={'version':'V55','main_drawers':6,'side_bins':2,'solid_floor_mm':2,'changed_meshes':changed,'functional_interfaces':'unchanged outside floor slab','baseline_negative_control':'V54 lattice rejected','note':'Single drawer retains original seam and locally thicker joint pads.'}
(new/'solid-floor-checks.json').write_text(json.dumps(report,indent=2));print('PASS: eight solid-bottom drawers; 2 mm floor; interfaces preserved')
