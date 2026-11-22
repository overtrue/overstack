"""Check current download contents, source hashes and local Markdown links."""
from pathlib import Path
import hashlib,json,posixpath,re,zipfile
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
DEVICES=['ams2pro+ht','ams2pro','common']


def check_bundle(archive):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None,archive
        names=set(z.namelist());prefix=archive.stem+'/'
        hashes=json.loads(z.read(prefix+'sha256.json'))
        assert names=={prefix+p for p in hashes}|{prefix+'README.md',prefix+'sha256.json'},archive
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
    for device in DEVICES:check_bundle(ROOT/'dist'/('stacknest-'+device+'.zip'))
