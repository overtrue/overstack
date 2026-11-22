"""Check packing against actual footprints and regress the reported drawer layout."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import np,trimesh
from shapely.geometry import MultiPoint,box
from shapely.affinity import translate
from print_layout import orient_for_area,pack
from print_profile_targets import TARGETS


def validate(groups,parts,target):
    area=box(*target['area']);seen=[]
    for group in groups:
        shapes=[]
        for obj in group:
            m=trimesh.load_mesh(obj['path']);center=m.bounds.mean(axis=0)
            dx=obj.get('pos_x',[center[0]-target['bed'][0]/2])[0]+target['bed'][0]/2-center[0]
            dy=obj.get('pos_y',[center[1]-target['bed'][1]/2])[0]+target['bed'][1]/2-center[1]
            shape=translate(MultiPoint(m.vertices[:,:2]).convex_hull.buffer(3),xoff=dx,yoff=dy)
            assert area.buffer(.001).covers(shape),('brim outside bed',obj['path'])
            assert all(not shape.intersects(other) for other in shapes),('overlapping brims',obj['path'])
            shapes.append(shape);seen.append(obj['path'])
    assert sorted(seen)==sorted(parts),'missing or duplicate objects'


if __name__=='__main__':
    folder=ROOT/'output/print-profiles/x2d/ams2pro-ht/03-single-drawer-layer'
    groups=json.loads((folder/'assembly.json').read_text())['plates']
    groups=[g['objects'] for g in groups]
    paths=[str(p) for p in sorted(folder.glob('C*.stl'))]
    validate(groups,paths,TARGETS['x2d'])
    assert any(any('C05-' in o['path'] for o in g) and any('C06-' in o['path'] for o in g) for g in groups),'rails must share a plate'
    assert len(groups)<=7,'drawer layout regressed'
    # A mirrored half must rest on its outside face, not its open inside face.
    for name in ['C07-standard_2_drawer_1.stl','C08-standard_2_drawer_2.stl']:
        m=trimesh.load_mesh(ROOT/'models/ams2pro+ht/03-single-drawer-layer/parts'/name)
        _,pose=orient_for_area(m,TARGETS['x2d']['area'],260)
        assert pose['downward_area_mm2']<1800 and pose['bed_contact_area_mm2']>12000,pose
    # Ensure the checker rejects the failure it is intended to catch.
    bad=[[dict(groups[0][0]),dict(groups[0][0])]]
    try:validate(bad,[bad[0][0]['path']]*2,TARGETS['x2d'])
    except AssertionError:pass
    else:raise AssertionError('overlap check did not reject duplicate placement')
    print('PASS footprints, brims, rail grouping, mirrored drawer orientation and overlap rejection')
