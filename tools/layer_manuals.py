"""One self-contained Chinese and English assembly guide per layer."""
from manual import *
from reportlab.pdfgen import canvas
SLUGS=['three-slot-plate-layer','eight-slot-plate-layer','single-drawer-layer','double-drawer-layer','triple-drawer-layer','device-top']
for lang in ['zh','en']:
 for i,slug in enumerate(SLUGS):
  b=Book(lang);z=b.zh;prefix=chr(65+i);title=(TITLES_ZH if z else TITLES_EN)[i]
  b.path=PDF/f'{i+1:02d}-{slug}-assembly-{lang}.pdf';b.c=canvas.Canvas(str(b.path),pagesize=(W,H),pageCompression=1);b.c.setTitle('StackNest / '+title+' / V55');b.c.setAuthor('overtrue')
  b.start(prefix+' / '+title,'LAYER ASSEMBLY')
  b.image('layer-'+prefix.lower()+'-assembled',35,185,520,310)
  b.text('叠序 StackNest' if z else 'StackNest',585,470,18,True)
  b.para(('本册只介绍本层的零件、装配与检查。' if z else 'This booklet covers this layer: its parts, assembly and checks.'),585,430,215,12)
  b.para(('先去毛边，再空载试配。不要敲入燕尾或导轨。' if z else 'Deburr first and dry-fit without load. Do not hammer dovetails or guides.'),585,350,215,11)
  group=[r for r in PARTS if r['layer']==i]
  for j,r in enumerate(group):
   col=j%3;row=j//3;b.text(r['id']+'  '+(r['label'] if z else EN_LABEL[r['label']]),42+col*245,167-row*13,9)
  b.note('V55数字样机；尚未实物试装。STL单位毫米，3MF仅含装配几何，尚未摆盘切片。' if z else 'V55 digital prototype; physical fit untested. STL units: mm. 3MF contains assembly geometry only, not a sliced job.');b.end()
  b.start('装配顺序' if z else 'Assembly sequence')
  b.image('layer-'+prefix.lower()+'-exploded',30,130,552,373,labels=True)
  b.steps((STEPS_ZH if z else STEPS_EN)[i],top=484)
  b.note('按编号匹配零件。爆炸位置用于辨认，不代表实际装入方向；按右侧步骤操作。' if z else 'Match part IDs to filenames. Exploded positions identify parts, not insertion paths; follow the steps on the right.');b.end()
  b.start('连接、使用与检查' if z else 'Connections, use and checks')
  key='rail-detail' if i<2 else ('drawer-joint' if i==2 else ('layer-f-assembled' if i==5 else 'layer-lock-detail'))
  b.image(key,35,150,480,345)
  use=(STEPS_ZH if z else STEPS_EN)[i][-1]
  steps=[use,('连接相邻层','弧形底脚对准槽后竖直落座。每条层缝装左右两枚锁片，从后向前推入；锁片可向后退出。') if z else ('Connect neighbouring layers','Align the curved feet and lower vertically. Insert the two seam keys from behind. Keys can slide out rearward.'),('验收本层','确认四角落座、连接到位、抽拉无卡滞。后横梁与锁片没有防丢锁止；实物配合、设备净空和承重仍需验证。') if z else ('Check this layer','Check seating, joints and free movement. Rear beams and keys are not captive. Physical fit, device clearance and load capacity still need testing.')]
  b.steps(steps,x=550,top=481,width=250)
  if i in [1,2,3,4]:
   b.para('抽屉底板为2 mm实心板，拼接与滑轨接口保留。' if z else 'Drawers use 2 mm solid floors; joining and slide interfaces are retained.',42,83,755,10)
  if i==2:
   b.para('两半抽屉的候选打印方向没有平面着床，后半高度也超过260 mm；这不是可用摆盘，需要重新安排方向与支撑。' if z else 'The candidate drawer poses lack planar bed contact; the rear half also exceeds 260 mm in height. Rework orientation and supports before slicing.',42,130,755,10,color=ORANGE)
  b.note('PETG/FDM检查发现单抽屉后半件薄壁及三抽屉薄层错误，另有悬垂、桥接等提示。尚无实物验证。' if z else 'PETG/FDM checks found thin-wall / thin-skin errors on four drawer parts, plus overhang and bridge warnings. Physical fit is untested.');b.end();b.save();print(b.path.name)
