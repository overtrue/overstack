"""Bundle numbered geometry, bilingual guides and final renders for sharing."""
from pathlib import Path
import shutil,json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist/stacknest-v55'
for name in ['pdf','images']:
 target=D/name;target.mkdir(exist_ok=True)
 for f in (ROOT/'docs'/name).iterdir():
  if f.is_file():shutil.copy2(f,target/f.name)
for f in ['makerworld-zh.md','makerworld-en.md','validation.json','provenance.md']:
 shutil.copy2(ROOT/'docs'/f,D/f)
shutil.copy2(ROOT/'README.md',D/'README.md');shutil.copy2(ROOT/'LICENSE',D/'LICENSE')
for folder in sorted(D.glob('0*')):
 prefix=folder.name.split('-')[0]
 for f in (ROOT/'docs/pdf').glob(prefix+'-*.pdf'):shutil.copy2(f,folder/f.name)
files=sorted(f for f in D.rglob('*') if f.is_file() and f.name!='sha256.json')
assert all(str(f.relative_to(D)).isascii() for f in files)
(D/'sha256.json').write_text(json.dumps({str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2))
archive=ROOT/'dist/stacknest-v55.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(D.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(D.parent)))
print(archive,archive.stat().st_size)
