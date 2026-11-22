"""Front-access storage with integral lift-out stops (PETG trial fits)."""
from geometry import *


def drawer_and_stops(carrier, H):
    from surfaces import lattice_floor
    floor=lattice_floor(92.5,310)
    walls=[box(92.5,0,8.5,310,8,H-9),box(92.5,0,8.5,6,271,H-9),
           box(396.5,0,8.5,6,271,H-9),box(92.5,265,8.5,310,6,H-9),box(92.5,0,8.5,310,8,3)]
    # Three underside pads support the sliding dovetail without raising the storage floor.
    pads=[box(x-20,119.5,6.3,40,32,4.45) for x in [140,247.5,355]]
    drawer=union([floor]+walls+pads+[box(92.5,0,6.5,310,2,9)])
    drawer=cut(drawer,rounded_xz(212.5,H-22,70,14,4,-1,10))
    # Continuous front-open grooves stop at Y204: tongue backY24 => travel180mm.
    groove=box(92.4,2,10,2.2,202,5)
    drawer=cut(drawer,union([groove,mirror_x(groove)]))
    # Integral toe: the drawer can be lifted off only at its open service position.
    toe=box(91.5,20,10.35,2.65,4,4.3)
    boss=box(83.5,14,3,9,16,H-3)
    stop=union([boss,toe])
    carrier=union([carrier,stop,mirror_x(stop)])
    entry=box(92.4,195.65,8.4,2.2,8.35,1.7)
    drawer=cut(drawer,union([entry,mirror_x(entry)]))
    for travel in [0,30,90,150,180]:
        assert overlap(move(drawer,[0,-travel,0]),carrier)<.01,('drawer travel',travel)
    assert overlap(move(drawer,[0,-181,0]),carrier)>1,'integral drawer stop fails'
    # Service: remove the upper module/top, pull to the stop, lift7mm, then pull free.
    for lift in np.linspace(0,7,29):
        assert overlap(move(drawer,[0,-180,lift]),carrier)<.01,('drawer lift',lift)
    for travel in np.linspace(180,300,25):
        assert overlap(move(drawer,[0,-travel,7]),carrier)<.01,('drawer removal',travel)
    return drawer,carrier


def side_bays(carrier,H):
    # 8 mm outer wall and floor; plate-bearing inner wall already measures 8 mm.
    floor=box(60.5,0,2.9,49,287,5.1)
    wall=box(64.4,0,3,4.1,283,H-3)
    carrier=union([carrier,floor,mirror_x(floor),wall,mirror_x(wall)])
    if H < 48:
        # Low plate module: the front closures belong to the side carriers.
        closure=box(68.4,0,7.9,41.2,8,H-7.9)
        return union([carrier,closure,mirror_x(closure)]),{}
    x0,x1=69.,109.
    cover=union([box(x0,0,8.5,40,4,H-9),box(x0,4,8.5,2,22,3),box(x1-2,4,8.5,2,22,3)])
    cover=cut(cover,rounded_xz(x0+8,(H+8)/2-4,24,8,2,-.1,2.8))
    for left in [True,False]:
        sx=x0 if left else x1-1.2
        beam=box(sx,3,13,1.2,20,5)
        hook=extrude(Polygon([(x0,18),(x0-.7,20),(x0-.7,21),(x0,23)]) if left else Polygon([(x1,18),(x1+.7,20),(x1+.7,21),(x1,23)]),13,5)
        cover=union([cover,beam,hook])
    recess=union([box(67.95,18.65,12.65,1.05,3.7,5.7),box(109,18.65,12.65,1.05,3.7,5.7)])
    carrier=cut(carrier,union([recess,mirror_x(recess)]))
    bin_mesh=union([box(x0,0,8.5,40,140,2),box(x0,0,8.5,3,140,H-9.5),
                    box(x1-3,0,8.5,3,140,H-9.5),box(x0,138,8.5,40,2,H-9.5),
                    box(x0,0,8.5,40,4,H-9)])
    bin_mesh=cut(bin_mesh,rounded_xz(x0+8,H-18,24,10,3,-1,6))
    bin_mesh=cut(bin_mesh,box(x0-.1,-1,15,1.2,75,5))
    toe=box(68.2,12,15.35,1.6,2,4.3)
    boss=box(64.5,8,8,4,10,H-8)
    stop=union([boss,toe]);carrier=union([carrier,stop,mirror_x(stop)])
    bin_mesh=cut(bin_mesh,box(x0-.1,67.65,8.4,1.2,6.35,6.7))
    cover=cut(cover,box(68.85,11.65,15,1.55,2.7,5))
    assert overlap(carrier,cover)<.01,'cover seated interference'
    for travel in [0,20,40,60]:
        assert overlap(move(bin_mesh,[0,-travel,0]),carrier)<.01,('side bin travel',travel)
    assert overlap(move(bin_mesh,[0,-61,0]),carrier)>.1,'side bin stop fails'
    for lift in np.linspace(0,12,49):
        assert overlap(move(bin_mesh,[0,-60,lift]),carrier)<.01,('side bin lift',lift)
    for travel in np.linspace(60,160,21):
        assert overlap(move(bin_mesh,[0,-travel,12]),carrier)<.01,('side bin removal',travel)
    assert all(m.is_watertight and len(m.split())==1 for m in [cover,bin_mesh])
    return carrier,{'side_cover_left':cover,'side_cover_right':mirror_x(cover),
                    'side_bin_left':bin_mesh,'side_bin_right':mirror_x(bin_mesh)}
