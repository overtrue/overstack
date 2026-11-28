"""One manifest supplies compact diagram callouts and README download rows."""
from pathlib import Path
import json,sys,os,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_variants import scene,LABELS
from geometry import *

OUT=ROOT/'output/numbered';OUT.mkdir(exist_ok=True);jobs=[]
LAYERS=['5-slot-plate-layer','8-slot-plate-layer','1-drawer-layer','2-drawer-layer','device-top']


for index,slug in enumerate(LAYERS):
    folder=ROOT/'models/ams2pro'/slug;manifest=folder/'parts.json';rows=json.loads(manifest.read_text());parts={}
    for i,r in enumerate(rows,1):
        r['id']=f'N{chr(65+index)}{i:02d}';r['label']=LABELS[r['name']]
        m=move(trimesh.load_mesh(ROOT/r['file']),r['offset_mm']);name=r['name'];shift=[0,0,0]
        if name.startswith('end_'):shift=[-100 if 'left' in name else 100,0,0]
        elif name.startswith('lock_'):shift=[-25 if 'left' in name else 25,110,40]
        elif name.startswith('front_beam'):shift=[-25 if name.endswith('_1') else 25,-75,0]
        elif name.startswith('rear_beam'):shift=[-25 if name.endswith('_1') else 25,75,0]
        elif name.startswith('divider'):shift=[0,0,100]
        elif name.startswith('drawer_half'):shift=[0,-180 if name.endswith('_1') else -70,70]
        elif name.startswith('drawer_'):shift=[-20 if name.endswith('_1') else 20,-150,70]
        elif name.startswith('top_'):shift=[-35 if name.endswith('_1') else 35,0,0]
        elif 'left' in name:shift=[-20,0,0]
        elif 'right' in name:shift=[20,0,0]
        parts[name]=move(m,shift)
    az,el=np.radians([-55,32]);forward=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.cross(-forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,-forward)
    # Separate projected bounds, so a leader cannot appear to land on a part
    # hiding its real target. Only diagram placements change, never STL geometry.
    def bounds(m):
        xy=np.c_[m.vertices@right,m.vertices@up];return np.array([xy.min(axis=0),xy.max(axis=0)])
    names=list(parts)
    for iteration in range(400):
        moved=False
        for i,a in enumerate(names):
            for b in names[i+1:]:
                aa=bounds(parts[a]);bb=bounds(parts[b]);penetration=np.minimum(aa[1],bb[1])-np.maximum(aa[0],bb[0])+16
                if np.all(penetration>0):
                    axis=int(np.argmin(penetration));sign=1 if aa[:,axis].mean()>=bb[:,axis].mean() else -1
                    delta=(right if axis==0 else up)*sign*(penetration[axis]/2+.1)
                    parts[a]=move(parts[a],delta);parts[b]=move(parts[b],-delta);moved=True
        if not moved:break
    else:raise AssertionError('Exploded diagram did not separate')
    path=OUT/(slug+'.glb');scene(parts).export(path)
    verts=np.vstack([m.vertices for m in parts.values()]);target=(verts.min(axis=0)+verts.max(axis=0))/2
    coords=verts-target;labels=[]
    boxes=[bounds(m)-np.array([target@right,target@up]) for m in parts.values()]
    for row_index,r in enumerate(rows):
        m=parts[r['name']];visible=m.face_normals@forward>.2
        face=np.argmax(np.where(visible,m.area_faces,0));anchor=m.triangles_center[face]
        v=anchor-target;point=np.array([v@right,v@up]);candidates=[]
        for radius in range(35,436,25):
            for angle in np.radians(np.arange(0,360,30)):
                pos=point+radius*np.array([np.cos(angle),np.sin(angle)])
                if any(np.all(pos+[28,13]>box[0]) and np.all(pos-[28,13]<box[1]) for box in boxes):continue
                if any(abs(pos[0]-q['position_mm'][0])<58 and abs(pos[1]-q['position_mm'][1])<28 for q in labels):continue
                line=point+(pos-point)*np.linspace(0,1,80)[:,None]
                crosses=any(np.any(np.all((line>box[0])&(line<box[1]),axis=1)) for k,box in enumerate(boxes) if k!=row_index)
                if not crosses:candidates.append((radius,pos.copy()))
            if candidates:break
        assert candidates,('No clear callout position',r['id'])
        pos=min(candidates,key=lambda p:p[0])[1]
        labels.append({'id':r['id'],'name':r['name'],'anchor_mm':anchor.tolist(),'position_mm':pos.tolist()})
    projected=np.c_[coords@right,coords@up]
    marks=np.array([q['position_mm'] for q in labels]);extent=np.vstack([projected,marks+np.array([30,15]),marks-np.array([30,15])])
    half=max(abs(extent[:,1]).max(),abs(extent[:,0]).max()/(1600/1200))*1.12
    jobs.append({'key':slug,'scene':str(path),'image':str(folder/'parts-numbered.png'),'width':1600,'height':1200,
                 'component_colors':True,'labels':labels,'camera':{'position':(target+forward*1800).tolist(),'target':target.tolist(),
                 'up':[0,0,1],'orthographicHalfHeight':float(half)}})
    manifest.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    p=folder/'README.md';text=p.read_text();start=text.index('| 编号 / ID |') if '| 编号 / ID |' in text else text.index('| Part |');end=text.index('\n\n',start)
    table='| 编号 / ID | 零件 | STL | X offset |\n| --- | --- | --- | ---: |\n'
    for r in rows:
        download=r.get('print_file',r['file'])
        offset='见装配清单 / see BOM' if 'print_file' in r else f'{r["offset_mm"][0]} mm'
        table+=f'| [{r["id"]}]({os.path.relpath(ROOT/download,folder)}) | {r["label"]} | `{Path(download).name}` | {offset} |\n'
    text=text[:start]+table.rstrip()+text[end:]
    text=re.sub(r'!\[Exploded view\]\([^\n]+\)',
        '![带编号的爆炸图 / Numbered exploded view](parts-numbered.png)\n\n编号与下表一一对应；左右以面对入口为准。爆炸图只用于辨认零件，不代表装入方向。\n\nMatch each callout to its table row. Left/right are viewed from the front. Exploded positions identify parts, not insertion directions.',text)
    p.write_text(text)
(OUT/'jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
print('Prepared',sum(len(j['labels']) for j in jobs),'unique part callouts')
