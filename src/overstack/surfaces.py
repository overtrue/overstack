"""Analytic surfaces. No mesh, section tracing or vendor model is an input."""
from geometry import *
from corner_pins import fixed_pin
from fabrication import sliding_profile
from layer_locks import lock_pocket


def rounded_rectangle(x,y,w,d,r):
    return rectangle(x+r,y+r,x+w-r,y+d-r).buffer(r,quad_segs=16)


def solid_floor(x,width):
    """Continuous 2 mm floor, retaining the existing underside datum."""
    return box(x,0,8.5,width,271,2)


def round_lip_tips(lips,width):
    """R3 on the four exposed upper lip ends; keep the z16 bearing face intact."""
    from shapely.geometry import Point
    corner=rectangle(57,23,60,26).difference(Point(57,23).buffer(3,quad_segs=24))
    tool=xz_extrude(corner,-1,289)
    return cut(lips,union([tool,mirror_x(tool,width)]))


def top_parts():
    """495 x 287 mm bearing frame, independent stepped HT opening and locating lips."""
    outer=rounded_rectangle(0,0,495,287,15)
    ams=rounded_rectangle(18.5,17.5,338,254,8)
    ht=rounded_rectangle(382.15,17.5,97.35,254,8)
    ring=outer.difference(ams.union(ht))
    body=extrude(ring,0,16)
    body=cut(body,extrude(ht.buffer(6,quad_segs=16),10.5,20))
    # Simple 3 mm perimeter lips at both ends; no imported device-shaped surface.
    rim=outer.difference(outer.buffer(-3,join_style=1))
    ends=rectangle(-1,-1,60,288).union(rectangle(435,-1,496,288))
    lips=round_lip_tips(union([extrude(p,16,10) for p in rim.intersection(ends).geoms]),495)
    separator=extrude(rounded_rectangle(371.5,126,4.65,42,1),16,5.5)
    feet=[]
    for right,back in [(False,False),(True,False),(False,True),(True,True)]:
        feet.append(fixed_pin(right,back))
    body=union([body,lips,separator,*feet])
    pocket=lock_pocket()
    body=cut(body,union([pocket,mirror_x(pocket)]))
    male=sliding_profile(8,8,5,length=5)
    female=male.buffer(.3,join_style=2)
    mask=union([box(-10,-10,-20,257.5,320,120),xz_extrude(male,-10,150),xz_extrude(male,140,170)])
    clearance=union([box(-10,-10,-20,257.8,320,120),xz_extrude(female,-10,150),xz_extrude(female,140,170)])
    parts=[intersection(body,mask),cut(body,clearance)]
    assert all(p.is_volume and len(p.split())==1 for p in parts)
    for dx in [-40,-20,-10,-5,-1,0]:
        assert overlap(move(parts[0],[dx,20,0]),parts[1])<.01,('top lateral insertion',dx)
    for travel in np.linspace(0,20,41):
        assert overlap(move(parts[0],[0,travel,0]),parts[1])<.01,('top slide',travel)
    for region in [box(240,0,-1,20,30,35),box(240,260,-1,20,30,35)]:
        left=intersection(parts[0],region);right=intersection(parts[1],region)
        for delta in [[-1.5,0,0],[0,0,1],[0,0,-1]]:
            assert overlap(move(left,delta),right)>.1,('top capture',delta)
    return parts


def illustrative_plate():
    """Nominal outline for explanatory graphics; NOT a manufacturing drawing."""
    body=rounded_rectangle(118.5,14,258,258,3)
    front=rounded_rectangle(220,4,55,13,3)
    rear=rounded_rectangle(230,269,35,11,2)
    return body.union(front).union(rear)
