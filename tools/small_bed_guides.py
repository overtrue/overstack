"""Build the 256 mm assembly previews, per-layer lists and the F06 corner detail."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from build_print_profiles import canonical_recipes
from build_variants import scene
from corner_pins import centre
from geometry import box,intersection,move,np,trimesh
OUT=ROOT/'output/small-illustrations';OUT.mkdir(exist_ok=True)
jobs=[]

for key,parents in canonical_recipes():
    if not key.startswith(('ams2pro/','ams2pro-ht/')):continue
    folder=ROOT/'models/256'/key;rows=json.loads((folder/'parts.json').read_text())
    original={r['id']:r for r in parents};assembled={};display={};pin_anchors={}
    guide=['# '+key+' · 256 mm','','先将同编号的前段 a 与后段 b 错开高度，对准燕尾后竖直合拢。图中前段为青色，后段为浅灰色。J 是整根横梁。','',
           'Match the number, align the front (a) and rear (b) tails, then lower one section into the other. Front sections are teal and rear sections light grey. J identifies a one-piece beam.','',
           '![拆件图 / Cut parts](preview.png)','','[装配模型 / Assembly](layer-assembly.glb)','','| 打印编号 / Print ID | 装配编号 / Assembly ID | STL |','| --- | --- | --- |']
    for row in rows:
        ident=row['id'];ids=row.get('parent_ids',[ident]);parent=original[ids[0]]
        off=parent.get('offset_mm',[0,0,0])
        mesh=move(trimesh.load_mesh(ROOT/row['file']),off);assembled[ident]=mesh
        src=Path(parent['file']).stem
        x=mesh.centroid[0];width=399 if key.startswith('ams2pro/') else 495
        dx=(-42 if x<width/2 else 42) if 'end_' in src else 0
        dy=(-40 if 'front_beam' in src else 38 if 'rear_beam' in src else -48 if '_drawer_' in '_'+src else 0)
        dz=0
        style='body'
        if 'parent_ids' in row and len(ids)==1:
            front=ident.endswith('a');dy+=-28 if front else 28;dz=9 if front else 0;style='front' if front else 'rear'
        if key=='ams2pro-ht/06-device-top':
            if ids==['F01']:dx=-22
            if ident in ('F02','F05'):
                dy=-28 if ident=='F02' else 28;style='front' if ident=='F02' else 'rear'
        if 'lock' in src:dy+=58;style='pin'
        if 'ht_foot_' in src:
            dy=-28 if ident=='F06' else 28;dz=-35;style='pin'
        shown=move(mesh,[dx,dy,dz]);display[ident+'__'+style]=shown
        if 'ht_foot_' in src:pin_anchors[ident]=shown.centroid
        import os
        link=os.path.relpath(ROOT/row.get('print_file',row['file']),folder)
        guide.append(f"| {ident} | {', '.join(ids)} | [{Path(link).name}]({link}) |")
    (folder/'README.md').write_text('\n'.join(guide)+'\n')
    scene(assembled).export(folder/'layer-assembly.glb')
    assert set(trimesh.load(folder/'layer-assembly.glb').graph.nodes_geometry)==set(assembled)
    tag=key.replace('/','-');path=OUT/(tag+'.glb');scene(display).export(path)
    vertices=np.vstack([p.vertices for p in display.values()]);target=(vertices.min(axis=0)+vertices.max(axis=0))/2
    az,el=np.radians([-62,35]);forward=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.cross(-forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,-forward)
    coords=vertices-target;half=max(np.ptp(coords@up)/2,np.ptp(coords@right)/3)*1.12
    jobs.append({'key':tag,'scene':str(path),'image':str(folder/'preview.png'),'width':1050,'height':700,
                 'split_colors':True,'camera':{'position':(target+forward*1600).tolist(),'target':target.tolist(),
                                              'up':[0,0,1],'orthographicHalfHeight':float(half)}})
    if pin_anchors:
        jobs[-1]['labels']=[]
        for ident,anchor in pin_anchors.items():
            delta=anchor-target
            x=np.clip(delta@right+24,-1.5*half+29,1.5*half-29)
            y=np.clip(delta@up-18,-half+14,half-14)
            jobs[-1]['labels'].append({'id':ident,'anchor_mm':anchor.tolist(),'position_mm':[x,y]})
(OUT/'jobs.json').write_text(json.dumps(jobs,indent=2))

# A true section through the centre of the marked HT front pin (F06/n5).
parts=ROOT/'models/ams2pro+ht/06-device-top/parts'
upper=trimesh.load_mesh(next(parts.glob('F02-*.stl')))
pin=trimesh.load_mesh(next(parts.glob('F06-*.stl')))
end=move(trimesh.load_mesh(ROOT/'models/common/end_right_60_plain.stl'),[0,0,-60])
cx,cy=centre(True,False);crop=box(cx-10,cy-.1,-8,20,.2,21)
im=Image.new('RGB',(1440,690),'#f4f4ef');draw=ImageDraw.Draw(im)
def font(size):
    return ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',size)
def section(mesh,ax,ay,scale,fill):
    part=intersection(mesh,crop)
    cross=part.section(plane_origin=[cx,cy,0],plane_normal=[0,1,0])
    for loop in sorted(cross.discrete,key=lambda a:-Polygon(a[:,[0,2]]).area):
        pts=[(ax+(x-cx)*scale,ay-z*scale) for x,y,z in loop]
        draw.polygon(pts,fill=fill,outline='#253839',width=2)
draw.text((52,34),'F06 / F07   层间圆柱定位销',font=font(43),fill='#203838')
draw.text((54,106),'AMS HT 侧前后共用  ·  Ø6 × 6.4 mm',font=font(28),fill='#355f61')
# Crop the ends and socket separately so the dowel and conical roof are visible.
section(end,407,450,21,'#a9b4b2');section(upper,407,450,21,'#77a2a1');section(move(pin,[0,0,-.5]),407,450,21,'#e59a53')
draw.text((166,635),'通过销轴的装配剖面',font=font(25),fill='#345252')
for anchor,yy,label in [((443,340),222,'顶件下侧盲孔，45° 收顶'),((464,396),383,'圆销两端 0.4 mm 倒角'),((484,523),519,'下层孔深 3.5 mm')]:
    draw.line([anchor,(615,yy+14),(660,yy+14)],fill='#304b4a',width=2)
    x,y=anchor;draw.ellipse((x-4,y-4,x+4,y+4),fill='#304b4a')
    draw.text((686,yy-3),label,font=font(29),fill='#203838')
draw.text((731,621),'先放圆销，再落顶件。',font=font(24),fill='#426462')
im.save(ROOT/'docs/images/corner-dowel-section.png')
