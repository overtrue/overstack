"""Check the exact exported new parts in candidate PETG print orientations."""
from pathlib import Path
import sys,json,subprocess,concurrent.futures,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from fabrication import orient
from multi_drawers import orient_candidate


def check(row):
    source=ROOT/row['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
    mesh=trimesh.load_mesh(source)
    try:printed,pose=orient(mesh)
    except AssertionError:printed,pose=orient_candidate(mesh)
    key=row['name'].replace('/','__');folder=ROOT/'output/variants/printing';folder.mkdir(exist_ok=True)
    path=folder/(key+'.stl');printed.export(path)
    result=subprocess.run(['cad','stl','dfm',str(path),'--process','printing','--technology','fdm',
        '--material','petg','--build-volume','256x256x260','--nozzle','.4','--layer-height','.2','--json'],capture_output=True,text=True)
    (folder/(key+'.json')).write_text(result.stdout or result.stderr)
    data=json.loads(result.stdout)
    out={**row,'placement':pose,'status':data['status'],'errors':[f for f in data['findings'] if f['severity']=='error'],
         'warnings':sorted(set(f['code'] for f in data['findings'] if f['severity']=='warning'))}
    print(key,out['status'],[f['code'] for f in out['errors']],flush=True)
    return out


if __name__=='__main__':
    report=json.loads((ROOT/'models/no-ht/validation.json').read_text())
    rows=[r for r in report['parts'] if not r['name'].endswith('_plain') and not r['name'].startswith('lock_')]
    previous=ROOT/'models/no-ht/printing.json'
    cached={r['sha256']:r for r in json.loads(previous.read_text())['parts']} if previous.exists() else {}
    changed=[r for r in rows if r['sha256'] not in cached or cached[r['sha256']]['status']!='ok']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:updated=list(pool.map(check,changed))
    cached.update({r['sha256']:r for r in updated})
    results=[{**cached[r['sha256']],**r} for r in rows]
    (ROOT/'models/no-ht/printing.json').write_text(json.dumps({'material':'PETG','process':'FDM','nozzle_mm':.4,
        'layer_mm':.2,'parts':results,'sliced':False,'physical_fit':'not_verified'},indent=2)+'\n')
    failed=[r for r in results if r['status']!='ok']
    print(len(results),'exported parts;',len(failed),'failed')
    raise SystemExit(bool(failed))
