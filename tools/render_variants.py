"""Render actual exported variants and highlight common ends; no equipment stand-ins."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_variants import scene
from geometry import *

OUT=ROOT/'output/variants';IMAGES=ROOT/'docs/images';jobs=[]


def save(key,parts,angle=(-55,25),size=(1600,1200)):
    path=OUT/(key+'.glb');scene(parts).export(path)
    verts=np.vstack([m.vertices for m in parts.values()]);target=(verts.min(axis=0)+verts.max(axis=0))/2
    az,el=np.radians(angle);forward=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.cross(-forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,-forward)
    coords=verts-target;half=max(np.ptp(coords@up)/2,np.ptp(coords@right)/(2*size[0]/size[1]))*1.15
    jobs.append({'key':key,'scene':str(path),'image':str(IMAGES/(key+'.png')),'width':size[0],'height':size[1],
                 'component_colors':True,'camera':{'position':(target+forward*1500).tolist(),'target':target.tolist(),
                 'up':[0,0,1],'orthographicHalfHeight':float(half)}})


report=json.loads((ROOT/'models/ams2pro/validation.json').read_text());plain={};peg={}
for layer in report['layers']:
    slug=layer['name'];parts={};exploded={}
    for r in json.loads((ROOT/'models/ams2pro'/slug/'parts.json').read_text()):
        m=move(trimesh.load_mesh(ROOT/r['file']),r['offset_mm']);name=r['name'];parts[name]=m
        plain[slug+'__'+name]=move(m,[0,0,layer['z_mm']])
        pg=move(trimesh.load_mesh(ROOT/r['file'].replace('_plain.stl','_pegboard.stl')),r['offset_mm']) if name.startswith('end_') else m
        peg[slug+'__'+name]=move(pg,[0,0,layer['z_mm']])
        shift=[0,0,0]
        if 'end_left' in name:shift=[-65,0,0]
        elif 'end_right' in name:shift=[65,0,0]
        elif 'front_beam' in name:shift=[0,-50,0]
        elif 'rear_beam' in name or 'lock' in name:shift=[0,60,0]
        elif 'divider' in name:shift=[0,0,40]
        elif 'drawer_' in name:shift=[0,-100,30]
        elif name=='top_1':shift=[-40,20,0]
        exploded[name]=move(m,shift)
    save('no-ht-'+slug+'-exploded',exploded)
save('no-ht-plain',plain)
save('no-ht-pegboard',peg)
common={}
for i,H in enumerate([40,60]):
    for j,style in enumerate(['plain','pegboard']):
        name=f'end_left_{H}_{style}';m=trimesh.load_mesh(ROOT/'models/common'/(name+'.stl'))
        common[name]=move(m,[j*115,0,i*110])
save('common-ends',common,angle=(-140,22))
aligned={}
z=0
for i,H in enumerate([40,60,40]):
    m=trimesh.load_mesh(ROOT/'models/common'/f'end_left_{H}_pegboard.stl')
    aligned[f'end_left_{H}_{i}']=move(m,[0,0,z]);z+=H
save('common-grid-alignment',aligned,angle=(180,0),size=(1600,900))
scene(aligned).export(ROOT/'models/common/straight-grid-stack.glb')
rows=json.loads((ROOT/'models/ams2pro+ht/parts.json').read_text());wide={}
heights=[0,40,100,160,220,280]
for r in rows:
    name=r['name'];m=trimesh.load_mesh(ROOT/'models/ams2pro+ht'/r['packaged_file'])
    if 'end_left' in name or 'end_right' in name:
        side='left' if 'end_left' in name else 'right';H=40 if r['layer']==0 else 60
        m=trimesh.load_mesh(ROOT/'models/common'/f'end_{side}_{H}_pegboard.stl')
    wide[name]=move(m,[0,0,heights[r['layer']]])
save('wide-pegboard',wide)
scene(wide).export(ROOT/'models/ams2pro+ht/overstack-pegboard.glb')
(OUT/'render-jobs.json').write_text(json.dumps(jobs,indent=2))
print('Prepared',len(jobs),'real-geometry scenes')
