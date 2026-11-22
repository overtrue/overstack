"""Prepare softly lit assembled previews for each browsable model directory."""
from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_variants import scene
from geometry import *

OUT=ROOT/'output/previews';OUT.mkdir(exist_ok=True)
jobs=[];wide={}


def prepare(folder,parts):
    key=str(folder.relative_to(ROOT/'models')).replace('/','-')
    path=OUT/(key+'.glb');scene(parts).export(path)
    vertices=np.vstack([m.vertices for m in parts.values()]);target=(vertices.min(axis=0)+vertices.max(axis=0))/2
    az,el=np.radians([-55,25]);forward=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.cross(-forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,-forward)
    coords=vertices-target;half=max(np.ptp(coords@up)/2,np.ptp(coords@right)/(2*1600/1200))*1.15
    jobs.append({'key':key,'scene':str(path),'image':str(folder/'preview.png'),'width':1600,'height':1200,
                 'component_colors':True,'camera':{'position':(target+forward*1500).tolist(),'target':target.tolist(),
                 'up':[0,0,1],'orthographicHalfHeight':float(half)}})


rows=json.loads((ROOT/'models/ams2pro+ht/parts.json').read_text())
for index,folder in enumerate(sorted((ROOT/'models/ams2pro+ht').glob('0*'))):
    parts={r['name']:trimesh.load_mesh(ROOT/'models/ams2pro+ht'/r['packaged_file']) for r in rows if r['layer']==index}
    prepare(folder,parts)
    wide.update({n:move(m,[0,0,[0,40,100,160,220,280][index]]) for n,m in parts.items()})
prepare(ROOT/'models/ams2pro+ht',wide)
for manifest in sorted((ROOT/'models/ams2pro').glob('*/parts.json')):
    parts={r['name']:move(trimesh.load_mesh(ROOT/r['file']),r['offset_mm']) for r in json.loads(manifest.read_text())}
    prepare(manifest.parent,parts)
for folder,source in [('ams2pro','no-ht-pegboard.png'),('common','common-ends.png')]:
    shutil.copy2(ROOT/'docs/images'/source,ROOT/'models'/folder/'preview.png')
(OUT/'jobs.json').write_text(json.dumps(jobs,indent=2))
print('Prepared',len(jobs),'renders; reused two matching previews')
