"""Test the shipped 256 mm parts in assembly coordinates, including the old right top."""
import json,sys
from pathlib import Path
from shapely import polygons,union_all,box as window
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import box,cut,extrude,intersection,mirror_x,move,np,overlap,trimesh,union
from corner_pins import circle,centre,fixed_pin,legacy_socket,loose_pin,receiver
from build_print_profiles import canonical_recipes


def mesh(row):return trimesh.load_mesh(ROOT/row['file'])


def geometry(p):
    assert p.is_volume and p.is_watertight and len(p.split())==1


def projection(p):
    triangles=p.triangles[p.face_normals[:,2]>.001,:,:2]
    return union_all(polygons(triangles),grid_size=.00001)


def check_layers():
    total=0
    for key,parents in canonical_recipes():
        if not key.startswith(('ams2pro/','ams2pro-ht/')):continue
        rows=json.loads((ROOT/'models/256'/key/'parts.json').read_text())
        original={r['id']:r for r in parents};pieces={}
        assert {i for row in rows for i in row.get('parent_ids',[row['id']])}==set(original),(key,'coverage')
        for row in rows:
            p=mesh(row);geometry(p);ident=row['id'];ids=row.get('parent_ids',[ident])
            if len(ids)==1 and ident!=ids[0]:
                parent=mesh(original[ids[0]])
                assert cut(p,parent).volume<.035,(key,ident,'outside functional geometry')
                if ident.endswith('a') and '_drawer_' in ('_'+Path(original[ids[0]]['file']).stem):
                    back=next(r for r in rows if r['id']==ids[0]+'b')
                    other=mesh(back);lo,hi=parent.bounds;y=(lo[1]+hi[1])/2
                    band=box(lo[0]+6.5,y-1,8.49,hi[0]-lo[0]-13,13,2.02)
                    cover=projection(intersection(p,band)).union(projection(intersection(other,band)))
                    query=window(lo[0]+6.51,y-.99,hi[0]-.01-6.5,y+11.99)
                    assert query.difference(cover).area<.01,(key,ident,'open floor seam')
            offset=original[ids[0]].get('offset_mm',[0,0,0])
            if key.startswith('ams2pro/') and ident=='KEY-right':offset=[-96,0,0]
            pieces[ident]=move(p,offset)
        pairs=0
        for i,(aid,a) in enumerate(pieces.items()):
            for bid,b in list(pieces.items())[i+1:]:
                assert overlap(a,b)<.035,(key,aid,bid,'assembly collision')
                pairs+=1
        total+=pairs
        print(key,len(rows),'pieces,',pairs,'pairs',flush=True)
    return total


def check_pins():
    for height in (40,60):
        for hand in ('left','right'):
            right=hand=='right'
            for style in ('plain','pegboard'):
                name=f'end_{hand}_{height}_{style}'
                end=trimesh.load_mesh(ROOT/'models/common'/(name+'.stl'))
                for back in (False,True):
                    fixed=fixed_pin(right,back);c=centre(right,back)
                    crop=box(c[0]-6,c[1]-6,-3.1,12,12,3.1)
                    foot=intersection(end,crop);assert cut(foot,fixed).volume+cut(intersection(fixed,crop),foot).volume<.001
                    hole=receiver(right,back,height)
                    assert overlap(hole,end)<.01
                    for part in (fixed,loose_pin(right,back)):
                        for dz in (0,.3,1,3,5):
                            assert overlap(move(part,[0,0,height+dz]),end)<.01
                    # New pins still fit inside an earlier nominal corner socket.
                    assert legacy_socket(right,back).covers(circle(right,back,3))
                if style=='plain' and right:
                    folder=ROOT/'models/256/compatibility'/f'ht-right-{height}'
                    assembled=union([mesh(r) for r in json.loads((folder/'parts.json').read_text())])
                    for back in (False,True):
                        hole=legacy_socket(True,back)
                        assert overlap(extrude(hole,height-3.499,3.499),assembled)<.02
                        wall=hole.buffer(1.2).difference(hole.buffer(.005))
                        # The round production entry has a 0.4 mm mouth chamfer.
                        ring=extrude(wall,height-3,2)
                        assert cut(ring,assembled).volume<.03,'transition socket wall'
                if style=='pegboard':
                    folder=ROOT/'models/256/common'/f'pegboard-{height}'
                    joined=union([mesh(r) for r in json.loads((folder/'parts.json').read_text()) if name in r['parent_ids']])
                    for y in np.arange(43.5,244,40):
                        for z in range(10,height,20):
                            access=box(5.1,y-3,z-8,20,6,16)
                            assert overlap(mirror_x(access) if right else access,joined)<.02
                    original=trimesh.load_mesh(ROOT/'models/common'/f'end_{hand}_{height}_plain.stl')
                    assert cut(joined,original).volume<.03
    top=ROOT/'models/ams2pro+ht/06-device-top/parts'
    front,rear=[trimesh.load_mesh(next(top.glob(i+'-*.stl'))) for i in ('F06','F07')]
    expected=move(front,[0,centre(True,True)[1]-centre(True,False)[1],0])
    assert cut(expected,rear).volume+cut(rear,expected).volume<.001,'pins differ'
    for back,part,ident in [(False,front,'F02'),(True,rear,'F05')]:
        section=trimesh.load_mesh(next(top.glob(ident+'-*.stl')))
        for yaw in range(0,360,5):
            m=part.copy()
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(yaw),[0,0,1],point=[*centre(True,back),0]))
            assert overlap(m,section)<.01
        for dz in [0,.5,1,3,6,12,30]:assert overlap(move(section,[0,0,dz]),part)<.01
    print('PASS: 40/60 mm plain and pegboard corners, both widths, old top receivers, dismounting and circular pins')

if __name__=='__main__':
    pairs=check_layers();check_pins();print('PASS:',pairs,'assembled part pairs')
