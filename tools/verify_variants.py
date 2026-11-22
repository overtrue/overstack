"""Independent exported-geometry checks, all layer pairings and common interfaces."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from layer_locks import layer_lock
from pegboard import slot_centers,yz_extrude
from shapely.geometry import LineString

report=json.loads((ROOT/'models/ams2pro/validation.json').read_text());layers={}
for row in report['parts']:
    p=ROOT/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],p
for layer in report['layers']:
    parts={r['name']:move(trimesh.load_mesh(ROOT/r['file']),r['offset_mm'])
           for r in json.loads((ROOT/'models/ams2pro'/layer['name']/'parts.json').read_text())}
    layers[layer['name']]=(layer['height_mm'],parts)
pairs=0
for lower,(H,lp) in layers.items():
    if lower=='device-top':continue
    for upper,(_,up) in layers.items():
        for an,a in lp.items():
            if an.startswith('lock_'):continue
            for bn,b in up.items():
                assert overlap(a,move(b,[0,0,H]))<.03,('stack pairing',lower,upper,an,bn)
                pairs+=1
        for right in [False,True]:
            key=mirror_x(layer_lock(),399) if right else layer_lock()
            for dz in [0,.3,1,3,10,30,60]:
                for name,m in up.items():
                    if name.startswith(('end_','plate_carrier','side_','top_')):
                        for an,a in lp.items():
                            if an.startswith('lock_'):continue
                            assert overlap(move(m,[0,0,H+dz]),a)<.03,('lowering',lower,upper,name,an,dz)
            for travel in [0,1,5,20]:
                k=move(key,[0,travel,H])
                for an,a in lp.items():
                    if not an.startswith('lock_'):assert overlap(k,a)<.03,('rear key lower',lower,travel,an)
                for bn,b in up.items():
                    if not bn.startswith('lock_'):assert overlap(k,move(b,[0,0,H]))<.03,('rear key upper',upper,travel,bn)
for H in [40,60]:
    for side in ['left','right']:
        plain=trimesh.load_mesh(ROOT/'models/common'/f'end_{side}_{H}_plain.stl')
        peg=trimesh.load_mesh(ROOT/'models/common'/f'end_{side}_{H}_pegboard.stl')
        assert abs(cut(peg,plain).volume)<.01
        if side=='right':plain=mirror_x(plain);peg=mirror_x(peg)
        protected=union([box(35,-1,-4,26,289,H+5),box(-1,-1,-4,62,25,H+5),box(-1,263,-4,62,25,H+5)])
        a=intersection(plain,protected);b=intersection(peg,protected)
        assert abs(cut(a,b).volume)+abs(cut(b,a).volume)<.01,('interface changed',H,side)
        for y,z in slot_centers(H):
            hole=LineString([(y,z-5),(y,z+5)]).buffer(2.5,quad_segs=16)
            assert np.allclose(hole.bounds,[y-2.5,z-7.5,y+2.5,z+7.5])
            assert overlap(peg,yz_extrude(hole,-.1,5.2))<.01
            # Solid panel lands either side are 5 mm, with actual clear air behind.
            for dy in [-5,5]:
                land=box(0,y+dy-.2,z-.2,5,.4,.4)
                assert abs(cut(land,peg).volume)<.01
            assert overlap(peg,box(5.1,y-3,z-8,20,6,16))<.01
print('PASS:',pairs,'exported stack pairs, lowering paths, rear keys, slot dimensions and unchanged interfaces')
(ROOT/'models/ams2pro/assembly-checks.json').write_text(json.dumps({'stack_pair_checks':pairs,'layer_pairings':20,
    'common_interfaces':'unchanged','slot_dimensions_mm':[5,15],'panel_thickness_mm':5,'physical_fit':'not_verified'},indent=2)+'\n')
