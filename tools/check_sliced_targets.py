"""Check actual G-code metadata for every printer profile."""
from pathlib import Path
import argparse,hashlib,json,zipfile
from print_profile_targets import TARGETS
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--printer',choices=TARGETS);parser.add_argument('--only');args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for key,target in TARGETS.items():
    if args.printer and key!=args.printer:continue
    base=ROOT/'print-profiles'/target['folder']
    for p in sorted(base.glob('*/*/manifest.json')):
        report=json.loads(p.read_text())
        if args.only and args.only!=report['profile']:continue
        if report['status']!='sliced_not_printed':continue
        project=p.parent/report.get('project_file',key+'-04-petg.3mf');assert sha(project)==report['project_sha256']
        sliced=ROOT/'output/print-profiles'/target['folder']/report['profile']/'sliced.3mf'
        result={'printer':target['printer'],'project_sha256':sha(project),'sliced_archive_sha256':sha(sliced),'plates':[]}
        with zipfile.ZipFile(project) as z:settings=json.loads(z.read('Metadata/project_settings.config'))
        with zipfile.ZipFile(sliced) as z:
            assert set(report['gcode_files'])=={n for n in z.namelist() if n.endswith('.gcode')}
            for name in report['gcode_files']:
                plate=json.loads(z.read(name.replace('.gcode','.json')))
                bounds=plate['bbox_all'];x0,y0,x1,y1=target['area']
                assert bounds[0]>=x0 and bounds[1]>=y0 and bounds[2]<=x1 and bounds[3]<=y1,(p,name,'outside target nozzle area',bounds)
                data=z.read(name);meta={}
                for line in data.decode().splitlines():
                    if line.startswith('; ') and ' = ' in line:
                        k,v=line[2:].split(' = ',1);meta[k]=v
                assert meta['printer_model']==target['printer'],(p,name,'wrong G-code printer')
                assert meta['filament_type']=='PETG' and meta['filament_ids']=='GFG00',(p,name,'wrong filament')
                for field in ['nozzle_diameter','nozzle_temperature','nozzle_temperature_initial_layer','textured_plate_temp','textured_plate_temp_initial_layer']:
                    actual=[float(x) for x in meta[field].split(',')]
                    expected=[float(x) for x in settings[field]]
                    assert actual==expected,(p,name,field,actual,expected)
                assert all(float(x)==.4 for x in meta['nozzle_diameter'].split(','))
                result['plates'].append({'file':name,'sha256':hashlib.sha256(data).hexdigest(),
                    'bbox_xy_mm':bounds,'first_extruder':plate['first_extruder'],
                    'printer_model':meta['printer_model'],'filament_type':meta['filament_type'],
                    'nozzle_diameter':meta['nozzle_diameter'],'nozzle_temperature':meta['nozzle_temperature'],
                    'bed_temperature':meta['textured_plate_temp'],'filament_map':meta.get('filament_map')})
        (p.parent/'slice-validation.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PASS G-code:',key,report['profile'],len(result['plates']),'plates')
