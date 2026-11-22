"""Generate reproducible CAD scenes and illustrations for the two manuals."""
from pathlib import Path
import sys,json,subprocess,concurrent.futures,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from package import LAYERS
D=ROOT/'dist/stacknest-v54';OUT=ROOT/'output/illustrations';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images';IMAGES.mkdir(parents=True,exist_ok=True)
rows=json.loads((D/'parts.json').read_text())
meshes={r['id']:trimesh.load_mesh(D/r['packaged_file']) for r in rows}

def colored(r,m):
    m=m.copy();name=r['name'];color=[157,182,184,255]
    if 'end_' in name or 'device_adapter' in name:color=[205,211,215,255]
    if ('_drawer_' in name and 'cassette' not in name) or 'side_bin' in name:color=[204,181,145,255]
    if 'lock' in name:color=[213,128,66,255]
    m.visual.vertex_colors=color;return m

def save_scene(key,selected,offset,angle=(-55,26),width=1800,height=1250):
    scene=trimesh.Scene();allmeshes=[];centers={}
    for r in selected:
        m=colored(r,meshes[r['id']]);m.apply_translation(offset(r));allmeshes.append(m)
        centers[r['id']]=m.centroid.tolist()
        m.apply_scale(.001);m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));scene.add_geometry(m,node_name=r['id'])
    path=OUT/(key+'.glb');scene.export(path)
    vertices=np.vstack([m.vertices for m in allmeshes])*1000
    # Above meshes were transformed to glTF Y-up. Convert back for the camera calculation.
    vertices=vertices@trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])[:3,:3].T
    target=(vertices.min(axis=0)+vertices.max(axis=0))/2
    az,el=np.radians(angle);forward=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.cross(-forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,-forward)
    coords=vertices-target;half=max(np.ptp(coords@up)/2,np.ptp(coords@right)/(2*width/height))*1.12
    camera={'position':(target+forward*1600).tolist(),'target':target.tolist(),'up':[0,0,1], 'orthographicHalfHeight':float(half),'zoom':1}
    job={'key':key,'scene':str(path),'image':str(IMAGES/(key+'.png')),'camera':camera,'width':width,'height':height,'centers':centers,'ids':[r['id'] for r in selected]}
    return job

def exploding(r):
    n=r['name'];x=y=z=0
    if 'end_left' in n:x=-70
    elif 'end_right' in n:x=70
    elif 'cassette' in n:
        i=int(n.rsplit('_',1)[1]);x=-25 if i==1 else (25 if i==2 else 0);y=-60 if i==3 else (60 if i==4 else 0)
    elif 'side_left' in n:x=-25
    elif 'side_right' in n:x=25
    elif 'front_beam' in n:y=-60
    elif 'rear_beam' in n:y=60
    elif 'divider' in n:z=40
    elif 'lock' in n:y=100;z=10
    elif 'drawer' in n or 'side_bin' in n:y=-110;z=38
    if n=='standard_2_drawer_1':y=-170
    if n=='standard_2_drawer_2':y=-90
    if n=='device_adapter_1':x=-40;y=20
    return [x,y,z]

jobs=[save_scene('hero',rows,lambda r:[0,0,LAYERS[r['layer']][2]],width=1800,height=1250),
      save_scene('stack-exploded',rows,lambda r:[0,0,LAYERS[r['layer']][2]+r['layer']*75],angle=(-65,18),width=1450,height=1800)]
for group,(prefix,folder,z) in enumerate(LAYERS):
    selected=[r for r in rows if r['layer']==group]
    jobs.append(save_scene('layer-'+prefix.lower()+'-exploded',selected,exploding,width=1800,height=1200))
    jobs.append(save_scene('layer-'+prefix.lower()+'-assembled',selected,lambda r:[0,0,0],width=1600,height=1000))
jobs.append(save_scene('rail-detail',[r for r in rows if r['name']=='standard_1_cassette_plates_1'],lambda r:[0,0,0],angle=(35,35),width=1600,height=1000))
jobs.append(save_scene('drawer-joint',[r for r in rows if r['name'].startswith('standard_2_drawer_')],lambda r:([70,0,0] if r['name'].endswith('_1') else [0,0,0]),angle=(-65,-28),width=1600,height=1000))
locks=[r for r in rows if r['name'] in ['standard_1_end_left_1','standard_2_end_left_1','seam_2_False_layer_lock']]
jobs.append(save_scene('layer-lock-detail',locks,lambda r:([0,0,-60] if r['name']=='standard_1_end_left_1' else ([0,55,0] if 'lock' in r['name'] else [0,0,0])),angle=(130,20),width=1200,height=1200))
(OUT/'jobs.json').write_text(json.dumps(jobs,indent=2))
cad=shutil.which('cad')
if not cad:raise SystemExit('Install text-to-cad (cad) to render these CAD illustrations.')
def render(j):
    cmd=[cad,'glb','snapshot',j['scene'],j['image'],'--camera',json.dumps(j['camera']),'--display',json.dumps({'camera':{'projection':'orthographic'}}),'--width',str(j['width']),'--height',str(j['height'])]
    r=subprocess.run(cmd,capture_output=True,text=True);print(j['key'],r.returncode,flush=True)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(render,jobs))
print('Rendered',len(jobs),'CAD illustrations')
