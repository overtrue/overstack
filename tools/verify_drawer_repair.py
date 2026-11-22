"""Check exported drawer joints, floors and the supported 256 mm print poses."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from fabrication import drawer_print_pose
D=ROOT/'output/model/parts'
left=trimesh.load_mesh(D/'standard_2_drawer_1.stl')
right=trimesh.load_mesh(D/'standard_2_drawer_2.stl')

def contains(mesh,probe):return abs(cut(probe,mesh).volume)<.01

# Probe the full female-channel length, not just the three male pads.
roof=box(247.81,45,9.9,7.68,225,1.39)
base=box(247.81,45,6.31,7.68,225,.8)
end=box(247.81,42.51,6.31,7.68,2.18,4.98)
for name,probe in [('roof',roof),('base',base),('closed end',end)]:
    assert contains(right,probe),name
assert not contains(cut(right,box(248,60,10,2,2,2)),roof),'negative control'
for travel in np.linspace(0,320,161):
    assert overlap(move(left,[0,travel,0]),right)<.01,('drawer joining',travel)
for delta in [[-1.5,0,0],[0,0,1],[0,0,-1],[0,-1,0]]:
    assert overlap(move(left,delta),right)>.1,('drawer capture',delta)
# Exercise the exported pair in the exported carrier, including removal at the stop.
carrier=union([trimesh.load_mesh(p) for p in D.glob('standard_2_cassette_drawer_*.stl')])
joined=union([left,right])
for travel in np.linspace(0,180,91):
    assert overlap(move(joined,[0,-travel,0]),carrier)<.01,('drawer travel',travel)
assert overlap(move(joined,[0,-181,0]),carrier)>1,'drawer stop'
for lift in np.linspace(0,7,29):
    assert overlap(move(joined,[0,-180,lift]),carrier)<.01,('drawer lift',lift)
for travel in np.linspace(180,300,25):
    assert overlap(move(joined,[0,-travel,7]),carrier)<.01,('drawer removal',travel)
poses={}
for name in ['standard_2_drawer_1','standard_2_drawer_2',*[f'3drawers_drawer_{i}' for i in range(1,4)]]:
    m=trimesh.load_mesh(D/(name+'.stl'));printed,pose=drawer_print_pose(m)
    assert m.is_volume and len(m.split())==1,name
    if name.startswith('3drawers'):
        x=m.bounds[0,0]
        assert contains(m,box(x+6.01,8.01,8.51,100.98,256.98,1.98)),name
        # The former DFM location is a full 6 mm sidewall/floor corner, not a thin skin.
        assert contains(m,box(x+.001,70,8.501,5.998,1,1)),name
    pose['source_sha256']=hashlib.sha256((D/(name+'.stl')).read_bytes()).hexdigest()
    poses[name]=pose
report={'female_channel_roof_mm_min':1.39,'female_channel_base_mm_min':.8,
        'closed_end_mm_min':2.18,'joining_positions_checked':161,'drawer_travel_mm':180,'lift_out_mm':7,
        'negative_control':'roof void rejected','poses':poses,
        'physical_fit':'not_verified','load_test':'not_verified'}
(ROOT/'output/model/drawer-repair-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS drawer joint stock, sliding capture, solid floors and planar print contact')
