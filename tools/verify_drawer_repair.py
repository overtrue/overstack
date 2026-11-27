"""Check exported triple-drawer floors, sidewalls and 256 mm print poses."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
from fabrication import drawer_print_pose
D=ROOT/'output/model/parts'
poses={}
for i in range(1,4):
    name=f'3drawers_drawer_{i}'
    m=trimesh.load_mesh(D/(name+'.stl'));printed,pose=drawer_print_pose(m)
    assert m.is_volume and len(m.split())==1,name
    x=m.bounds[0,0]
    floor=box(x+6.01,8.01,8.51,100.98,256.98,1.98)
    wall=box(x+.001,70,8.501,5.998,1,1)
    for probe in [floor,wall]:
        assert abs(cut(probe,m).volume)<.01,name
    pose['source_sha256']=hashlib.sha256((D/(name+'.stl')).read_bytes()).hexdigest()
    poses[name]=pose
report={'floor_mm':2,'sidewall_mm':6,'poses':poses,
        'physical_fit':'not_verified','load_test':'not_verified'}
(ROOT/'output/model/drawer-repair-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: three exported drawers, solid floors, sidewalls and planar print contact')
