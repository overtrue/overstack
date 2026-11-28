"""Try the one printable bowtie in every rear connection, using the exported solids."""
import hashlib,json,re,sys,zipfile
from functools import cache
from pathlib import Path
from shapely import box,intersects,linestrings

from build_print_profiles import ROOT,canonical_recipes
from geometry import cut,move,np,overlap,trimesh
from ht_layers import LAYERS
from layer_locks import REAR_LOCK_FILE
from print_profile_targets import TARGETS
from verify_front_pin_slices import paths


@cache
def mesh(file):
    return trimesh.load_mesh(ROOT/file)


spare=mesh(REAR_LOCK_FILE)
assert spare.is_volume and len(spare.split())==1 and np.allclose(spare.extents,[12,16,5.3])
assert abs(spare.bounds[0,2])<.0001
seated=move(spare,-spare.bounds.mean(axis=0))
seated.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
for axis in ([0,1,0],[1,0,0]):
    flipped=seated.copy()
    flipped.apply_transform(trimesh.transformations.rotation_matrix(np.pi,axis))
    assert cut(flipped,seated).volume+cut(seated,flipped).volume<.001

# A prism extended straight back covers the entire insertion and withdrawal path.
sweep=seated.copy()
vertices=sweep.vertices.copy()
vertices[vertices[:,1]>0,1]+=20
sweep.vertices=vertices


def socket(parts,x,z,upper):
    path=move(sweep,[x,284,z])
    assert all(overlap(path,p)<.01 for p in parts),(x,z,upper,'blocked insertion')
    lifted=move(seated,[x,284,z+(-.8 if upper else .8)])
    assert any(overlap(lifted,p)>.1 for p in parts),(x,z,upper,'missing retaining shoulder')


def layer(rows,width,height):
    parts=[];centres=[]
    for row in rows:
        part=move(mesh(row['file']),row.get('offset_mm',[0,0,0]))
        if row.get('print_file')==REAR_LOCK_FILE:
            centre=part.bounds.mean(axis=0)
            aligned=move(seated,centre)
            assert cut(aligned,part).volume+cut(part,aligned).volume<.005,(row['id'],'different bowtie')
            centres.append(centre.tolist())
        else:
            parts.append(part)
    assert len(centres)==2 and np.allclose(sorted(centres),[[38,284,0],[width-38,284,0]],atol=.001),centres
    for x in (38,width-38):
        socket(parts,x,0,upper=True)
        if height:socket(parts,x,height,upper=False)


def check_slices(manifest):
    report=json.loads(manifest.read_text())
    keys={p['id']+'-'+Path(p['source']).stem for p in report['parts'] if p.get('print_file')==REAR_LOCK_FILE}
    if not keys:return 0,0
    folder=manifest.parent
    work=ROOT/'output'/folder.relative_to(ROOT)
    groups=json.loads((work/'assembly.json').read_text())['plates']
    target=TARGETS[report['printer_key']]
    x0,y0,x1,y1=target['area']
    base=json.loads((folder/'slice-validation.json').read_text())
    archives={'sliced.3mf':{p['file']:p['sha256'] for p in base['plates']}}
    if target['group']=='256':
        matte=json.loads((folder/'matte-slice.json').read_text())
        archives['matte/sliced.3mf']={f'Metadata/plate_{p["plate"]}.gcode':p['gcode_sha256'] for p in matte['gcode']}
    for archive,hashes in archives.items():
        checked=set()
        with zipfile.ZipFile(work/archive) as z:
            for i,plate in enumerate(groups,1):
                bounds={}
                for obj in plate['objects']:
                    name=Path(obj['path']).stem
                    if name in keys:
                        x=(x0+x1)/2+obj['pos_x'][0];y=(y0+y1)/2+obj['pos_y'][0]
                        bounds[name]=(x-6.3,y-8.3,x+6.3,y+8.3)
                if not bounds:continue
                meta=json.loads(z.read(f'Metadata/plate_{i}.json'))
                for name in bounds:
                    first=[o for o in meta['bbox_objects'] if o['name'].startswith(name+'_')]
                    assert len(first)==1 and np.isclose(first[0]['area'],162,atol=.02),(manifest,name,'first layer')
                member=f'Metadata/plate_{i}.gcode';gcode=z.read(member)
                assert hashlib.sha256(gcode).hexdigest()==hashes[member],(manifest,archive,member)
                # The 5.3 mm spare lies flat. Inspect through its final possible layer.
                stop=next((m.start() for m in re.finditer(rb'^; Z_HEIGHT: ([\d.]+)',gcode,re.M) if float(m[1])>5.4),len(gcode))
                supports=[];walls={name:set() for name in bounds}
                for feature,height,a,b in paths(gcode[:stop]):
                    if feature in (b'Support',b'Support interface'):
                        supports.append((a,b))
                    else:
                        for name,(xmin,ymin,xmax,ymax) in bounds.items():
                            if xmin<a[0]<xmax and ymin<a[1]<ymax and xmin<b[0]<xmax and ymin<b[1]<ymax:
                                walls[name].add(height)
                lines=linestrings(np.asarray(supports).reshape(-1,2,2))
                for name,rect in bounds.items():
                    assert not intersects(lines,box(*rect)).any(),(manifest,archive,i,name,'support touching key')
                    assert {round(h*.2,2) for h in range(1,27)}<=walls[name],(manifest,archive,i,name,'missing outer wall')
                checked.update(bounds)
        assert checked==keys,(manifest,archive,'missing sliced rear key')
    return len(archives),len(keys)*len(archives)


if __name__=='__main__':
    large=dict(canonical_recipes());small=ROOT/'models/256'
    compact=json.loads((ROOT/'models/ams2pro/validation.json').read_text())['layers']
    families=[('ams2pro/'+r['name'],399,None if r['name']=='device-top' else r['height_mm']) for r in compact]
    families += [('ams2pro-ht/'+slug,495,{'A':40,'B':60,'D':60,'E':60,'F':None}[prefix]) for prefix,slug,_ in LAYERS]
    for name,width,height in families:
        layer(large[name],width,height)
        layer(json.loads((small/name/'parts.json').read_text()),width,height)
    for h in (40,60):
        for width in (399,495):
            for side,x in [('left',38),('right',width-38)]:
                end=move(mesh(f'models/common/end_{side}_{h}_pegboard.stl'),[width-495 if side=='right' else 0,0,0])
                socket([end],x,0,True)
                socket([end],x,h,False)
        adapter=json.loads((small/f'compatibility/ht-right-{h}/parts.json').read_text())
        parts=[mesh(r['file']) for r in adapter]
        socket(parts,457,0,True)
        socket(parts,457,h,False)
    for profile,x,lower,upper in [('fit-check/interfaces',38,'FIT05','FIT06'),('fit-check/ht-top',457,'HT01','HT02')]:
        pieces={r['id']:mesh(r['file']) for r in large[profile]}
        socket([pieces[lower]],x,0,False)
        socket([pieces[upper]],x,0,True)
    print('PASS: one reversible bowtie, 10 layers on both bed sizes, both pegboard heights and widths, both transition ends and both fit sets')
    if '--slices' in sys.argv:
        totals=np.sum([check_slices(p) for p in sorted((ROOT/'print-profiles').rglob('manifest.json'))],axis=0)
        print(f'PASS: {totals[0]} sliced projects, {totals[1]} flat rear keys with outer walls and no support contact')
