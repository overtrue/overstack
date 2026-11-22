"""Package only successfully sliced projects; retain a separate blocked-status index."""
from pathlib import Path
import hashlib,json,runpy,zipfile,re,posixpath,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'print-profiles'
runpy.run_path(str(ROOT/'tools/check_print_profiles.py'),run_name='__main__')
files=[ROOT/'LICENSE',P/'README.md',*sorted((P/'presets').glob('*')),*(ROOT/'models/fit-check').glob('*')];lines=['# 配置索引 / Profile index','','所有项目尚未实物验收，不可标记为 MakerWorld 已验证配置。 / None is physically validated.','',
 '| Profile | Status | Plates | Estimated hours | PETG g |','| --- | --- | ---: | ---: | ---: |'];records=[]
for p in sorted(P.glob('*/*/manifest.json')):
 r=json.loads(p.read_text());hours=weight=0
 readme=[f"# {r['profile']}",'',f"Status: **{r['status']}**",'',
     'X2D · 0.4 mm · PETG Basic · Textured PEI · 0.20 mm', '',
     '端框：普通 / Ends: plain' if r['profile'].startswith('ams2pro') else '试配小件 / Fit specimens','',
     '尚未实物试装、测试承重或上传 MakerWorld。 / Not physically validated or published to MakerWorld.','']
 if r['status']=='sliced_not_printed':
  for plate in ET.parse(p.parent/'slice-info.xml').findall('plate'):
   m={x.get('key'):x.get('value') for x in plate.findall('metadata')};hours+=float(m['prediction'])/3600;weight+=float(m['weight'])
  files.extend([p,p.parent/'x2d-04-petg.3mf',p.parent/'slice-info.xml'])
  files.extend(p.parent/f"plate_{q['number']}.png" for q in r['plates'])
  if (p.parent/'printing-checks.json').exists():files.append(p.parent/'printing-checks.json')
  readme += ['[打开摆盘工程 / Open project](x2d-04-petg.3mf)','',f'预计 / Estimate: {hours:.1f} h · {weight:.1f} g PETG','',
     '| Plate | Parts | Preview |','| --- | --- | --- |']
  for plate in r['plates']:
   readme.append(f"| {plate['number']} | {plate['name']} | ![Plate {plate['number']}](plate_{plate['number']}.png) |")
  link=f"[{r['profile']}]({r['profile']}/README.md)"
 else:
  files.append(p);link=r['profile']
  readme += ['此项未提供打印工程。 / No print project is provided.','',*[f'- {b}' for b in r.get('blockers',[])]]
 (p.parent/'README.md').write_text('\n'.join(readme)+'\n');files.append(p.parent/'README.md')
 lines.append(f"| {link} | {r['status']} | {len(r.get('plates',[]))} | {hours:.1f} | {weight:.1f} |")
 records.append({'profile':r['profile'],'status':r['status'],'blockers':r.get('blockers',[])})
(P/'INDEX.md').write_text('\n'.join(lines)+'\n');files.append(P/'INDEX.md')
archive=ROOT/'dist/stacknest-print-profiles-preview.zip';archive.parent.mkdir(exist_ok=True)
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,str(p.relative_to(ROOT)))
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
