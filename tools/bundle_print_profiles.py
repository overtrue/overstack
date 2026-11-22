"""Package only successfully sliced projects; retain a separate blocked-status index."""
from pathlib import Path
import hashlib,json,runpy,zipfile,re,posixpath,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'print-profiles'
runpy.run_path(str(ROOT/'tools/check_print_profiles.py'),run_name='__main__')
files=[ROOT/'LICENSE',ROOT/'docs/drawer-repair.md',P/'README.md',*sorted(P.glob('**/presets/*.json')),*(ROOT/'models/fit-check').glob('*')];lines=['# 配置索引 / Profile index','','所有项目尚未实物验收，不可标记为 MakerWorld 已验证配置。 / None is physically validated.','',
 '小于 256 × 256 mm 的打印板不支持，不提供小板工程。 / Beds smaller than 256 × 256 mm are unsupported; no small-bed projects are provided.',''];records=[]
from print_profile_targets import TARGETS
current_group=None
paths=sorted(P.rglob('manifest.json'),key=lambda p:(['256','h-series'].index(json.loads(p.read_text()).get('bed_group','256')),str(p)))
for p in paths:
 r=json.loads(p.read_text());hours=weight=0
 printer_key=r.get('printer_key','x2d');group=r.get('bed_group','256');project_name=r.get('project_file',printer_key+'-04-petg.3mf')
 relative=str(p.parent.relative_to(P))
 if group!=current_group:
  current_group=group;lines += ['## '+{'256':'256 mm · X2D / P2S','h-series':'H 系列大板 / H-series · H2S / H2C / H3C'}[group],'','| Printer | Profile | Status | Plates | Estimated hours | PETG g |','| --- | --- | --- | ---: | ---: | ---: |']
 readme=[f"# {r['profile']}",'',f"Status: **{r['status']}**",'',
     r['printer'].replace('Bambu Lab ','')+' · 0.4 mm · PETG Basic · Textured PEI · 0.20 mm', '',
     '端框：普通 / Ends: plain' if r['profile'].startswith('ams2pro') else '试配小件 / Fit specimens','',
     '尚未实物试装、测试承重或上传 MakerWorld。 / Not physically validated or published to MakerWorld.','']
 if r['status']=='sliced_not_printed':
  for plate in ET.parse(p.parent/'slice-info.xml').findall('plate'):
   m={x.get('key'):x.get('value') for x in plate.findall('metadata')};hours+=float(m['prediction'])/3600;weight+=float(m['weight'])
  files.extend([p,p.parent/project_name,p.parent/'slice-info.xml'])
  files.extend(p.parent/f"plate_{q['number']}.png" for q in r['plates'])
  if (p.parent/'printing-checks.json').exists():files.append(p.parent/'printing-checks.json')
  files.append(p.parent/'slice-validation.json')
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
(P/'INDEX.md').write_text('\n'.join(lines)+'\n');files.append(P/'INDEX.md')
def bundle(name,selected,index=None):
 archive=ROOT/'dist'/name;archive.parent.mkdir(exist_ok=True)
 contents={str(p.relative_to(ROOT)):p.read_bytes() for p in selected}
 if index is not None:contents['print-profiles/INDEX.md']=index.encode()
 if name=='stacknest-print-profiles-h-series.zip':
  guide='models/fit-check/README.md'
  contents[guide]=contents[guide].replace(b'../../print-profiles/x2d/fit-check/',b'../../print-profiles/h2s/fit-check/')
 hashes={n:hashlib.sha256(data).hexdigest() for n,data in contents.items()}
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for n,data in contents.items():z.writestr(n,data)
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

bundle('stacknest-print-profiles-preview.zip',files)
intro,standard,large=('\n'.join(lines)+'\n').split('## ')
for group,section in [('256',standard),('h-series',large)]:
 selected=[]
 for p in files:
  rel=p.relative_to(ROOT).parts
  if rel[0]!='print-profiles' or len(rel)==2:
   selected.append(p)
  elif TARGETS[rel[1]]['group']==group:
   selected.append(p)
 bundle('stacknest-print-profiles-'+group+'.zip',selected,intro+'## '+section)
