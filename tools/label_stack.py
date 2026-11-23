"""Label the current exploded render with layer names in both languages."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import trimesh
from package import LAYERS
job=next(j for j in json.loads((ROOT/'output/illustrations/jobs.json').read_text()) if j['key']=='stack-exploded')
rows=json.loads((ROOT/'models/ams2pro+ht/parts.json').read_text())
source=Image.open(job['image']).convert('RGBA');bbox=source.getbbox();crop=source.crop(bbox)
camera=job['camera'];eye=np.array(camera['position']);target=np.array(camera['target'])
forward=target-eye;forward/=np.linalg.norm(forward)
right=np.cross(forward,camera['up']);right/=np.linalg.norm(right);up=np.cross(right,forward)
scale=source.height/(2*camera['orthographicHalfHeight'])
anchors=[]
for layer in range(6):
    r=next(r for r in rows if r['layer']==layer and ('end_right' in r['name'] or r['name']=='device_adapter_2'))
    m=trimesh.load_mesh(ROOT/'models/ams2pro+ht'/r['packaged_file'])
    world=m.centroid+np.array([0,0,LAYERS[layer][2]+layer*75])
    v=world-target
    anchors.append((source.width/2+np.dot(v,right)*scale-bbox[0]+30,
                    source.height/2-np.dot(v,up)*scale-bbox[1]+30))
titles={'zh':['五槽打印板层','八槽打印板层','单抽屉层','双抽屉层','三抽屉层','设备顶件'],
        'en':['Five-slot plate layer','Eight-slot plate layer','Single-drawer layer','Double-drawer layer','Triple-drawer layer','Device top']}
for lang,names in titles.items():
    font_path='/System/Library/Fonts/STHeiti Medium.ttc' if lang=='zh' else '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    font=ImageFont.truetype(font_path,30)
    labels=[f'{chr(65+i)} · {name}' for i,name in enumerate(names)]
    label_width=int(max(font.getlength(t) for t in labels))+40
    canvas=Image.new('RGB',(crop.width+100+label_width,crop.height+60),'white')
    canvas.paste(crop,(30,30),crop);draw=ImageDraw.Draw(canvas);label_x=crop.width+85
    for (x,y),text in zip(anchors,labels):
        draw.line([(x,y),(label_x-18,y)],fill='#607e83',width=2)
        draw.ellipse((x-5,y-5,x+5,y+5),fill='#607e83',outline='white',width=2)
        draw.text((label_x,y),text,font=font,fill='#20343c',anchor='lm')
    path=ROOT/'docs/images'/f'stack-exploded-{lang}.png';canvas.save(path)
    print(path)
