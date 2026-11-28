"""Check the exported HT top against the original left half, rear key and end frames."""
from pathlib import Path
import json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import box,cut,intersection,mirror_x,move,np,overlap,trimesh,union,xz_extrude
from shapely import Polygon,union_all
from surfaces import top_parts
from corner_pins import centre,loose_pin,legacy_socket,SOCKET_DEPTH,PIN_LENGTH

folder=ROOT/'models/ams2pro+ht/06-device-top/parts'
pieces={p.name[:3]:trimesh.load_mesh(p) for p in folder.glob('*.stl')}
assert set(pieces)=={f'F{i:02d}' for i in range(1,8)}
left,front,key,rear,front_foot,rear_foot=[pieces[k] for k in ('F01','F02','F04','F05','F06','F07')]
original_left,blank=top_parts()
assert cut(left,original_left).volume<.02 and cut(original_left,left).volume<.02
right=union([front,rear,front_foot,rear_foot])
assert cut(right,blank).volume<.02,'new material enters an original device or interface clearance'
for section,foot in [(front,front_foot),(rear,rear_foot)]:
    assert np.isclose(section.bounds[0,2],0) and section.extents[2]<=26.001
    planar=(section.face_normals[:,2]<-.99999)&(section.triangles_center[:,2]<.001)
    assert section.area_faces[planar].sum()>9000,'loss of flat first-layer contact'
    assert np.allclose(foot.bounds[:,2],[-3,3.4],atol=.001)
    c=foot.bounds.mean(axis=0)
    for yaw in (0,17,45,91,180,271):
        for flip in (0,180):
            test=foot.copy()
            for axis,angle in [([1,0,0],flip),([0,0,1],yaw)]:
                test.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle),axis,point=c))
            assert overlap(test,section)<.01
    for z in np.arange(0,28,.5):assert overlap(move(section,[0,0,z]),foot)<.01,('top lowered onto dowel',z)
    assert overlap(section,move(foot,[0,0,2]))>1,'blind socket roof missing'
assert np.allclose(front_foot.extents,rear_foot.extents,atol=.001)
for pin in (front_foot,rear_foot):
    assert np.allclose(pin.extents,[6,6,6.4],atol=.001)
    # A dowel resting on a receiver bottom still engages the upper socket.
    assert PIN_LENGTH-SOCKET_DEPTH>2.8

for z in np.arange(0,28,.5):assert overlap(move(front,[0,0,z]),rear)<.01,('rail join',z)
for direction in [[0,-1,0],[-1,0,0],[1,0,0]]:
    assert overlap(move(front,direction),rear)>1,'rail tails do not hold in plane'
for dx in [-40,-20,-5,0]:assert overlap(move(left,[dx,20,0]),right)<.02
for y in np.arange(0,20.5,.5):assert overlap(move(left,[0,y,0]),right)<.02
for region in [box(240,0,-1,20,30,35),box(240,260,-1,20,30,35)]:
    a,b=intersection(left,region),intersection(right,region)
    for d in [[-1.5,0,0],[0,0,1],[0,0,-1]]:assert overlap(move(a,d),b)>.1,'old F01 lost capture'
# Compare exported solids by translation alone, like moving a printed part
# across the frame. Keep both assembly position IDs and a single print shape.
common=trimesh.load_mesh(ROOT/'models/common/lock_left.stl')
wide=ROOT/'models/ams2pro+ht'
keys=[wide/r['packaged_file'] for r in json.loads((wide/'parts.json').read_text())
      if 'layer_lock' in r['name'] or r['name'].startswith('top_rear_lock')]
keys.extend([ROOT/'models/common/lock_right.stl',ROOT/'models/fit-check/HT03-rear-key.stl'])
for path in keys:
    other=trimesh.load_mesh(path)
    aligned=move(common,other.bounds.mean(axis=0)-common.bounds.mean(axis=0))
    assert cut(aligned,other).volume+cut(other,aligned).volume<.002,(path,'different rear key')
for h in (40,60):
    for style in ('plain','pegboard'):
        for hand,section in [('left',left),('right',rear)]:
            end=move(trimesh.load_mesh(ROOT/'models/common'/f'end_{hand}_{h}_{style}.stl'),[0,0,-h])
            for z in [0,.3,1,3,8,28]:
                assert overlap(end,move(section,[0,0,z]))<.02
            for printed in (pieces['F03'],key):
                pos=[38 if hand=='left' else 457,284,0]
                seated=move(printed,pos-printed.bounds.mean(axis=0))
                for angle in (0,np.pi):
                    rotated=seated.copy()
                    rotated.apply_transform(trimesh.transformations.rotation_matrix(angle,[0,1,0],point=pos))
                    for y in (0,.5,1,3,6,9,12):
                        sliding=move(rotated,[0,y,0])
                        assert overlap(sliding,end)<.01 and overlap(sliding,section)<.01
                    assert overlap(rotated,move(end,[0,0,-.8]))>.1
                    assert overlap(rotated,move(section,[0,0,.8]))>.1
# The waist and retaining shoulders must match the standard 0.35 mm clearance.
# Only the ceiling above the upper end is relieved for bed-flat printing.
key_face=union_all([Polygon(t[:,[0,2]]) for t in key.triangles[key.face_normals[:,1]>.999]])
opening=xz_extrude(key_face.buffer(.35,join_style='mitre'),281,6)
mouth=box(449,281,0,16,6,8.35)
expected=cut(mouth,opening)
actual=intersection(mouth,rear)
assert cut(expected,actual).volume+cut(actual,expected).volume<.005,'F05 seat differs from the common key'
centres=rear.triangles_center
roof=(abs(centres[:,0]-457)<7)&(centres[:,1]>281)&(centres[:,2]>8.35)&(rear.face_normals[:,2]<-.01)
normals=rear.face_normals[roof]
slopes=normals[normals[:,2]>-.99]
assert len(slopes) and np.allclose(abs(slopes[:,0]),-slopes[:,2],atol=.001),'rear pocket roof slopes'
crown=rear.triangles[roof][normals[:,2]<-.99]
assert np.isclose(np.ptp(crown[:,:,0]),1.5,atol=.005),'F05 roof bridge'
assert np.isclose(crown[:,:,2].max(),13.95,atol=.005),'F05 roof height'
cover=box(450.66,281.01,13.96,12.68,5.98,2.03)
assert cut(cover,rear).volume<.005,'loss of material above rear socket'
print('PASS: bed contact, feet and rail joints, one reversible rear key in both slots, 40/60 mm plain and pegboard ends, 45-degree roof, 1.5 mm bridge')
