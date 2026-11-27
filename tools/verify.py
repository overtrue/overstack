"""Check exported deliverables and the absence of external model inputs."""
from pathlib import Path
import sys,json,ast
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
from ht_layers import LAYERS
D=ROOT/'output/model';data=json.loads((D/'checks.json').read_text())
assert len(data['parts'])==48
assert data['source_mesh_inputs']==[]
assert data['assembly_pairs_checked']==1128
counts=[sum(r['layer']==i for r in data['parts']) for i in range(5)]
assert counts==[6,10,13,15,4],counts
for r in data['parts']:
    m=trimesh.load_mesh(D/r['file'])
    assert m.is_volume and m.is_watertight and len(m.split())==1,r['name']
    assert np.allclose(m.bounds,r['bounds_mm'],atol=.0001),r['name']
scene=trimesh.load(D/'assembly.glb');bounds=[]
records={r['name']:r for r in data['parts']}
assert set(scene.graph.nodes_geometry)==set(records)
for n in scene.graph.nodes_geometry:
    t,k=scene.graph[n];m=scene.geometry[k].copy();m.apply_transform(t)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]));m.apply_scale(1000);bounds.append(m.bounds)
    r=records[n];z=LAYERS[r['layer']][2]
    assert np.allclose(m.bounds,np.array(r['bounds_mm'])+[0,0,z],atol=.001),('stack position',n)
assert np.allclose(np.max(np.array(bounds)[:,1],axis=0)-np.min(np.array(bounds)[:,0],axis=0),[495,287,249],atol=.001)
# Geometry constructors may only create shapes; model-file loaders are forbidden.
for path in (ROOT/'src/overstack').glob('*.py'):
    tree=ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            assert node.func.attr not in {'load','load_mesh','load_scene','read_text','read_bytes'},(path.name,node.lineno)
assert not any('side_cover' in r['name'] for r in data['parts'])
# Both low front openings must be solid as one part with their side carriers.
for name,x in [('low_0_cassette_plates_1',68.5),('low_0_cassette_plates_2',385.5)]:
    m=trimesh.load_mesh(D/'parts'/(name+'.stl'))
    assert abs(cut(box(x,.01,8.01,41,7.98,31.98),m).volume)<.02,('front closure',name)
print('PASS: 48 closed solids; five complete layers; 495 x 287 x 249 mm; no external model inputs; two integral front closures')

# Five usable ledges in the new low layer; the former height and a sixth slot
# must be refused rather than silently reducing the required top clearance.
from base import build_module
for h,n in [(30,3),(40,6)]:
    try:build_module(h,n)
    except ValueError:pass
    else:raise AssertionError(('unsupported plate layout accepted',h,n))
carrier=trimesh.load_mesh(D/'parts/low_0_cassette_plates_1.stl')
end=trimesh.load_mesh(D/'parts/low_0_end_left_1.stl')
assert abs(end.bounds[1,2]-40)<.001
for i in range(5):
    ledge=box(120,100,6.2+6*i,4,20,1)
    assert abs(cut(ledge,carrier).volume)<.001,('missing low ledge',i)
    plate=box(120,100,7.5+6*i,4,20,1.5)
    assert overlap(plate,carrier)<.001,('low slot obstructed',i)
assert end.bounds[1,2]-(7.5+4*6+1.5)>=7
print('PASS: exported 40 mm layer has five clear slots; 30 mm and six-slot layouts rejected.')
