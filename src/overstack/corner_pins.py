"""Vertical locating pins. The surrounding frame faces carry the stack load."""
from shapely.geometry import Point,LineString
from geometry import np,trimesh,move

RADIUS=3.
ENGAGEMENT=3.
CHAMFER=.4
SOCKET_DEPTH=3.5
PIN_LENGTH=6.4


def centre(right=False,back=False):
    # The centre of the former arc. A new pin also seats in the old receiver.
    x=15-7.5/np.sqrt(2)
    return (495-x if right else x,287-x if back else x)


def circle(right,back,radius):
    return Point(centre(right,back)).buffer(radius,quad_segs=16)


def turned(right,back,section):
    # Revolve a closed radial section, including the axis, into one clean solid.
    mesh=trimesh.creation.revolve(np.array(section,dtype=float),sections=64)
    return move(mesh,[*centre(right,back),0])


def fixed_pin(right,back):
    return turned(right,back,[(0,-ENGAGEMENT),(RADIUS-CHAMFER,-ENGAGEMENT),(RADIUS,-ENGAGEMENT+CHAMFER),
                                (RADIUS,.1),(0,.1)])


def loose_pin(right,back):
    return turned(right,back,[(0,-ENGAGEMENT),(RADIUS-CHAMFER,-ENGAGEMENT),(RADIUS,-ENGAGEMENT+CHAMFER),
                                (RADIUS,PIN_LENGTH-ENGAGEMENT-CHAMFER),(RADIUS-CHAMFER,PIN_LENGTH-ENGAGEMENT),
                                (0,PIN_LENGTH-ENGAGEMENT)])


def clearance(right,back):
    if back:return .7
    return .85 if right else .35


def receiver(right,back,height):
    radius=RADIUS+clearance(right,back)
    return turned(right,back,[(0,height-SOCKET_DEPTH),(radius,height-SOCKET_DEPTH),
                              (radius,height-CHAMFER),(radius+CHAMFER,height),
                              (radius+CHAMFER,height+.1),(0,height+.1)])


def top_socket(right,back):
    # A blind underside socket leaves the bearing surface intact. The conical
    # roof prints at 45 degrees and closes with a 1 mm bridge.
    r=RADIUS+.35
    return turned(right,back,[(0,-.1),(r+CHAMFER,-.1),(r+CHAMFER,0),(r,CHAMFER),
                              (r,SOCKET_DEPTH),(.5,SOCKET_DEPTH+r-.5),(0,SOCKET_DEPTH+r-.5)])


def legacy_socket(right,back):
    # Optional transition to an already printed upper frame with curved feet.
    a=np.radians(np.linspace(185,265,41))
    x=15+7.5*np.cos(a);y=15+7.5*np.sin(a)
    stem=LineString(np.column_stack((495-x if right else x,287-y if back else y))).buffer(3,quad_segs=12)
    pocket=stem.buffer(.7 if back else .35,quad_segs=12)
    if right and not back:
        from shapely.affinity import translate
        pocket=translate(pocket,xoff=-.5).union(translate(pocket,xoff=.5))
    return pocket
