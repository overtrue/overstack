"""Slice the approved 256 mm layouts a second time with the official PETG Matte preset."""
import argparse,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from build_print_profiles import ROOT,digest,run
from print_profile_targets import TARGETS
from print_slice_metrics import metrics


def model_payload(data):
    return re.sub(rb'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',b'uuid',data)


def build(printer,folder):
    report=json.loads((folder/'manifest.json').read_text());profile=report['profile']
    assert report['status']=='sliced_not_printed'
    base=folder/report['project_file'];assert digest(base)==report['project_sha256']
    preset=ROOT/'print-profiles'/printer/'presets'
    material=preset/'filament-matte.json';settings=json.loads(material.read_text())
    assert settings['filament_id']=='GFG03' and settings['compatible_printers']==[TARGETS[printer]['printer']+' 0.4 nozzle']
    job=ROOT/'output/print-profiles'/printer/profile
    work=job/'matte';work.mkdir(exist_ok=True)
    assembly=job/'assembly.json'
    # The baseline file and this export must contain exactly the same objects
    # and transforms. Studio alone applies the different filament preset.
    raw=work/'raw.3mf';sliced=work/'sliced.3mf'
    target=folder/(printer+'-04-petg-matte.3mf')
    evidence=folder/'matte-slice.json'
    if evidence.exists() and target.exists() and sliced.exists():
        previous=json.loads(evidence.read_text())
        if (previous['base_project_sha256']==digest(base) and previous['filament_preset_sha256']==digest(material)
                and previous['project_sha256']==digest(target)):
            print(printer,profile,'Matte already sliced',flush=True)
            return
    for path in (raw,sliced):path.unlink(missing_ok=True)
    args=['--load-settings',str(preset/'printer.json')+';'+str(job/'process.json'),
          '--load-filaments',str(material),'--load-assemble-list',str(assembly),'--orient','0','--export-3mf',raw.name]
    code,log=run(args,work,'build.log');assert code==0 and raw.exists(),log[-900:]
    with zipfile.ZipFile(raw) as z:data={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(base) as z:
        for name in z.namelist():
            if not name.startswith('3D/') or not name.endswith('.model'):continue
            assert model_payload(z.read(name))==model_payload(data[name]),(profile,name,'matte geometry differs')
    cfg=json.loads(data['Metadata/project_settings.config'])
    for k in ('extruder_nozzle_stats','extruder_ams_count'):
        if cfg.get(k)==[]:cfg.pop(k)
    data['Metadata/project_settings.config']=json.dumps(cfg).encode()
    def write(path):
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as out:
            for n,b in data.items():out.writestr(n,b)
    arranged=work/'arranged.3mf';write(arranged)
    code,log=run(['--slice','0','--export-3mf',sliced.name,str(arranged)],work,'slice.log')
    assert code==0 and sliced.exists(),(profile,log[-1500:])
    paths=[];x0,y0,x1,y1=TARGETS[printer]['area']
    with zipfile.ZipFile(sliced) as z:
        cfg=json.loads(z.read('Metadata/project_settings.config'))
        assert cfg['filament_ids']==['GFG03'] and 'PETG Matte' in cfg['filament_settings_id'][0],(profile,cfg['filament_ids'],cfg['filament_settings_id'])
        for k in ['filament_density','filament_max_volumetric_speed','nozzle_temperature','textured_plate_temp']:
            # Studio resolves the first extrusion mode in the arranged project.
            assert float(cfg[k][0])==float(settings[k][0]),(profile,k,cfg[k],settings[k])
        info=ET.fromstring(z.read('Metadata/slice_info.config'))
        assert len(info.findall('plate'))==len(report['plates'])
        assert len(info.findall('.//object'))==len(report['parts']) and not any(o.get('skipped')=='true' for o in info.findall('.//object'))
        for p in report['plates']:
            name='Metadata/plate_'+str(p['number'])+'.gcode';gcode=z.read(name)
            assert b'; filament_ids = GFG03' in gcode and TARGETS[printer]['printer'].encode() in gcode
            bounds=json.loads(z.read(name.replace('.gcode','.json')))['bbox_all']
            assert bounds[0]>=x0 and bounds[1]>=y0 and bounds[2]<=x1 and bounds[3]<=y1,(profile,bounds)
            paths.append({'plate':p['number'],'gcode_sha256':hashlib.sha256(gcode).hexdigest(),'bounds_mm':bounds})
        data['Metadata/project_settings.config']=json.dumps(cfg).encode()
        for n in z.namelist():
            if n.startswith('Metadata/') and n.endswith('.png'):data[n]=z.read(n)
    write(target)
    result={'base_project_sha256':digest(base),'filament_preset_sha256':digest(material),
            'filament':settings['name'],'filament_id':'GFG03','density_g_cm3':float(settings['filament_density'][0]),
            'project_file':target.name,'project_sha256':digest(target),'gcode':paths,
            'metrics':metrics(sliced,density=float(settings['filament_density'][0])),'physical_print':'not_verified'}
    (folder/'matte-slice.json').write_text(json.dumps(result,indent=2)+'\n')
    print(printer,profile,result['metrics']['hours'],result['metrics']['support_g'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--printer',choices=('x2d','p2s'),required=True);parser.add_argument('--only')
    args=parser.parse_args();base=ROOT/'print-profiles'/args.printer
    for f in sorted(base.glob('*/*/manifest.json')):
        if args.only and str(f.parent.relative_to(base))!=args.only:continue
        build(args.printer,f.parent)
