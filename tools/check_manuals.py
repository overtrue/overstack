"""Render every booklet page and check file counts, text bounds and image presence."""
from pathlib import Path
from ht_layers import LAYERS
import json,re
import pymupdf
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/pdf';OUT=ROOT/'output/manual-review';OUT.mkdir(parents=True,exist_ok=True)
books=sorted(D.glob('0*-assembly-*.pdf'))
assert {f.name for f in books}=={f'{slug}-assembly-{lang}.pdf' for _,slug,_ in LAYERS for lang in ['zh','en']}
thumbs=[]
for f in books:
 doc=pymupdf.open(f);assert len(doc)==3,f
 for i,p in enumerate(doc):
  assert len(p.get_text())>150,(f,i)
  assert len(p.get_images())>=1,(f,i)
  for block in p.get_text('dict')['blocks']:
   if block['type']!=0:continue
   for line in block['lines']:
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox'];assert x0>=0 and y0>=0 and x1<=p.rect.width+1 and y1<=p.rect.height+1,(f,i,span['text'])
  out=OUT/f'{f.stem}-{i+1}.png';p.get_pixmap(matrix=pymupdf.Matrix(1.15,1.15),alpha=False).save(out)
  if i==1:
   p.get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).save(ROOT/'docs/images'/f'{f.stem}.png')
  im=Image.open(out);im.thumbnail((400,283));tile=Image.new('RGB',(420,310),'#eeeeee');tile.paste(im,(10,5));ImageDraw.Draw(tile).text((10,291),f.stem+f' p{i+1}',fill='black');thumbs.append(tile)
part_ids={p['id'] for p in json.loads((ROOT/'models/ams2pro+ht/parts.json').read_text())}
for lang in ['zh','en']:
 with pymupdf.open(D/f'overstack-assembly-{lang}.pdf') as doc:
  assert len(doc)==len(LAYERS)+7
  assert set(re.findall(r'\b[A-Z]\d{2}\b',doc[-1].get_text()))==part_ids,('combined parts index',lang)
  for i,(prefix,_,_) in enumerate(LAYERS):
   assert prefix+' / ' in doc[3+i].get_text(),('combined layer page',lang,prefix)
for start in range(0,len(thumbs),12):
 sheet=Image.new('RGB',(1680,930),'white')
 for i,tile in enumerate(thumbs[start:start+12]):sheet.paste(tile,((i%4)*420,(i//4)*310))
 sheet.save(OUT/f'contact-{start//12+1}.png')
print('PASS: 10 standalone bilingual booklets, 30 pages, images and text bounds checked')
