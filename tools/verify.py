"""Check exported deliverables and the absence of external model inputs."""
from pathlib import Path
import sys,json,ast
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
D=ROOT/'output/model-v55';data=json.loads((D/'checks.json').read_text())
assert len(data['parts'])==58
assert data['source_mesh_inputs']==[]
assert data['assembly_pairs_checked']==1653
counts=[sum(r['layer']==i for r in data['parts']) for i in range(6)]
assert counts==[6,10,10,13,15,4],counts
for r in data['parts']:
    m=trimesh.load_mesh(D/r['file'])
    assert m.is_volume and m.is_watertight and len(m.split())==1,r['name']
    assert np.allclose(m.bounds,r['bounds_mm'],atol=.0001),r['name']
scene=trimesh.load(D/'assembly.glb');bounds=[]
for n in scene.graph.nodes_geometry:
    t,k=scene.graph[n];m=scene.geometry[k].copy();m.apply_transform(t)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]));m.apply_scale(1000);bounds.append(m.bounds)
assert np.allclose(np.max(np.array(bounds)[:,1],axis=0)-np.min(np.array(bounds)[:,0],axis=0),[495,287,299],atol=.001)
# Geometry constructors may only create shapes; model-file loaders are forbidden.
for path in (ROOT/'src/stacknest').glob('*.py'):
    tree=ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            assert node.func.attr not in {'load','load_mesh','load_scene','read_text','read_bytes'},(path.name,node.lineno)
assert not any('side_cover' in r['name'] for r in data['parts'])
# Both low front openings must be solid as one part with their side carriers.
for name,x in [('low_0_cassette_plates_1',68.5),('low_0_cassette_plates_2',385.5)]:
    m=trimesh.load_mesh(D/'parts'/(name+'.stl'))
    assert abs(cut(box(x,.01,8.01,41,7.98,21.98),m).volume)<.02,('front closure',name)
print('PASS: 58 closed solids; six complete layers; 495 x 287 x 299 mm; no external model inputs; two integral front closures')
