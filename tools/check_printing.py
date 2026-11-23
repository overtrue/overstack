"""Optional generic FDM checks via text-to-cad; does not slice or print."""
from pathlib import Path
import sys,json,subprocess,concurrent.futures,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
from fabrication import orient,drawer_print_pose
from multi_drawers import orient_candidate
D=ROOT/'output/model';OUT=ROOT/'output/printing';OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((D/'checks.json').read_text());cad=shutil.which('cad')
if not cad:raise SystemExit('Install text-to-cad (cad) to run the optional manufacturing checks.')
unique={};placements=[]
for r in data['parts']:
    f=D/r['file'];sha=hashlib.sha256(f.read_bytes()).hexdigest()
    if sha in unique:
        placements.append({'name':r['name'],'same_geometry_as':unique[sha]['name']});continue
    m=trimesh.load_mesh(f)
    if r['name'].startswith(('standard_2_drawer_','3drawers_drawer_')):
        printed,placement=drawer_print_pose(m)
    else:
        try:printed,placement=orient(m)
        except AssertionError:printed,placement=orient_candidate(m)
    path=OUT/(r['name']+'.stl');printed.export(path)
    entry={'name':r['name'],'source_sha256':sha,'file':path.name,'placement':placement};unique[sha]=entry;placements.append(entry)

def check(r):
    path=OUT/r['file'];cmd=[cad,'stl','dfm',str(path),'--process','printing','--technology','fdm','--material','petg','--build-volume','256x256x260','--nozzle','0.4','--layer-height','0.2','--json']
    result=subprocess.run(cmd,capture_output=True,text=True)
    (OUT/(path.stem+'-dfm.json')).write_text(result.stdout)
    d=json.loads(result.stdout)
    row={**r,'status':d['status'],'warnings':sorted(set(f['code'] for f in d['findings'] if f['severity']=='warning')),'errors':[f for f in d['findings'] if f['severity']=='error']}
    print(path.name,result.returncode,flush=True)
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,unique.values()))
(OUT/'checks.json').write_text(json.dumps({'material':'PETG','process':'FDM','unique_parts':results,'all_parts':placements,'sliced':False,'physical_fit':'not_verified'},indent=2))
failed=[r for r in results if r['status']!='ok']
print('FAILED' if failed else 'PASS',len(results),'distinct parts;',len(failed),'failed; no slicing or load validation')
raise SystemExit(bool(failed))
