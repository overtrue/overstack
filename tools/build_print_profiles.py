"""Build Bambu Studio project profiles from the published part manifests."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import trimesh,np
from fabrication import orient
from multi_drawers import orient_candidate
STUDIO='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
OUT=ROOT/'print-profiles';WORK=ROOT/'output/print-profiles'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def recipes():
    yield 'fit-check/pegboard',[{'id':'FIT01','file':'models/common/pegboard_fit_coupon.stl'}]
    fit=ROOT/'models/fit-check/parts.json'
    if fit.exists():yield 'fit-check/interfaces',json.loads(fit.read_text())
    for p in sorted((ROOT/'models/ams2pro').glob('*/parts.json')):
        rows=json.loads(p.read_text())
        if not any(r['name'].startswith('lock_') for r in rows):
            rows += [{'id':'KEY-'+s,'file':f'models/common/lock_{s}.stl'} for s in ['left','right']]
        yield 'ams2pro/'+p.parent.name,rows
    rows=json.loads((ROOT/'models/ams2pro+ht/parts.json').read_text())
    for layer in sorted({r['layer'] for r in rows}):
        group=[{'id':r['id'],'file':'models/ams2pro+ht/'+r['packaged_file']} for r in rows if r['layer']==layer]
        slug=Path(next(r['packaged_file'] for r in rows if r['layer']==layer)).parts[0]
        if layer==0:group += [{'id':'KEY-'+s,'file':f'models/common/lock_{s}.stl'} for s in ['left','right']]
        yield 'ams2pro-ht/'+slug,group

def run(args,folder,log):
    result=subprocess.run([STUDIO,*args,'--outputdir',str(folder)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (folder/log).write_text(result.stdout)
    return result.returncode,result.stdout

def build(key,rows,slice_project):
    dest=OUT/key;dest.mkdir(parents=True,exist_ok=True)
    work=WORK/key;work.mkdir(parents=True,exist_ok=True)
    report={'profile':key,'printer':'Bambu Lab X2D','nozzle_mm':.4,'material':'Bambu PETG Basic','bed':'Textured PEI Plate','layer_mm':.2,
            'end_style':'plain' if key.startswith('ams2pro') else None,'studio_version':'02.09.01.70','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'physical_fit':'not_verified','load_test':'not_verified','makerworld_ready':False,'parts':[],'status':'preparing'}
    sources=[*sorted((ROOT/'src/stacknest').glob('*.py')),ROOT/'tools/build.py',ROOT/'tools/build_variants.py',ROOT/'tools/build_fit_checks.py']
    report['model_source_hashes']={str(p.relative_to(ROOT)):digest(p) for p in sources}
    inputs=[];blockers=[]
    for r in rows:
        source=ROOT/r['file'];mesh=trimesh.load_mesh(source)
        try:printed,pose=orient(mesh)
        except AssertionError:
            try:printed,pose=orient_candidate(mesh)
            except AssertionError:
                blockers.append(r['id']+': no fitting orientation');report['parts'].append({'id':r['id'],'source':r['file'],'sha256':digest(source),'quantity':1});continue
        if 'print_rotation' in r:
            t=np.eye(4);t[:3,:3]=r['print_rotation'];printed=mesh.copy();printed.apply_transform(t)
            shift=-printed.bounds[0];printed.apply_translation(shift);t[:3,3]=shift
            down=printed.face_normals[:,2]<-.707;elevated=printed.triangles_center[:,2]>.25
            overhang=float(printed.area_faces[down&elevated].sum());bed=float(printed.area_faces[down&~elevated].sum())
            pose={'assembly_to_print':t.tolist(),'bounds_mm':printed.extents.tolist(),'downward_area_mm2':overhang,
                  'bed_contact_area_mm2':bed,'supports_required':overhang>1,'brim_mm':3,'required_extruder_area_mm':[256,256]}
        record={'id':r['id'],'source':r['file'],'sha256':digest(source),'quantity':1,**pose};report['parts'].append(record)
        if pose['bed_contact_area_mm2']<1 or printed.extents[2]>260:blockers.append(r['id']+': no planar bed contact or exceeds build height')
        printed.apply_translation([128-printed.bounds.mean(axis=0)[0],128-printed.bounds.mean(axis=0)[1],0]);path=work/(r['id']+'-'+source.stem+'.stl');printed.export(path);inputs.append(str(path))
    # Consume the published manufacturing findings instead of guessing by layer name.
    validation=ROOT/('models/ams2pro+ht/validation.json' if key.startswith('ams2pro-ht/') else 'models/ams2pro/printing.json')
    report['validation_source']={'file':str(validation.relative_to(ROOT)),'sha256':digest(validation)}
    for failure in json.loads(validation.read_text()).get('printing_failures',[]):
        if any(Path(r['file']).stem.endswith(failure['part']) for r in rows):
            blockers.append(failure['part']+': '+', '.join(sorted({e['code'] for e in failure['errors']})))
    if key=='fit-check/interfaces' and not blockers:
        checks=[]
        for path,r in zip(inputs,report['parts']):
            result=subprocess.run(['cad','stl','dfm',path,'--process','printing','--technology','fdm','--material','petg',
                '--build-volume','256x256x260','--nozzle','.4','--layer-height','.2','--json'],capture_output=True,text=True)
            data=json.loads(result.stdout);checks.append({'id':r['id'],'source_sha256':r['sha256'],'status':data['status'],'findings':data['findings']})
            if data['status']!='ok':blockers.append(r['id']+': generic printing check failed')
        (dest/'printing-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    if blockers:
        for old in [dest/'x2d-04-petg.3mf',dest/'slice-info.xml',*dest.glob('plate_*.png')]:
            if old.exists():old.unlink()
        report.update(status='blocked',blockers=blockers);(dest/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(key,'BLOCKED',flush=True);return
    preset=OUT/'presets';process=json.loads((preset/'process.json').read_text())
    process.update(curr_bed_type='Textured PEI Plate',wall_loops='4',sparse_infill_density='20%',sparse_infill_pattern='gyroid',
                   enable_support='1' if any(r['supports_required'] for r in report['parts']) else '0',support_type='tree(auto)',brim_type='outer_only',brim_width='3')
    (work/'process.json').write_text(json.dumps(process,indent=2))
    report['preset_hashes']={p.name:digest(p) for p in preset.glob('*.json')}
    report['process_overrides']={k:process[k] for k in ['curr_bed_type','wall_loops','sparse_infill_density','sparse_infill_pattern','enable_support','support_type','brim_type','brim_width']}
    groups=[];small=None;x=y=8;row_height=0
    for path,r in zip(inputs,report['parts']):
        w,h,_=r['bounds_mm'];obj={'path':path,'count':1,'filaments':[1]}
        if max(w,h)>180:
            groups.append([obj]);continue
        if small is None:small=[];groups.append(small)
        if x+w>248:x=8;y+=row_height+10;row_height=0
        if y+h>248:small=[];groups.append(small);x=y=8;row_height=0
        obj.update(pos_x=[x+w/2-128],pos_y=[y+h/2-128])
        small.append(obj);x+=w+10;row_height=max(row_height,h)
    identifiers={path:r['id'] for path,r in zip(inputs,report['parts'])}
    assembly={'plates':[{'plate_name':f'{i+1:02d} '+', '.join(identifiers[o['path']] for o in group),
        'need_arrange':False,'objects':group} for i,group in enumerate(groups)]}
    (work/'assembly.json').write_text(json.dumps(assembly,indent=2))
    project=work/'project.3mf'
    if project.exists():project.unlink()
    code,log=run(['--load-settings',str(preset/'printer.json')+';'+str(work/'process.json'),'--load-filaments',str(preset/'filament-1.json'),
                 '--load-assemble-list',str(work/'assembly.json'),'--orient','0','--export-3mf','project.3mf'],work,'build.log')
    if code or not project.exists():raise RuntimeError((key,log[-1800:]))
    with zipfile.ZipFile(project) as z:content={n:z.read(n) for n in z.namelist()}
    settings=json.loads(content['Metadata/project_settings.config'])
    # Studio CLI exports empty nozzle lists; let Studio reconstruct them from the machine preset.
    for field in ['extruder_nozzle_stats','extruder_ams_count']:
        if settings.get(field)==[]:settings.pop(field)
    content['Metadata/project_settings.config']=json.dumps(settings).encode()
    target=dest/'x2d-04-petg.3mf'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in content.items():z.writestr(n,b)
    plates=[{'number':i+1,'name':p['plate_name'],'objects':[Path(o['path']).stem for o in p['objects']]} for i,p in enumerate(assembly['plates'])]
    report.update(status='arranged',plates=plates,project_sha256=digest(target))
    if slice_project:
        sliced=work/'sliced.3mf'
        if sliced.exists():sliced.unlink()
        code,log=run(['--slice','0','--export-3mf','sliced.3mf',str(target)],work,'slice.log')
        report['slice_exit_code']=code
        report['status']='slice_failed' if code or not (work/'sliced.3mf').exists() else 'sliced_not_printed'
        if report['status']=='slice_failed':report['slice_error']=log[-3000:]
        else:
            with zipfile.ZipFile(work/'sliced.3mf') as z:
                for n in z.namelist():
                    if n.startswith('Metadata/plate_') and n.endswith('.png') and '_small' not in n and 'no_light' not in n:(dest/Path(n).name).write_bytes(z.read(n))
                report['gcode_files']=[n for n in z.namelist() if n.endswith('.gcode')]
                assert len(report['gcode_files'])==len(plates),(key,'missing plate G-code')
                info=ET.fromstring(z.read('Metadata/slice_info.config'))
                assert all(o.get('skipped')!='true' for o in info.findall('.//object'))
                # Use the slicer's regenerated thumbnails, not the earlier project thumbnails.
                for n in z.namelist():
                    if n.startswith('Metadata/') and n.endswith('.png'):content[n]=z.read(n)
                settings=json.loads(z.read('Metadata/project_settings.config'))
                content['Metadata/project_settings.config']=json.dumps(settings).encode()
                (dest/'slice-info.xml').write_bytes(z.read('Metadata/slice_info.config'))
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in content.items():z.writestr(n,b)
    report['project_sha256']=digest(target)
    (dest/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(key,report['status'],len(plates),'plates',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--only');p.add_argument('--slice',action='store_true');a=p.parse_args()
    WORK.mkdir(parents=True,exist_ok=True)
    version=subprocess.run([STUDIO,'--help'],cwd=WORK,capture_output=True,text=True).stdout
    if not version.startswith('BambuStudio-02.09.01.70:'):raise SystemExit('Studio version changed; refresh presets and revalidate before rebuilding.')
    for key,rows in recipes():
        if a.only and a.only not in key:continue
        build(key,rows,a.slice)
