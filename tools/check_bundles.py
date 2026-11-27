"""Check current download contents, source hashes and local Markdown links."""
from pathlib import Path
import hashlib,json,posixpath,re,zipfile
from urllib.parse import unquote,urlsplit
from ht_layers import LAYERS

ROOT=Path(__file__).resolve().parents[1]
DEVICES=['ams2pro+ht','ams2pro','common']


def check_bundle(archive):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None,archive
        names=set(z.namelist());prefix=archive.stem+'/'
        hashes=json.loads(z.read(prefix+'sha256.json'))
        assert names=={prefix+p for p in hashes}|{prefix+'README.md',prefix+'sha256.json'},archive
        if archive.stem=='overstack-ams2pro':
            single='models/ams2pro/1-drawer-layer/'
            parts=json.loads(z.read(prefix+single+'parts.json'))
            files={part['file'] for part in parts}
            assert {single+'drawer_half_1.stl',single+'drawer_half_2.stl'} <= files <= hashes.keys(),(archive,'single drawer')
        else:
            assert not any(p.startswith('docs/images/no-ht-1-drawer') for p in hashes),(archive,'compact drawer image')
        if archive.stem=='overstack-ams2pro+ht':
            expected={slug for _,slug,_ in LAYERS}
            layers={p.split('/')[2] for p in hashes if p.startswith('models/ams2pro+ht/') and p.endswith('.stl')}
            assert layers==expected,(archive,'HT layer set',layers)
            model_dir='models/ams2pro+ht/'
            parts=json.loads(z.read(prefix+model_dir+'parts.json'))
            assert {model_dir+p['packaged_file']:p['packaged_sha256'] for p in parts}=={
                path:digest for path,digest in hashes.items() if path.startswith(model_dir) and path.endswith('.stl')
            },(archive,'numbered STL hashes')
            guides={p for p in hashes if p.startswith('docs/pdf/0') and p.endswith('.pdf')}
            assert guides=={f'docs/pdf/{slug}-assembly-{lang}.pdf' for slug in expected for lang in ['zh','en']}
        for path,digest in hashes.items():
            assert hashlib.sha256(z.read(prefix+path)).hexdigest()==digest,(archive,path,'archive hash')
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,(archive,path,'source hash')
        for name in sorted(names):
            if not name.endswith('.md'):continue
            for link in re.findall(r'\]\(([^)]+)\)',z.read(name).decode()):
                url=urlsplit(link)
                if url.scheme or url.netloc or not url.path:continue
                target=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(url.path)))
                assert target in names or any(n.startswith(target.rstrip('/')+'/') for n in names),(archive,name,link)
    print('PASS:',archive.name,'contents, source hashes and Markdown links')


if __name__=='__main__':
    for device in DEVICES:check_bundle(ROOT/'dist'/('overstack-'+device+'.zip'))
