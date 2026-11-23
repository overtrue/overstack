"""Extract small fit specimens from the same analytic interfaces as production parts."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
from base import build_module
from layer_locks import layer_lock
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
(out/'parts.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'connected specimens; dovetail, rear-key and corner mating checks')
