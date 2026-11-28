"""Package only successfully sliced projects; retain a separate blocked-status index."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile,re,posixpath,xml.etree.ElementTree as ET
from build_print_profiles import REAR_LOCK_FILE
from print_profile_targets import TARGETS
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'print-profiles'
parser=argparse.ArgumentParser();parser.add_argument('--group',choices=['256','h-series']);group_filter=parser.parse_args().group
printers=[key for key,t in TARGETS.items() if not group_filter or t['group']==group_filter]
for flags in ([['--printer',key] for key in printers] if group_filter else [[]]):
 subprocess.run([sys.executable,str(ROOT/'tools/check_print_profiles.py'),*flags],check=True)
files=[ROOT/'LICENSE',ROOT/'docs/drawer-repair.md',ROOT/'docs/ht-top-printing.md',ROOT/'docs/images/corner-dowel-section.png',P/'README.md',*sorted(P.glob('**/presets/*.json')),*(ROOT/'models/fit-check').glob('*')];lines=['# 配置索引 / Profile index','','所有项目尚未实物验收，不可标记为 MakerWorld 已验证配置。 / None is physically validated.','',
 '小于 256 × 256 mm 的打印板不支持，不提供小板工程。 / Beds smaller than 256 × 256 mm are unsupported; no small-bed projects are provided.',''];records=[]
files.append(ROOT/REAR_LOCK_FILE)
small_files={ROOT/'docs/256-printing.md',ROOT/'docs/images/corner-dowel-section.png'}
small_files.update(p for p in (ROOT/'models/256').rglob('*') if p.is_file())
for bom in (ROOT/'models/256').glob('*/*/parts.json'):
 small_files.update(ROOT/r['file'] for r in json.loads(bom.read_text()))
current_group=None
paths=sorted(P.rglob('manifest.json'),key=lambda p:(['256','h-series'].index(json.loads(p.read_text()).get('bed_group','256')),str(p)))
for p in paths:
 r=json.loads(p.read_text());hours=weight=0
 printer_key=r.get('printer_key','x2d');group=r.get('bed_group','256');project_name=r.get('project_file',printer_key+'-04-petg.3mf')
 if printer_key not in printers:continue
 relative=str(p.parent.relative_to(P))
 if group!=current_group:
  current_group=group;lines += ['## '+{'256':'256 mm · X2D / P2S','h-series':'H 系列大板 / H-series · H2S / H2C / H3C'}[group],'','| Printer | Profile | Status | Plates | Estimated hours | PETG g |','| --- | --- | --- | ---: | ---: | ---: |']
 readme=[f"# {r['profile']}",'',f"Status: **{r['status']}**",'',
     r['printer'].replace('Bambu Lab ','')+' · 0.4 mm · PETG Basic · Textured PEI · 0.20 mm', '',
     {'replacement':'HT 侧替换件 / HT-side replacement','common':'洞洞板端框 / Pegboard ends','compatibility':'旧 HT 顶件过渡端框 / Legacy HT-top end','fit-check':'试配小件 / Fit specimens'}.get(r['profile'].split('/')[0],'普通端框 / Plain ends'),'',
     '尚未实物试装、测试承重或上传 MakerWorld。 / Not physically validated or published to MakerWorld.','']
 if r['profile'] in ('fit-check/ht-top','replacement/ht-top-right'):
  readme+=['旧 F02 的 PETG Matte 实打遇到支撑难拆，层间定位脚和圆角有缝。请选择与耗材匹配的工程或预设。','',
           'The original matte PETG print had stuck supports and gaps at the stacking foot and corners. Choose the project or filament preset for your spool.','']
 if group=='256':
  matte=json.loads((p.parent/'matte-slice.json').read_text());matte_project=p.parent/matte['project_file']
  assert matte['project_sha256']==hashlib.sha256(matte_project.read_bytes()).hexdigest() and matte['base_project_sha256']==r['project_sha256']
  files.extend([matte_project,p.parent/'matte-slice.json'])
  readme += [f"[PETG Matte · 打开工程 / Open project]({matte_project.name})", '',
             f"Matte · {matte['metrics']['plate_count']} 盘 / plates · {matte['metrics']['hours']:.2f} h · {matte['metrics']['total_g']:.2f} g · 支撑 / support {matte['metrics']['support_g']:.2f} g",'']
  if r['profile'].startswith(('ams2pro/','ams2pro-ht/')):
   readme+=['同编号的 a 和 b 竖直合拢。J 是整根横梁。 / Lower matching a/b sections together. J denotes a one-piece beam.','']
  if r['profile']=='fit-check/front-pin':
   readme+=['把短圆销 P3 放入下层 P1，再落下顶件前角 P2。翻转圆销再试一次。 / Put P3 into P1, lower P2 and repeat with the pin flipped.','']
  if r['profile'].startswith('compatibility/'):
   readme+=['这对前后段合成一只右端框，用于上方保留旧弧脚、下方连接新版圆孔。 / Join the two sections into one right end for an older curved upper foot on a new round-pin stack.','']
 if any(part.get('print_file')==REAR_LOCK_FILE for part in r['parts']) or r['profile'].startswith(('common/','compatibility/')):
  link=posixpath.relpath(REAR_LOCK_FILE,str(p.parent.relative_to(ROOT)))
  readme+=[f'每道接缝左右各用一片，所有层通用。 / Use two identical bowties per seam, one on each side. [通用尾锁 / Rear key STL]({link})','']
 if r['profile']=='fit-check/ht-top':
  readme+=['把 HT04 圆销放入下层 HT01，再放上 HT02，从后方水平推入通用蝴蝶锁片 HT03。检查锁槽顶面、外圆角及能否徒手退出。HT05 与 HT06 竖直合拢，检查新接缝。','',
           'Place HT04 in the lower HT01 hole, then lower HT02 onto it and slide the common HT03 bowtie in from the rear, either end up. Inspect the pocket roof and round corner, then withdraw the key by hand. Lower HT05 into HT06 to test the rail joint.','']
 if r['profile']=='replacement/ht-top-right':
  readme+=['F02、F05 平放打印，F06、F07 为相同的圆柱销，任一端贴板。将前后段的两处燕尾竖直合拢，再把圆销放入下层右侧前后孔。F03、F04 都是同一片蝴蝶锁片。右侧用其中一片，大面贴板打印，装好后从后面水平推入 F05。','',
           'Print F02 and F05 flat and the identical F06 and F07 dowels on end. Join both dovetails vertically and place the dowels in the holes of the lower frame. F03 and F04 are identical bowties. Print either on its broad face and slide it into F05 from the rear.','']
 if r['status']=='sliced_not_printed':
  for plate in ET.parse(p.parent/'slice-info.xml').findall('plate'):
   m={x.get('key'):x.get('value') for x in plate.findall('metadata')};hours+=float(m['prediction'])/3600;weight+=float(m['weight'])
  files.extend([p,p.parent/project_name,p.parent/'slice-info.xml'])
  files.extend(p.parent/f"plate_{q['number']}.png" for q in r['plates'])
  if (p.parent/'printing-checks.json').exists():files.append(p.parent/'printing-checks.json')
  files.append(p.parent/'slice-validation.json')
  for name in ['layout-validation.json','layout-printing-checks.json','layout-rule-validation.json']:
   if (p.parent/name).exists():files.append(p.parent/name)
  comparison=p.parent/'layout-validation.json'
  if comparison.exists():
   c=json.loads(comparison.read_text());before=c['before'];after=c['after']
   readme += ['摆盘切片对比 / Sliced layout comparison:', '',
      '| Metric | Before | After |','| --- | ---: | ---: |',
      *[f"| {label} | {before[field]} | {after[field]} |" for label,field in
        [('Plates','plate_count'),('Estimated hours','hours'),('PETG g','total_g'),('Support extrusion g','support_g')]],
      '', '支撑重量按 G-code 挤出量估算；未实物验证。 / Support mass is estimated from G-code extrusion; not physically validated.', '']
  readme += [f'[打开摆盘工程 / Open project]({project_name})','',f'预计 / Estimate: {hours:.1f} h · {weight:.1f} g PETG','',
     '| Plate | Parts | Preview |','| --- | --- | --- |']
  for plate in r['plates']:
   readme.append(f"| {plate['number']} | {plate['name']} | ![Plate {plate['number']}](plate_{plate['number']}.png) |")
  link=f"[{r['profile']}]({relative}/README.md)"
 else:
  files.append(p);link=r['profile']
  readme += ['此项未提供打印工程。 / No print project is provided.','',*[f'- {b}' for b in r.get('blockers',[])]]
 (p.parent/'README.md').write_text('\n'.join(readme)+'\n');files.append(p.parent/'README.md')
 lines.append(f"| {r['printer'].replace('Bambu Lab ','')} | {link} | {r['status']} | {len(r.get('plates',[]))} | {hours:.1f} | {weight:.1f} |")
 records.append({'profile':r['profile'],'status':r['status'],'blockers':r.get('blockers',[])})
if not group_filter:
 (P/'INDEX.md').write_text('\n'.join(lines)+'\n');files.append(P/'INDEX.md')
def bundle(name,selected,index=None,guide=None):
 archive=ROOT/'dist'/name;archive.parent.mkdir(exist_ok=True)
 contents={str(p.relative_to(ROOT)):p.read_bytes() for p in selected}
 if index is not None:contents['print-profiles/INDEX.md']=index.encode()
 if guide is not None:contents['README.md']=guide.encode()
 if name=='overstack-print-profiles-h-series.zip':
  guide='models/fit-check/README.md'
  contents[guide]=contents[guide].replace(b'../../print-profiles/x2d/fit-check/',b'../../print-profiles/h2s/fit-check/')
 hashes={n:hashlib.sha256(data).hexdigest() for n,data in contents.items()}
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for n,data in sorted(contents.items()):z.writestr(n,data)
  z.writestr('sha256.json',json.dumps(hashes,indent=2)+'\n')
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for n,h in hashes.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
  for n in z.namelist():
   if not n.endswith('.md'):continue
   for link in re.findall(r'\]\(([^)]+)\)',z.read(n).decode()):
    if '://' in link:continue
    target=posixpath.normpath(posixpath.join(posixpath.dirname(n),link.split('#')[0]))
    assert target in z.namelist() or any(p.startswith(target.rstrip('/')+'/') for p in z.namelist()),(n,link)
 print(archive,hashlib.sha256(archive.read_bytes()).hexdigest())

if not group_filter:bundle('overstack-print-profiles-preview.zip',set(files)|small_files)
intro,*sections=('\n'.join(lines)+'\n').split('## ')
for group,section in zip(dict.fromkeys(TARGETS[key]['group'] for key in printers),sections,strict=True):
 selected=[]
 for p in files:
  rel=p.relative_to(ROOT).parts
  if rel[0]!='print-profiles' or len(rel)==2:
   selected.append(p)
  elif TARGETS[rel[1]]['group']==group:
   selected.append(p)
 bundle('overstack-print-profiles-'+group+'.zip',set(selected)|(small_files if group=='256' else set()),intro+'## '+section)

# Small downloads for testing the reported corner or replacing only the old F02.
for slug,profile,title in [('front-pin','fit-check/front-pin','F06 前角圆销试印 / Front dowel fit test'),
                           ('fit','fit-check/ht-top','HT 后角试印 / HT rear corner test'),
                           ('right','replacement/ht-top-right','HT 侧五件替换套 / HT-side replacement')]:
 if group_filter and (group_filter!='256' or slug!='front-pin'):continue
 selected=[ROOT/'LICENSE',ROOT/'docs/ht-top-printing.md',ROOT/'docs/images/corner-dowel-section.png']
 if slug!='front-pin':selected.append(ROOT/REAR_LOCK_FILE)
 guide=[f'# {title}','','选自己的机型，在 Bambu Studio 内换成这卷 PETG Matte 的材料预设后切片。',
        'Choose your printer, select the preset for your matte spool and reslice in Bambu Studio.','']
 for printer in TARGETS:
  folder=P/printer/profile
  if not folder.is_dir():continue
  selected.extend(f for f in files if f.parent==folder)
  manifest=json.loads((folder/'manifest.json').read_text())
  selected.extend(ROOT/part['source'] for part in manifest['parts'])
  project=(folder/manifest['project_file']).relative_to(ROOT)
  guide.append(f'- [{printer.upper()} · Bambu Studio]({project})')
  if TARGETS[printer]['group']=='256':
   matte=json.loads((folder/'matte-slice.json').read_text())
   guide.append(f"- [{printer.upper()} · PETG Matte]({(folder/matte['project_file']).relative_to(ROOT)})")
 guide+=['','[试配方法与切片结果 / Fit test and slice results](docs/ht-top-printing.md)']
 bundle(f'overstack-ht-top-{slug}.zip',selected,guide='\n'.join(guide)+'\n')
