"""Check the actual oriented meshes used by each print profile, with a per-pose cache."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import trimesh
from print_profile_targets import TARGETS


def check(printer=None,only=None):
    cache=ROOT/'output/profile-printing-checks';cache.mkdir(exist_ok=True)
    failed=[]
    for key,target in TARGETS.items():
        if printer and key!=printer:continue
        for manifest in sorted((ROOT/'print-profiles'/key).glob('*/*/manifest.json')):
            report=json.loads(manifest.read_text())
            if only and only!=report['profile']:continue
            assert report['status']=='sliced_not_printed',(manifest,report['status'])
            checks=[];x0,y0,x1,y1=target['area'];volume=f"{x1-x0}x{y1-y0}x{target['height']}"
            for part in report['parts']:
                path=ROOT/'output/print-profiles'/key/report['profile']/(part['id']+'-'+Path(part['source']).stem+'.stl')
                mesh=trimesh.load_mesh(path);mesh.apply_translation(-mesh.bounds[0]);data=mesh.export(file_type='stl')
                sha=hashlib.sha256(data+volume.encode()).hexdigest();result=cache/(sha+'.json')
                if not result.exists():
                    local=cache/(sha+'.stl');local.write_bytes(data)
                    run=subprocess.run(['cad','stl','dfm',str(local),'--process','printing','--technology','fdm','--material','petg',
                        '--build-volume',volume,'--nozzle','.4','--layer-height','.2','--json'],capture_output=True,text=True)
                    parsed=json.loads(run.stdout);result.write_text(json.dumps(parsed,indent=2)+'\n')
                parsed=json.loads(result.read_text())
                row={'id':part['id'],'source_sha256':part['sha256'],'assembly_to_print':part['assembly_to_print'],
                     'status':parsed['status'],'errors':[f for f in parsed['findings'] if f['severity']=='error'],
                     'warnings':sorted({f['code'] for f in parsed['findings'] if f['severity']=='warning'})}
                checks.append(row)
                if parsed['status']!='ok':failed.append({'printer':key,'profile':report['profile'],**row})
            (manifest.parent/'layout-printing-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
            print(key,report['profile'],'checked',len(checks),'parts',flush=True)
    (cache/'failures.json').write_text(json.dumps(failed,indent=2)+'\n')
    print('FAIL' if failed else 'PASS',len(failed),'manufacturing failures',flush=True)
    return failed


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--printer',choices=TARGETS);parser.add_argument('--only');args=parser.parse_args()
    raise SystemExit(bool(check(args.printer,args.only)))
