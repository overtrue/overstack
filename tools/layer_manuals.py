"""One self-contained Chinese and English assembly guide per layer."""
from manual import *
from reportlab.pdfgen import canvas
for lang in ['zh','en']:
 for i,(prefix,slug,_) in enumerate(LAYERS):
  b=Book(lang);z=b.zh;title=(TITLES_ZH if z else TITLES_EN)[i]
  b.path=PDF/f'{slug}-assembly-{lang}.pdf';b.c=canvas.Canvas(str(b.path),pagesize=(W,H),pageCompression=1);b.c.setTitle('Overstack / '+title);b.c.setAuthor('overtrue')
  b.start(prefix+' / '+title,'LAYER ASSEMBLY')
  b.image('layer-'+prefix.lower()+'-assembled',35,185,520,310)
  b.text('Overstack' if z else 'Overstack',585,470,18,True)
  b.para(('本册只介绍本层的零件、装配与检查。' if z else 'This booklet covers this layer: its parts, assembly and checks.'),585,430,215,12)
  b.para(('先去毛边，再空载试配。不要敲入燕尾或导轨。' if z else 'Deburr first and dry-fit without load. Do not hammer dovetails or guides.'),585,350,215,11)
  group=[r for r in PARTS if r['layer']==i]
  for j,r in enumerate(group):
   col=j%3;row=j//3;b.text(r['id']+'  '+(r['label'] if z else EN_LABEL[r['label']]),42+col*245,167-row*13,9)
  b.note('数字样机；尚未实物试装。STL单位毫米，3MF仅含装配几何，尚未摆盘切片。' if z else 'digital prototype; physical fit untested. STL units: mm. 3MF contains assembly geometry only, not a sliced job.');b.end()
  b.start('装配顺序' if z else 'Assembly sequence')
  b.image('layer-'+prefix.lower()+'-exploded',30,130,552,373,labels=True)
  b.steps((STEPS_ZH if z else STEPS_EN)[i],top=484)
  b.note('按编号匹配零件。爆炸位置用于辨认，不代表实际装入方向；按右侧步骤操作。' if z else 'Match part IDs to filenames. Exploded positions identify parts, not insertion paths; follow the steps on the right.');b.end()
  b.start('连接、使用与检查' if z else 'Connections, use and checks')
  key='rail-detail' if i<2 else ('layer-f-assembled' if prefix=='F' else 'layer-lock-detail')
  b.image(key,35,150,480,345)
  use=(STEPS_ZH if z else STEPS_EN)[i][-1]
  steps=[use,('连接相邻层','圆柱定位销对准槽后竖直落座。每条层缝用两片相同的蝴蝶锁片，从后方插入，左右、上下通用。') if z else ('Connect neighbouring layers','Align the round corner pins and lower vertically. Insert two identical bowties from behind. Either fits either side, either end up.'),('验收本层','确认四角落座、连接到位、抽拉无卡滞。后横梁与锁片没有防丢锁止；实物配合、设备净空和承重仍需验证。') if z else ('Check this layer','Check seating, joints and free movement. Rear beams and keys are not captive. Physical fit, device clearance and load capacity still need testing.')]
  b.steps(steps,x=550,top=481,width=250)
  if prefix in ['B','D','E']:
   b.para('抽屉底板为2 mm实心板。' if z else 'Drawers use 2 mm solid floors.',42,118,755,10)
  b.note('PETG/FDM检查通过；仍有悬垂、桥接等提示。尚无实物验证。' if z else 'PETG/FDM checks pass; overhang and bridge warnings remain. Physical fit is untested.');b.end();b.save();print(b.path.name)
