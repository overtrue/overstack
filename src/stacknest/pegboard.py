"""SKADIS-style common ends: 5 x 15 mm slots, R2.5, 5 mm panel.

40 mm repeat with 20 mm stagger; each layer is an independent accessory zone.
PETG/FDM 0.4 mm nozzle, 0.2 mm layer. Hook fit and load need a printed coupon.
"""
from geometry import *
from shapely.geometry import LineString


def yz_extrude(profile,x,depth):
    m=extrude(profile,0,depth)
    m.apply_transform(np.array([[0,0,1,x],[1,0,0,0],[0,1,0,0],[0,0,0,1]],float))
    return m


def slot_centers(H):
    if H==30:return [(y,15) for y in np.arange(43.5,244,40)]
    if H==60:return [(y,z) for y0,z in [(43.5,10),(63.5,30),(43.5,50)] for y in np.arange(y0,244,40)]
    raise ValueError('Common ends have 30 or 60 mm height')


def end(module,right=False):
    H=module['height'];original=mirror_x(module['ends'][1]) if right else module['ends'][0]
    # Recess behind the outer panel, avoiding corner sockets, rear locks and
    # inner dovetails. The open end cavity gives hooks over 20 mm rear clearance.
    recess=rectangle(27,2,260,H-2).buffer(2,quad_segs=12)
    m=cut(original,yz_extrude(recess,5,25))
    for y,z in slot_centers(H):
        slot=LineString([(y,z-5),(y,z+5)]).buffer(2.5,quad_segs=16)
        m=cut(m,yz_extrude(slot,-.1,5.2))
        assert overlap(m,box(5.1,y-3,z-8,20,6,16))<.01,('hook rear clearance',H,y,z)
    assert m.is_volume and len(m.split())==1
    # All material changed lies in the side panel; connection regions are exact.
    protected=[box(35,-1,-4,26,289,H+5),box(-1,-1,-4,62,25,H+5),box(-1,263,-4,62,25,H+5)]
    for region in protected:
        assert abs(intersection(original,region).volume-intersection(m,region).volume)<.01
    return mirror_x(m) if right else m


def coupon():
    profile=rectangle(3,3,77,77).buffer(3,quad_segs=12)
    panel=extrude(profile,0,5)
    for x,y in [(20,20),(60,20),(40,40),(20,60),(60,60)]:
        hole=LineString([(x,y-5),(x,y+5)]).buffer(2.5,quad_segs=16)
        panel=cut(panel,extrude(hole,-.1,5.2))
    return panel
