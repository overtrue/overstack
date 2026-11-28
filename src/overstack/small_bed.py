"""Tool-free front/rear splits for the 256 mm print bed (assembly coordinates)."""
from geometry import Polygon, rectangle, extrude, intersection, cut, move, overlap, union


def tail(cx, seam, neck, head, depth):
    profile=Polygon([(cx-neck,seam-1),(cx-neck,seam+.6),(cx-head,seam+depth-1.6),
                     (cx-head,seam+depth),(cx+head,seam+depth),(cx+head,seam+depth-1.6),
                     (cx+neck,seam+.6),(cx+neck,seam-1)])
    return profile.buffer(-.32,join_style='round').buffer(.32,quad_segs=4)


def split(mesh, family, right=False):
    lo,hi=mesh.bounds
    def outside(offset):
        return hi[0]-offset if right else lo[0]+offset
    seam=(lo[1]+hi[1])/2
    if family=='drawer':
        spec=[(lo[0]+3,1,1.85,5),(hi[0]-3,1,1.85,5)]
        # Wide floor fingers share load and keep the thin floor flush even
        # between the sidewalls. All fingers engage in the same downward motion.
        n=max(1,round((hi[0]-lo[0]-30)/48))
        spec.extend((lo[0]+(hi[0]-lo[0])*(i+.5)/n,5,8,7) for i in range(n))
    elif family=='end':spec=[(outside(6),2.0,3.7,6)]
    elif family=='carrier':
        # The wide cassette has two parallel walls and a continuous floor.
        # Centre the tails in each spine and the clear floor between them.
        if hi[0]-lo[0]>50:spec=[(outside(10.2),1.7,2.7,6),(outside(33),4,7,8),(outside(59.2),1.7,2.8,6)]
        else:spec=[(outside(10.2),1.7,2.7,6)]
    elif family=='top':spec=[(outside(10),2.5,4.8,7)]
    elif family=='divider':spec=[((lo[0]+hi[0])/2,1.7,2.7,6)]
    else:raise ValueError(family)
    front=rectangle(lo[0]-2,lo[1]-2,hi[0]+2,seam)
    for x,neck,head,depth in spec:front=front.union(tail(x,seam,neck,head,depth))
    z=lo[2]-2;height=hi[2]-z+2
    male=extrude(front,z,height)
    open_front=front.buffer(.30,join_style='round',quad_segs=4)
    female=extrude(open_front,z,height)
    if family=='drawer':
        # Overlap the 2 mm floor across the entire seam. The rear ledge bears
        # under the front lip; loose fasteners cannot fall through the XY gap.
        floor_band=rectangle(lo[0]+6.4,seam-2,hi[0]-6.4,seam+13)
        floor_mask=rectangle(lo[0]-2,lo[1]-2,hi[0]+2,seam)
        for x,neck,head,depth in spec[2:]:
            floor_mask=floor_mask.union(tail(x,seam,neck,head,depth))
        lip=floor_mask.buffer(3.,join_style='round',quad_segs=4).intersection(floor_band)
        male=union([male,extrude(lip,9.6,.9)])
        female=union([female,extrude(lip.buffer(.30,quad_segs=4),9.4,1.1)])
    a=intersection(mesh,male)
    b=cut(mesh,female)
    assert all(p.is_volume and len(p.split())==1 for p in (a,b)),(family,lo,hi,'disconnected')
    # These cross-sections are constant at the seam. Every normal insertion
    # height clears; after seating, both lateral directions and pull-apart bind.
    for dz in [0,.3,2,8,hi[2]-lo[2]+1]:
        assert overlap(move(a,[0,0,dz]),b)<.025,(family,'vertical insertion',dz)
    for delta in ([0,-1.5,0],[1.5,0,0],[-1.5,0,0]):
        assert overlap(move(a,delta),b)>.10,(family,'unretained',delta)
    assert a.volume+b.volume>mesh.volume*.98,(family,'excessive clearance')
    return a,b
