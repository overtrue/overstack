"""Verify profile source hashes, embedded geometry, quantities and slice coverage."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import np,trimesh
from scipy.spatial import cKDTree
from build_print_profiles import recipes
from print_profile_targets import TARGETS
parser=argparse.ArgumentParser();parser.add_argument('--printer',choices=TARGETS);args=parser.parse_args()
expected=dict(recipes());found={k:set() for k in TARGETS if not args.printer or k==args.printer}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

for path in sorted((ROOT/'print-profiles').rglob('manifest.json')):
    report=json.loads(path.read_text());folder=path.parent
    printer_key=report.get('printer_key','x2d')
    if printer_key not in found:continue
    target=TARGETS[printer_key]
    base=ROOT/'print-profiles'/target['folder'];project_name=report.get('project_file',printer_key+'-04-petg.3mf')
    assert folder==base/report['profile'],(path,'wrong target folder')
    assert report['printer']==target['printer'],(path,'wrong printer')
    found[printer_key].add(report['profile'])
    assert {(r['id'],r['source']) for r in report['parts']}=={(r['id'],r['file']) for r in expected[report['profile']]},(path,'incomplete recipe')
    for name,digest in report['model_source_hashes'].items():assert sha(ROOT/name)==digest,(path,'model source changed')
    if 'validation_source' in report:
        v=report['validation_source'];assert sha(ROOT/v['file'])==v['sha256'],(path,'validation changed')
    for name,digest in report.get('preset_hashes',{}).items():assert sha(base/'presets'/name)==digest,(path,'preset changed')
    for part in report['parts']:assert sha(ROOT/part['source'])==part['sha256'],(path,part['id'],'stale source')
    assert not report['makerworld_ready'] and report['physical_fit']=='not_verified'
    if report['status']=='blocked':
        assert not (folder/project_name).exists(),('blocked profile has project',path)
        print('BLOCKED:',report['profile']);continue
    assert report['preset_hashes'],(path,'missing preset provenance')
    project=folder/project_name;assert sha(project)==report['project_sha256']
    with zipfile.ZipFile(project) as z:
        assert z.testzip() is None
        settings=json.loads(z.read('Metadata/project_settings.config'))
        assert settings['printer_model']==target['printer']
        assert settings['curr_bed_type']=='Textured PEI Plate' and settings['filament_type']==['PETG']
        assert all(float(v)==.4 for v in settings['nozzle_diameter'])
        for k,v in report['process_overrides'].items():assert settings[k]==v,(path,k,'process mismatch')
        assert float(settings['layer_height'])==report['layer_mm']
        x0,y0,x1,y1=target['area']
        for part in report['parts']:
            assert np.all(np.array(part['bounds_mm'])<=np.array([x1-x0-6,y1-y0-6,target['height']])+.001),(path,part['id'],'build volume')
        config=ET.fromstring(z.read('Metadata/model_settings.config'))
        objects=config.findall('object');assert len(objects)==len(report['parts'])
        core={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        main=ET.fromstring(z.read('3D/3dmodel.model'))
        model_objects={o.get('id'):o for o in main.findall('./m:resources/m:object',core)}
        actual=[]
        for obj in objects:
            name=next(m.get('value') for m in obj.findall('metadata') if m.get('key')=='name')
            matches=[r for r in report['parts'] if name.startswith(r['id']+'-')]
            assert len(matches)==1,(path,name);actual.append(matches[0]['id'])
            component=model_objects[obj.get('id')].find('./m:components/m:component',core)
            external=component.get('{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path').lstrip('/')
            model=ET.fromstring(z.read(external))
            mesh=model.find('.//m:mesh',core)
            vertices=[[float(v.get(a)) for a in 'xyz'] for v in mesh.findall('./m:vertices/m:vertex',core)]
            faces=[[int(t.get(a)) for a in ['v1','v2','v3']] for t in mesh.findall('./m:triangles/m:triangle',core)]
            embedded=trimesh.Trimesh(vertices=vertices,faces=faces)
            source=trimesh.load_mesh(ROOT/matches[0]['source'])
            assert embedded.is_volume and np.isclose(embedded.volume,source.volume,rtol=1e-5),(path,name,'geometry volume')
            assert np.isclose(embedded.area,source.area,rtol=1e-5),(path,name,'geometry area')
            expected_mesh=source.copy();expected_mesh.apply_transform(matches[0]['assembly_to_print'])
            a=embedded.vertices-embedded.bounds.mean(axis=0);b=expected_mesh.vertices-expected_mesh.bounds.mean(axis=0)
            assert cKDTree(a).query(b)[0].max()<.0002 and cKDTree(b).query(a)[0].max()<.0002,(path,name,'vertex geometry')
        assert sorted(actual)==sorted(r['id'] for r in report['parts'])
        assigned=[next(m.get('value') for m in i.findall('metadata') if m.get('key')=='object_id') for i in config.findall('./plate/model_instance')]
        assert sorted(assigned)==sorted(o.get('id') for o in objects),(path,'plate coverage')
    if report['status']=='sliced_not_printed':
        assert report['slice_exit_code']==0 and len(report['gcode_files'])==len(report['plates'])
        if printer_key!='x2d':
            evidence=json.loads((folder/'slice-validation.json').read_text())
            assert evidence['project_sha256']==report['project_sha256']
            assert evidence['printer']==target['printer'] and len(evidence['plates'])==len(report['plates'])
            for plate in evidence['plates']:
                bounds=plate['bbox_xy_mm'];x0,y0,x1,y1=target['area']
                assert bounds[0]>=x0 and bounds[1]>=y0 and bounds[2]<=x1 and bounds[3]<=y1,(path,'slice outside target nozzle area')
        info=ET.parse(folder/'slice-info.xml');plates=info.findall('plate');assert len(plates)==len(report['plates'])
        assert len(info.findall('.//object'))==len(report['parts'])
        for p in plates:
            meta={m.get('key'):m.get('value') for m in p.findall('metadata')}
            assert meta['outside']=='false' and float(meta['weight'])>0 and float(meta['prediction'])>0
            assert all(o.get('skipped')=='false' for o in p.findall('object'))
            assert (folder/f"plate_{meta['index']}.png").exists()
    print('PASS:',report['profile'],report['status'],len(report['parts']),'parts')

for printer_key,profiles in found.items():
    if not (ROOT/'print-profiles'/TARGETS[printer_key]['folder']).exists():continue
    assert profiles==set(expected),(printer_key,'missing/extra profiles',set(expected)-profiles,profiles-set(expected))
