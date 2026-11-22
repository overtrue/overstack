"""ZIP the new sets with shared parts, matching manifests, guides and images."""
from pathlib import Path
import hashlib,json,zipfile
from check_bundles import check_bundle
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist';DIST.mkdir(exist_ok=True)
for device in ['ams2pro+ht','ams2pro','common']:
    name='stacknest-'+device
    folders=['models/'+device]+(['models/common'] if device!='common' else [])
    files=[ROOT/'LICENSE']
    for folder in folders:files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    files.extend(p for p in (ROOT/'docs/images').glob('*.png') if device=='ams2pro+ht' or (device=='ams2pro' and p.name in ['lip-r3-detail.png','showcase-no-ht.png']) or p.name.startswith(('no-ht-','common-ends','common-grid-alignment','wide-pegboard')))
    if device!='common':files.append(ROOT/'docs/render-assets.md')
    if device=='ams2pro+ht':
        files.append(ROOT/'docs/drawer-repair.md')
        files.extend(p for p in (ROOT/'docs/pdf').iterdir() if p.is_file())
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    archive=DIST/(name+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):z.write(p,name+'/'+str(p.relative_to(ROOT)))
        z.writestr(name+'/sha256.json',json.dumps(hashes,indent=2)+'\n')
        z.writestr(name+'/README.md','# StackNest\n\nStart with models/'+device+'/README.md.\n\n先阅读对应 models 目录中的 README。模型未切片，尚未实物验收。\n')
    check_bundle(archive)
    print(archive.name,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
