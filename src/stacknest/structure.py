"""Two continuous side rails joined by two single-piece bottom crossbars."""
from geometry import *

GAP=.3
BAR_DEPTH=24
BAR_HEIGHT=6.0
SEAT_HEIGHT=2.0
FRONT_SEAT=1.8
FRONT_ENTRY_TRAVEL=29.0


def front_profile():
    # Straight T section beneath the lowest ledge; 1.2mm outer wall after clearance.
    return rectangle(111,1.8,115,4.8).union(rectangle(115,2.6,125.5,4.2))


def front_spring(pressed=False):
    # Integral accessible underside latch: 19mm free length, 1.2mm web.
    arm=box(123.3,3,.5,1.2,21,1.5)
    hook=extrude(Polygon([(123.3,20),(122.4,22),(122.4,24),(123.3,24)]),.5,1.5)
    spring=union([arm,hook])
    if pressed:
        v=spring.vertices.copy();v[:,0]+=np.clip((v[:,1]-5)/19,0,1)**2
        spring.vertices=v
    return spring


def front_bar(pressed=False):
    body=box(125.5,0,0,244,BAR_DEPTH,BAR_HEIGHT)
    left=xz_extrude(front_profile(),2,22)
    anchor=box(123.3,2,.5,3.2,3,1.5)
    return union([body,left,mirror_x(left),anchor,front_spring(pressed)])


def front_clearance():
    section=front_profile().buffer(GAP,join_style=2).intersection(rectangle(100,FRONT_SEAT,130,6))
    left=xz_extrude(section,1.7,51.6)
    # Open-bottom finger access and a short detent pocket only in the front boss.
    latch_path=box(123,1.7,-.1,2.5,51.6,2.4)
    detent=box(122.1,19.7,-.1,3.4,4.6,2.4)
    center=box(125.5,-.1,-.1,244,24.2,6.1)
    entry=box(110.7,27.7,-.1,14.8,25.6,5.2)
    return union([left,mirror_x(left),latch_path,detent,center,entry,mirror_x(entry)])


def crossbar_profile(front=True):
    y=0 if front else 287-BAR_DEPTH
    center=y+BAR_DEPTH/2
    left=Polygon([(116.5,center-9),(125.5,center-6),
                  (125.5,center+6),(116.5,center+9)])
    right=Polygon([(495-x,yy) for x,yy in left.exterior.coords])
    return rectangle(125.5,y,369.5,y+BAR_DEPTH).union(left).union(right)


def crossbar(front=True):
    if front:return front_bar()
    y=0 if front else 287-BAR_DEPTH
    beam=box(125.5,y,0,244,BAR_DEPTH,BAR_HEIGHT)
    tongues=extrude(crossbar_profile(front),SEAT_HEIGHT,BAR_HEIGHT-SEAT_HEIGHT)
    return union([beam,tongues])


def crossbar_clearance(front=True,H=60):
    if front:return front_clearance()
    y=0 if front else 287-BAR_DEPTH
    # Tongues drop from above onto a 2mm floor, even on the bottom module's feet.
    socket=extrude(crossbar_profile(front).buffer(GAP,join_style=2),SEAT_HEIGHT,H-SEAT_HEIGHT+.1)
    center=box(125.5-GAP,y-.1,-.1,244+2*GAP,BAR_DEPTH+.2,H+.2)
    return union([socket,center])


def install_structure(carrier,H):
    # Delete the old front/rear central bridges; preserve both full-length side bases.
    carrier=cut(carrier,box(116.5,-.1,-.1,262,292,H+.2))
    carrier=cut(carrier,box(60.5,277,-.1,374,30,H+.2))
    carrier=union([carrier,box(60.5,277,0,56,10,H),box(378.5,277,0,56,10,H),
                   box(109.5,0,0,16,32,BAR_HEIGHT),box(369.5,0,0,16,32,BAR_HEIGHT),
                   box(109.5,287-BAR_DEPTH,0,16,BAR_DEPTH,BAR_HEIGHT),box(369.5,287-BAR_DEPTH,0,16,BAR_DEPTH,BAR_HEIGHT),
                   crossbar(True),crossbar(False)])
    return carrier


def split_carrier(mesh):
    bars=[intersection(mesh,crossbar(front)) for front in [True,False]]
    sides=cut(mesh,union([crossbar_clearance(True,mesh.bounds[1,2]),crossbar_clearance(False,mesh.bounds[1,2])]))
    sides=sorted(sides.split(),key=lambda x:x.centroid[0])
    assert len(sides)==2,('expected two continuous sides',len(sides))
    parts=sides+bars
    assert all(p.is_watertight and p.volume>0 and len(p.split())==1 for p in parts)
    assert sum(p.volume for p in parts)>.94*mesh.volume
    for i,a in enumerate(parts):
        for b in parts[i+1:]:assert overlap(a,b)<.01
    # Front raises through the nearby bottom entry, then slides forward29mm.
    # The pressed state is a kinematic envelope, not a force/fatigue simulation.
    for travel in [0,.3,1,3,6,10,20,26,29]:
        for side in sides:
            assert overlap(move(front_bar(True),[0,travel,0]),side)<.02,('front slide blocked',travel)
    for lift in [0,-.3,-1,-3,-6,-10,-20]:
        for side in sides:
            assert overlap(move(front_bar(),[0,FRONT_ENTRY_TRAVEL,lift]),side)<.02,('bottom entry blocked',lift)
    for side in sides:
        for travel in [0,.3,1,3,6,10,20,40,60]:
            assert overlap(move(bars[1],[0,0,travel]),side)<.01,('rear top insertion blocked',travel)
    assert sum(overlap(move(bars[0],[0,1,0]),side) for side in sides)>.1,'front latch fails to retain'
    return parts
