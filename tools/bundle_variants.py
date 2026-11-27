"""ZIP the new sets with shared parts, matching manifests, guides and images."""
from pathlib import Path
import hashlib,json,zipfile
from check_bundles import check_bundle
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist';DIST.mkdir(exist_ok=True)
for device in ['ams2pro+ht','ams2pro','common']:
    name='overstack-'+device
    folders=['models/'+device]+(['models/common'] if device!='common' else [])
    files=[ROOT/'LICENSE']
    for folder in folders:files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    for image in (ROOT/'docs/images').glob('*.png'):
        shared=image.name.startswith(('common-ends','common-grid-alignment'))
        compact=image.name.startswith(('no-ht-','showcase-no-ht'))
        if shared or (device=='ams2pro+ht' and not compact) or (device=='ams2pro' and (compact or image.name=='lip-r3-detail.png')):
            files.append(image)
    if device!='common':files.append(ROOT/'docs/render-assets.md')
    if device=='ams2pro+ht':
        files.append(ROOT/'docs/drawer-repair.md')
        files.extend(p for p in (ROOT/'docs/pdf').iterdir() if p.is_file())
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    archive=DIST/(name+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):z.write(p,name+'/'+str(p.relative_to(ROOT)))
        z.writestr(name+'/sha256.json',json.dumps(hashes,indent=2)+'\n')
        guide='models/'+device+'/README.md'
        z.writestr(name+'/README.md',f'# Overstack\n\n[模型与装配说明 / Models and assembly guide]({guide})\n\n'
                   '实物试装待验证。 / Physical assembly is untested.\n')
    check_bundle(archive)
    print(archive.name,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
