"""Extract small fit specimens from the same analytic interfaces as production parts."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
from base import build_module
from layer_locks import REAR_LOCK_FILE,layer_lock
from ht_top import right_top_parts
from surfaces import top_parts
from fabrication import orient
import compact
def inter(a,b):return trimesh.boolean.intersection([a,b],engine="manifold")
m=build_module(40,5);ends=m['ends'][0];carrier=compact.plate_layer(m)['plate_carrier_left']
parts={
 'FIT02-dovetail-socket':inter(ends,box(45,27,0,20,26,40)),
 'FIT03-dovetail-tongue':inter(m['parts']['cassette_plates'],box(52,27,0,24,26,40)),
 'FIT04-plate-slots':inter(carrier,box(55,100,0,85,25,40)),
 'FIT05-key-lower':inter(move(ends,[0,0,-40]),box(24,269,-12,28,18,12)),
 'FIT06-key-upper':inter(ends,box(24,269,0,28,18,12)),
 'FIT07-key':layer_lock(),
 'FIT08-foot-lower':inter(move(ends,[0,0,-40]),box(0,0,-12,30,30,12)),
 'FIT09-foot-upper':inter(ends,box(0,0,-3,30,30,15)),
}
for n,p in parts.items():assert p.is_volume and len(p.split())==1,(n,'disconnected specimen')
for a,b in [('FIT02-dovetail-socket','FIT03-dovetail-tongue'),('FIT05-key-lower','FIT07-key'),('FIT06-key-upper','FIT07-key'),('FIT08-foot-lower','FIT09-foot-upper')]:assert overlap(parts[a],parts[b])<.01,(a,b)
for travel in [0,1,5,20,45]:assert overlap(parts['FIT02-dovetail-socket'],move(parts['FIT03-dovetail-tongue'],[0,0,travel]))<.01
for travel in [0,1,5,20]:
 for n in ['FIT05-key-lower','FIT06-key-upper']:assert overlap(parts[n],move(parts['FIT07-key'],[0,travel,0]))<.01
parents={'FIT02':ends,'FIT03':carrier,'FIT04':carrier,'FIT05':ends,'FIT06':ends,'FIT07':layer_lock(),'FIT08':ends,'FIT09':ends}
out=ROOT/'models/fit-check';out.mkdir(exist_ok=True);rows=[]
for n,p in parts.items():
 f=out/(n+'.stl');p.export(f);rows.append({'id':n.split('-')[0],'file':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'print_rotation':np.array(orient(parents[n.split('-')[0]])[1]['assembly_to_print'])[:3,:3].tolist()})
next(r for r in rows if r['id']=='FIT07')['print_file']=REAR_LOCK_FILE
(out/'parts.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'connected specimens; dovetail, rear-key and corner mating checks')

# Clip the production rear corner and the narrower of the two new rail joints.
# The crop includes the actual F04 key, the exposed R3 lip end and the R15 rim.
front,rear,_,rear_foot=right_top_parts(top_parts()[1])
corner=box(432,262,-12,64,26,39)
seam=box(478,153,-.1,18,32,27)
right_key=mirror_x(layer_lock())
coupons=[('HT01-lower-corner',intersection(move(m['ends'][1],[0,0,-40]),corner),0),
         ('HT02-upper-corner',intersection(rear,corner),0),('HT03-rear-key',right_key,90),
         ('HT04-rear-foot',rear_foot,0),('HT05-front-joint',intersection(front,seam),0),
         ('HT06-rear-joint',intersection(rear,seam),0)]
rows=[]
for name,part,angle in coupons:
    assert part.is_volume and len(part.split())==1,name
    path=out/(name+'.stl');part.export(path)
    rotation=trimesh.transformations.rotation_matrix(np.radians(angle),[1,0,0])[:3,:3]
    rows.append({'id':name.split('-')[0],'file':str(path.relative_to(ROOT)),
                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'print_rotation':rotation.tolist()})
next(r for r in rows if r['id']=='HT03')['print_file']=REAR_LOCK_FILE
(out/'ht-top-parts.json').write_text(json.dumps(rows,indent=2)+'\n')
