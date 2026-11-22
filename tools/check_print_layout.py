"""Check packing against actual footprints and regress the reported drawer layout."""
from pathlib import Path
import argparse,hashlib,json,sys,tempfile
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
            m=trimesh.load_mesh(obj['path'])
            dx=obj.get('pos_x',[0])[0];dy=obj.get('pos_y',[0])[0]
            shape=translate(MultiPoint(m.vertices[:,:2]).convex_hull.buffer(3),xoff=dx,yoff=dy)
            assert area.buffer(.001).covers(shape),('brim outside bed',obj['path'])
            assert all(not shape.intersects(other) for other in shapes),('overlapping brims',obj['path'])
            shapes.append(shape);seen.append(obj['path'])
    assert sorted(seen)==sorted(parts),'missing or duplicate objects'


def validate_profile(manifest,recipes,pose_cache):
    import build_print_profiles as builder
    report=json.loads(manifest.read_text());key=report['printer_key'];target=TARGETS[key]
    assert report['status']=='sliced_not_printed',(manifest,report['status'])
    project=manifest.parent/report['project_file']
    assert hashlib.sha256(project.read_bytes()).hexdigest()==report['project_sha256'],(manifest,'project changed')
    evidence=json.loads((manifest.parent/'slice-validation.json').read_text())
    assert evidence['project_sha256']==report['project_sha256'],(manifest,'stale slice check')
    builder.TARGET=target
    rows={r['id']:r for r in recipes[report['profile']]}
    assert set(rows)=={p['id'] for p in report['parts']},(manifest,'recipe changed')
    for part in report['parts']:
        row=rows[part['id']];source=ROOT/row['file']
        assert part['source']==row['file'] and hashlib.sha256(source.read_bytes()).hexdigest()==part['sha256'],(manifest,part['id'],'source changed')
        cache_key=(key,row['file'],json.dumps(row.get('print_rotation')))
        if cache_key not in pose_cache:
            mesh=trimesh.load_mesh(source)
            printed,pose=builder.orient_for_target(mesh,source)
            if 'print_rotation' in row:
                t=np.eye(4);t[:3,:3]=row['print_rotation'];printed=mesh.copy();printed.apply_transform(t)
                shift=-printed.bounds[0];printed.apply_translation(shift);t[:3,3]=shift
                down=(printed.face_normals[:,2]<-.707)&(printed.triangles_center[:,2]>.25)
                pose={'assembly_to_print':t,'bounds_mm':printed.extents,'supports_required':float(printed.area_faces[down].sum())>1,'brim_mm':3}
            pose_cache[cache_key]=pose
        pose=pose_cache[cache_key]
        for field in ['assembly_to_print','bounds_mm']:
            assert np.allclose(part[field],pose[field],atol=.0001),(manifest,part['id'],'orientation changed')
        for field in ['supports_required','brim_mm']:
            assert part[field]==pose[field],(manifest,part['id'],'support settings changed')
    folder=ROOT/'output/print-profiles'/key/report['profile']
    groups=[g['objects'] for g in json.loads((folder/'assembly.json').read_text())['plates']]
    paths=[str(folder/(p['id']+'-'+Path(p['source']).stem+'.stl')) for p in report['parts']]
    validate(groups,paths,target)
    expected=pack(paths,report['parts'],target)
    assert len(expected)==len(groups),(manifest,'layout no longer matches packing rules')
    for actual,wanted in zip(groups,expected):
        assert [o['path'] for o in actual]==[o['path'] for o in wanted],(manifest,'different grouping')
        for a,b in zip(actual,wanted):
            for axis in ['pos_x','pos_y']:
                assert np.allclose(a.get(axis,[0]),b.get(axis,[0]),atol=.0001),(manifest,'different placement')
    # Preserve the original generation hashes; separately record that the output
    # still matches current rules when a code change has no effect on this profile.
    proof={'project_sha256':report['project_sha256'],
        'rule_source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [ROOT/'tools/print_layout.py',ROOT/'tools/build_print_profiles.py',ROOT/'tools/print_profile_targets.py',Path(__file__).resolve()]},
        'checks':['source geometry','orientation transforms','support flags','brim clearance','plate groups','XY placement']}
    (manifest.parent/'layout-rule-validation.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');args=parser.parse_args()
    if args.all:
        from build_print_profiles import recipes
        recipe_map=dict(recipes());pose_cache={}
        for key in TARGETS:
            for manifest in sorted((ROOT/'print-profiles'/key).glob('*/*/manifest.json')):
                validate_profile(manifest,recipe_map,pose_cache)
                print('PASS layout:',key,str(manifest.parent.relative_to(ROOT/'print-profiles'/key)),flush=True)
    folder=ROOT/'output/print-profiles/x2d/ams2pro-ht/03-single-drawer-layer'
    groups=json.loads((folder/'assembly.json').read_text())['plates']
    groups=[g['objects'] for g in groups]
    paths=[str(p) for p in sorted(folder.glob('C*.stl'))]
    validate(groups,paths,TARGETS['x2d'])
    assert any(any('C05-' in o['path'] for o in g) and any('C06-' in o['path'] for o in g) for g in groups),'rails must share a plate'
    assert len(groups)<=7,'drawer layout regressed'
    for name in ['C05-standard_2_cassette_drawer_3.stl','C06-standard_2_cassette_drawer_4.stl']:
        m=trimesh.load_mesh(ROOT/'models/ams2pro+ht/03-single-drawer-layer/parts'/name)
        _,pose=orient_for_area(m,TARGETS['x2d']['area'],260)
        assert pose['bounds_mm'][2]<=6.001 and pose['bed_contact_area_mm2']>5800,pose
    # A mirrored half must rest on its outside face, not its open inside face.
    for name in ['C07-standard_2_drawer_1.stl','C08-standard_2_drawer_2.stl']:
        m=trimesh.load_mesh(ROOT/'models/ams2pro+ht/03-single-drawer-layer/parts'/name)
        _,pose=orient_for_area(m,TARGETS['x2d']['area'],260)
        assert pose['downward_area_mm2']<1800 and pose['bed_contact_area_mm2']>12000,pose
    for source,height in [('models/common/end_left_60_plain.stl',63),
                          ('models/ams2pro/2-drawer-layer/drawer_1.stl',53),
                          ('models/ams2pro/8-slot-plate-layer/plate_carrier_left.stl',60)]:
        m=trimesh.load_mesh(ROOT/source)
        _,pose=orient_for_area(m,TARGETS['h2s']['area'],340)
        assert pose['bounds_mm'][2]<=height+.001,('unnecessary tall pose',source,pose)
    for name in ['E01-3drawers_divider_1.stl','E02-3drawers_divider_2.stl']:
        m=trimesh.load_mesh(ROOT/'models/ams2pro+ht/05-triple-drawer-layer/parts'/name)
        _,pose=orient_for_area(m,TARGETS['h2s']['area'],340,rotation=([1,0,0],180))
        assert pose['bounds_mm'][2]<=58.001 and pose['bed_contact_area_mm2']>2000,pose
    m=trimesh.load_mesh(ROOT/'models/ams2pro+ht/03-single-drawer-layer/parts/C07-standard_2_drawer_1.stl')
    _,pose=orient_for_area(m,TARGETS['h2s']['area'],340)
    assert pose['downward_area_mm2']<1800,('avoid supporting the entire drawer floor',pose)
    # Two flat drawer bodies fit side by side on the larger bed. Starting in the
    # center used to waste both remaining strips of space and force two plates.
    with tempfile.TemporaryDirectory() as temporary:
        m=trimesh.load_mesh(ROOT/'models/ams2pro/2-drawer-layer/drawer_1.stl')
        m,pose=orient_for_area(m,TARGETS['h2s']['area'],340)
        m.apply_translation([170-m.extents[0]/2,160-m.extents[1]/2,0])
        path=str(Path(temporary)/'drawer.stl');m.export(path)
        packed=pack([path,path],[pose,pose],TARGETS['h2s'])
        assert len(packed)==1,'two large-bed drawer bodies should share a plate'
        validate(packed,[path,path],TARGETS['h2s'])
    # Ensure the checker rejects the failure it is intended to catch.
    bad=[[dict(groups[0][0]),dict(groups[0][0])]]
    try:validate(bad,[bad[0][0]['path']]*2,TARGETS['x2d'])
    except AssertionError:pass
    else:raise AssertionError('overlap check did not reject duplicate placement')
    print('PASS footprints, brims, rail grouping, mirrored drawer orientation and overlap rejection')
