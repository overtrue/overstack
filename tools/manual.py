"""Create Chinese and English assembly guides from the same geometry and part IDs."""
from pathlib import Path
import os,json,sys,math
from ht_layers import LAYERS
ROOT=Path(__file__).resolve().parents[1]
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape,A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
import numpy as np
from PIL import Image

DOC=ROOT/'docs';PDF=DOC/'pdf';PDF.mkdir(exist_ok=True)
PACK=ROOT/'models/ams2pro+ht'
PARTS=json.loads((PACK/'parts.json').read_text())
JOBS={j['key']:j for j in json.loads((ROOT/'output/illustrations/jobs.json').read_text())}
W,H=landscape(A4);INK=colors.HexColor('#20343C');TEAL=colors.HexColor('#257A78');MUTED=colors.HexColor('#607079');PALE=colors.HexColor('#F3F6F5');ORANGE=colors.HexColor('#BF743D')
regular=os.environ.get('OVERSTACK_FONT_REGULAR','/System/Library/Fonts/STHeiti Light.ttc')
bold=os.environ.get('OVERSTACK_FONT_BOLD','/System/Library/Fonts/STHeiti Medium.ttc')
if not Path(regular).exists() or not Path(bold).exists():raise SystemExit('Set OVERSTACK_FONT_REGULAR and OVERSTACK_FONT_BOLD to CJK TrueType font files.')
pdfmetrics.registerFont(TTFont('CN',regular,subfontIndex=0));pdfmetrics.registerFont(TTFont('CNB',bold,subfontIndex=0))
EN_LABEL={'左端框':'Left end frame','右端框':'Right end frame','左侧承架':'Left carrier','右侧承架':'Right carrier','前横梁':'Front beam','后横梁':'Rear beam','左小抽屉':'Left side bin','右小抽屉':'Right side bin','层间锁片':'Rear locking key','隔墙':'Divider','顶部左片':'Left top half','HT 前段':'HT front section','HT 后段':'HT rear section','HT 前定位脚':'HT front foot','HT 后定位脚':'HT rear foot','抽屉1':'Drawer 1','抽屉2':'Drawer 2','抽屉3':'Drawer 3'}
TITLES_ZH=['五槽打印板层','八槽打印板层','双抽屉层','三抽屉层','设备顶件']
TITLES_EN=['Five-slot plate layer','Eight-slot plate layer','Double-drawer layer','Triple-drawer layer','Device top']
STEPS_ZH=[
 [('先装中段承架','左右承架的前封闭面已做成一体，不再安装独立封板。托条朝内，后挡在后。'),('装前后横梁','前梁从底部入口托入，再向前滑约29 mm。后梁从后方水平推入，位于托条下方。'),('装左右端框','对齐两侧竖向燕尾，从上方落入端框槽。检查中段不扭曲、底面能平放。')],
 [('先拼好中段和端框','托条朝内，后挡朝后。前梁走底部入口，后梁从后方滑入；再装左右端框。'),('装两只小抽屉','从正面放入侧仓导向。到位后检查两边间隙，不要敲入。'),('试走完整行程','小抽屉可拉出约60 mm。拆卸时先移开上层，再在止点抬高约12 mm，向前取出。')],
 [('拼好前后两根横梁','每根梁的两半先沿竖直方向对合中央燕尾。前梁从前方装入，后梁从后方装入。'),('装中间隔墙','将一个隔墙的前后定位舌对准梁上的槽，从上方落入。然后将中段装进两侧端框。'),('装两只整件抽屉','分别沿导向装入。每只抽屉正常行程约180 mm；拆卸需在止点抬高7 mm。')],
 [('装四片横梁和两侧承架','前后梁各两片，先拼梁，再从对应前后方向装进侧承架。'),('装两片隔墙','隔墙前后定位舌必须同时进槽，形成三个等宽通道。中段随后装进左右端框。'),('逐只装入抽屉','先逐只试滑，再同时关闭。不要用面板把手提起整层；拆抽屉前先移开上层或顶件。')],
 [('拼好 HT 侧','F02 前段和 F05 后段平放打印。对准两处错开的燕尾，沿竖直方向合拢。'),('放入圆销，滑合左片','F06 和 F07 相同，先放入下层右侧前后孔，任一端朝下。左片 F01 向后错开约 20 mm，对准前后燕尾后向前滑到位。'),('落座后装锁片','对齐四个角，竖直落座。从后方水平插入两片相同的蝴蝶锁片。F03、F04 左右通用，上下可翻转。')]
]
STEPS_EN=[
 [('Build the middle frame','The front closures are integral with the two carriers. No separate blanking plates are needed. Ledges face inward and stops face the rear.'),('Fit the front and rear beams','Lift the front beam through its bottom entry, then slide it forward about 29 mm. Slide the rear beam in horizontally from behind, below the ledges.'),('Fit the end frames','Align the vertical dovetails and lower the middle carriers into the end-frame slots. Check that the layer is square and rests flat.')],
 [('Assemble the frame','Ledges face inward. Fit the front beam through its bottom entry and slide the rear beam in from behind. Add the two end frames.'),('Insert both side bins','Feed the bins into their guides from the front. Check both clearances; do not hammer them into place.'),('Check the travel','Side bins travel about 60 mm. To remove one, first remove the layer above, pull to the stop, lift about 12 mm and pull forward.')],
 [('Join the two split beams','Each front/rear beam has two halves. Join each central dovetail vertically first. Insert the front beam from the front and the rear beam from behind.'),('Lower the centre divider','Align its front and rear tabs with the beam slots and lower it into place. Then fit the middle frame into the end frames.'),('Insert both one-piece drawers','Guide each drawer into its channel. Normal travel is about 180 mm. Removal requires a 7 mm lift at the stop.')],
 [('Fit beams and side carriers','The front and rear beams each have two pieces. Join them, then insert them into the carriers from their respective ends.'),('Fit both dividers','Seat both locating tabs on each divider to create three equal channels. Fit the middle frame into the two end frames.'),('Check each drawer','Test each drawer separately, then close all three. Do not lift the layer by the handles. Remove the layer above before lifting a drawer out.')],
 [('Join the HT sections','Print F02 and F05 bottom-down. Align both staggered tails and lower one section into the other.'),('Place the dowels and slide in F01','Set F06 and F07 into the lower right-front and right-rear holes, either end first. Offset F01 about 20 mm rearward, align the original dovetails and slide it forward.'),('Seat and lock the top','Align the four corners and lower the top. Slide the two identical bowties into the rear slots. F03 and F04 fit either side, either end up.')]
]

class Book:
 def __init__(self,lang):
  self.lang=lang;self.zh=lang=='zh';self.reg='CN' if self.zh else 'Helvetica';self.bold='CNB' if self.zh else 'Helvetica-Bold';self.page=0
  self.path=PDF/f'overstack-assembly-{lang}.pdf';self.c=canvas.Canvas(str(self.path),pagesize=(W,H),pageCompression=1)
  self.c.setTitle(('Overstack 组装教程' if self.zh else 'Overstack Assembly Guide'));self.c.setAuthor('overtrue');self.c.setSubject('Assembly guide for a geometry-checked prototype')
 def text(self,s,x,y,size=11,bold=False,color=INK):
  self.c.setFillColor(color);self.c.setFont(self.bold if bold else self.reg,size);self.c.drawString(x,y,s)
 def para(self,s,x,top,width,size=10.5,color=INK):
  style=ParagraphStyle('body',fontName=self.reg,fontSize=size,leading=size*1.48,textColor=color,wordWrap='CJK' if self.zh else None)
  p=Paragraph(s,style);_,h=p.wrap(width,1000);p.drawOn(self.c,x,top-h);return h
 def start(self,title,kicker='ASSEMBLY GUIDE'):
  self.page+=1;c=self.c;c.setFillColor(colors.HexColor('#FCFCF9'));c.rect(0,0,W,H,fill=1,stroke=0)
  self.text('OVERSTACK / '+kicker,38,H-29,8,True,TEAL);self.text(title,38,H-62,23,True)
  c.bookmarkPage('p'+str(self.page));c.addOutlineEntry(title,'p'+str(self.page),level=0)
  c.setStrokeColor(colors.HexColor('#DFE6E3'));c.line(38,35,W-38,35)
  self.text(('数字样机 · 尚未实物试装' if self.zh else 'DIGITAL PROTOTYPE - PHYSICAL FIT NOT VERIFIED'),38,20,8,color=MUTED)
  self.text(f'{self.page:02d}',W-55,20,9,True)
 def end(self):self.c.showPage()
 def image(self,key,x,y,w,h,labels=False):
  path=DOC/'images'/(key+'.png');iw,ih=Image.open(path).size;scale=min(w/iw,h/ih);ww=iw*scale;hh=ih*scale;xx=x+(w-ww)/2;yy=y+(h-hh)/2
  self.c.drawImage(str(path),xx,yy,ww,hh,mask='auto')
  if labels:
   j=JOBS[key];cam=j['camera'];eye=np.array(cam['position']);target=np.array(cam['target']);up=np.array(cam['up']);f=target-eye;f/=np.linalg.norm(f);right=np.cross(f,up);right/=np.linalg.norm(right);up=np.cross(right,f)
   occupied=[]
   for ident in j['ids']:
    v=np.array(j['centers'][ident])-target;px=xx+ww/2+np.dot(v,right)*hh/(2*cam['orthographicHalfHeight']);py=yy+hh/2+np.dot(v,up)*hh/(2*cam['orthographicHalfHeight'])
    bx,by=px+10,py+12
    for _ in range(20):
     if any(abs(bx-a)<31 and abs(by-b)<19 for a,b in occupied):by+=20
     else:break
    bx=max(xx+16,min(xx+ww-16,bx));by=max(yy+12,min(yy+hh-12,by));occupied.append((bx,by))
    self.c.setStrokeColor(TEAL);self.c.setLineWidth(.6);self.c.line(px,py,bx,by)
    self.c.setFillColor(TEAL);self.c.roundRect(bx-15,by-8,30,16,4,fill=1,stroke=0);self.c.setFillColor(colors.white);self.c.setFont('Helvetica-Bold',8);self.c.drawCentredString(bx,by-3,ident)
  return xx,yy,ww,hh
 def steps(self,steps,x=597,top=480,width=207):
  y=top
  for i,(title,body) in enumerate(steps,1):
   self.c.setFillColor(TEAL);self.c.circle(x+8,y-6,8,fill=1,stroke=0);self.c.setFillColor(colors.white);self.c.setFont('Helvetica-Bold',9);self.c.drawCentredString(x+8,y-9,str(i))
   h=self.para(title,x+25,y+2,width-25,11.5);y-=max(h,16)+10
   y-=self.para(body,x,y,width,10.2)+22
 def note(self,s,x=40,y=73,w=760):
  self.c.setFillColor(PALE);self.c.roundRect(x,y-7,w,37,5,fill=1,stroke=0);self.para(s,x+11,y+21,w-22,9.4,color=MUTED)
 def save(self):self.c.save()

def build(lang):
 b=Book(lang);z=b.zh
 b.start('Overstack' if z else 'Overstack','MODULAR AMS STORAGE')
 b.text('AMS 模块化收纳底座' if z else 'Modular storage for AMS 2 Pro + AMS HT',40,H-92,15,color=MUTED)
 b.image('hero',245,91,565,392)
 b.text('ASSEMBLY GUIDE',40,419,10,True,TEAL)
 b.para('把打印板、抽屉与设备托架，叠成一套。' if z else 'Build-plate storage, drawers and a device top in one modular stack.',40,389,195,18)
 b.para('4 层 + 顶件\n51 个制作零件\n13 个打印板位\n5 只主抽屉 + 2 只侧抽屉'.replace('\n','<br/>') if z else '4 layers + device top<br/>51 fabrication parts<br/>13 plate slots<br/>5 main drawers + 2 side bins',40,283,193,11.5)
 b.para('495 × 287 × 249 mm<br/>当前整套装配外廓，含底脚。' if z else '495 x 287 x 249 mm<br/>Complete stack, including feet.',40,160,195,10.5)
 b.note('本教程对应 数字样机。爆炸图用于辨认零件；实际装入方向请按步骤操作。' if z else 'This guide describes the digital prototype. Exploded offsets identify parts; follow the written insertion directions.');b.end()
 b.start('从下到上的五组零件' if z else 'Five groups, from bottom to top')
 b.image('stack-exploded',35,58,420,448)
 y=482
 for i in reversed(range(len(LAYERS))):
  n=sum(r['layer']==i for r in PARTS);height=40 if i==0 else (60 if i<len(LAYERS)-1 else 26)
  b.text(LAYERS[i][0],495,y,22,True,TEAL)
  b.text((TITLES_ZH if z else TITLES_EN)[i],535,y+1,13,True)
  b.text((f'{n} 个零件 / '+('顶面高 26 mm' if i==len(LAYERS)-1 else f'层高 {height} mm')) if z else f'{n} parts / '+('26 mm above layer' if i==len(LAYERS)-1 else f'{height} mm layer'),535,y-19,10,color=MUTED);y-=66
 b.para('层间锁片计入其上方层；顶部两枚锁片计入 F 组。' if z else 'Inter-layer keys belong to the layer above. The two top keys belong to group F.',490,83,305,10,color=MUTED);b.end()
 b.start('开始之前' if z else 'Before assembly')
 intro=[('准备工具','平整桌面、修边刀或细砂纸、卡尺。先去毛边，尤其是燕尾槽、导轨和锁片边缘。') if z else ('Prepare the workspace','Use a flat surface, a deburring tool or fine abrasive, and calipers. Remove burrs from dovetails, guides and locking keys.'),('先试配再堆叠','逐层空载试装。卡住时找出干涉位置，不要敲打薄托条或用锁片强拉到位。') if z else ('Dry-fit one layer at a time','Check each layer without load. If a joint binds, locate the interference instead of hammering thin ledges or pulling parts together with a key.'),('文件不是切片包','STL 和 3MF 保留装配位置。3MF仅包含几何，没有打印机、材料或支撑配置。') if z else ('The files are not sliced jobs','STL and 3MF files retain assembly positions. The 3MF files contain geometry only, with no printer, material or support settings.')]
 b.steps(intro,x=42,top=482,width=345)
 b.image('layer-a-assembled',413,255,385,235)
 b.para('统一方向' if z else 'Orientation',433,233,330,14)
 b.para('前：抽屉拉手和打印板入口。<br/>后：层间锁片和打印板后挡。<br/>所有尺寸单位为毫米。' if z else 'Front: drawer handles and plate entry.<br/>Rear: locking keys and plate stops.<br/>All dimensions are in millimetres.',433,202,330,11)
 b.note('PETG / FDM / 0.4 mm喷嘴 / 0.2 mm层高仅是已运行的通用几何检查条件，不是已验证的打印配置。' if z else 'PETG / FDM / 0.4 mm nozzle / 0.2 mm layers are the generic check conditions, not a validated print profile.');b.end()
 for i,(prefix,_,_) in enumerate(LAYERS):
  b.start(prefix+' / '+(TITLES_ZH if z else TITLES_EN)[i])
  b.image('layer-'+prefix.lower()+'-exploded',30,156,552,346,labels=True)
  b.steps((STEPS_ZH if z else STEPS_EN)[i],top=484)
  group=[r for r in PARTS if r['layer']==i]
  for j,r in enumerate(group):
   col=j%3;row=j//3;label=r['label'] if z else EN_LABEL[r['label']]
   b.text(r['id']+'  '+label,42+col*180,143-row*15,8.6,color=MUTED)
  note=('爆炸图不是装配路径。每个编号对应文件名开头的同一编号。' if z else 'Exploded offsets are not insertion paths. Match each ID to the same prefix on its part file.')
  b.para(note,42,57,750,8.4,color=MUTED);b.end()
 b.start('层间连接与拆卸' if z else 'Stacking and separating layers')
 b.image('layer-lock-detail',40,111,475,397,labels=True)
 b.steps([('先对齐圆柱定位销','底脚朝下、锁片孔朝后，竖直落座。确认四角都贴合后，再装锁片。'),('锁片从后方推入','每道层缝用两片相同的蝴蝶锁片，左右通用，上下可翻转。锁片限制上下分离，但可向后抽出，不是防丢自锁件。'),('拆卸顺序相反','先取下设备和上层内容物，再向后抽出锁片、竖直提开上层。移动整套时从底部承托。')] if z else [('Align the round pins','Feet face down and key pockets face the rear. Lower the layer vertically. Seat all four corners before fitting keys.'),('Push keys in from behind','Use two identical bowties per seam, either side and either end up. They resist vertical separation but can be withdrawn rearward; they are not captive latches.'),('Disassemble in reverse','Remove devices and contents first. Pull the keys out rearward, then lift the upper layer vertically. Support the base when moving the stack.')],x=552,top=480,width=250)
 b.note('装好层间锁片不等于完成承重验证。本版没有额定载荷。' if z else 'Fitted locking keys do not establish a load rating. This version has no tested load rating.');b.end()
 b.start('打印板与抽屉怎么取出' if z else 'Removing plates and drawers')
 b.image('rail-detail',35,240,470,259)
 b.image('layer-d-exploded',35,56,470,194)
 b.steps([('打印板：抬约1 mm后前抽','两侧托条一直延伸到后挡。后挡是刚性限位，不是弹性卡扣；不要强行继续向后推。'),('主抽屉：180 mm + 抬7 mm','先移开上层或顶件，拉到止点，再抬高约7 mm继续前抽。小侧抽屉对应60 mm + 抬12 mm。'),('实心底板与设备底部','所有抽屉均采用2 mm实心底板。设备上机前应核对脚位、底壳、进气和走线。')] if z else [('Plates: lift about 1 mm, then pull','The side ledges run to the rear stops. These are rigid stops, not spring clips; do not force a plate farther back.'),('Main drawers: 180 mm + 7 mm lift','Remove the upper layer or top, pull to the stop, lift about 7 mm and continue forward. Side bins use 60 mm travel + 12 mm lift.'),('Solid floors and device clearance','All drawers have 2 mm solid floors. Check device feet, underside, ventilation and cables before use.')],x=545,top=482,width=258);b.end()
 b.start('检查完成了什么，还差什么' if z else 'What is checked, and what remains')
 checks=[('51 个零件都是封闭实体','整装 1275 对关系无体积干涉；托条、抽取、止挡与连接路径做了数字检查。'),('通用打印检查通过','条件为PETG/FDM、0.4 mm喷嘴、0.2 mm层高、256×256×260 mm空间。38 种不同几何通过检查。抽屉方向与支撑以对应机型工程为准，已检查平面着床。仍有悬垂、桥接和薄尖边提示。'),('还没有实物试装和承重结果','实际切片估算见打印配置索引，旧 HT 右顶件已有 PETG Matte 实打反馈，新顶件待复打。网格检查未覆盖孔轴和刻字等细节规则。')] if z else [('51 closed solid parts','All 1,275 assembly pairs are free of volumetric clashes. Ledges, travel, stops and connection paths have digital checks.'),('Generic print checks passed','Conditions: PETG/FDM, 0.4 mm nozzle, 0.2 mm layers, 256 x 256 x 260 mm volume. All 38 distinct geometries pass. Use the printer-specific projects for drawer orientation and supports; planar bed contact is checked. Overhang, bridge and thin-edge warnings remain.'),('Physical fit and strength are still untested','Slicer estimates are in the print-profile index; the original HT side was printed in PETG Matte. The revised top awaits a physical test. Mesh checks do not evaluate all hole-axis or detail rules.')]
 b.steps(checks,x=42,top=480,width=405)
 b.text('发布前实物记录' if z else 'Before a community release',494,480,15,True)
 items=['每层装配与拆卸照片','燕尾、层间锁片、后梁的配合','打印板尺寸和止挡是否合适','抽屉完整行程与抬出操作','AMS 2 Pro / HT脚位、通风和稳定性','实际材料、摆盘、支撑与打印配置'] if z else ['Photograph each assembled layer','Check dovetails, keys and rear-beam fit','Test actual plates against the stops','Test full drawer travel and lift-out','Check device seating, airflow and stability','Record material, orientation and support settings']
 yy=445
 for item in items:
  b.c.setStrokeColor(TEAL);b.c.rect(495,yy-9,9,9,fill=0,stroke=1);h=b.para(item,515,yy+2,285,10.5);yy-=max(37,h+15)
 b.note('当前图片全部由实际CAD几何渲染，不是实物照片。' if z else 'Every illustration in this guide is rendered from the actual CAD geometry. None is a photograph of a printed assembly.');b.end()
 b.start(f'零件清单 / {len(PARTS)}件' if z else f'Parts index / {len(PARTS)} pieces')
 for i,r in enumerate(PARTS):
  col,row=divmod(i,(len(PARTS)+1)//2);x=42+col*399;y=493-row*14.8
  b.text(r['id'],x,y,8.5,True,TEAL);b.text(r['label'] if z else EN_LABEL[r['label']],x+42,y,8.5)
  b.text(LAYERS[r['layer']][0]+' / '+LAYERS[r['layer']][1][:2],x+330,y,8,color=MUTED)
 b.end();b.save();print(b.path)
 return b.path

if __name__=='__main__':
 for lang in ['zh','en']:build(lang)
