"""399 mm AMS-only modules; original 60 mm ends and rear keys are reused.

PETG/FDM, 0.4 mm nozzle, 0.2 mm layers. Physical device fit remains unverified.
The plate envelope is 258 mm plus 2 mm lateral play and two 9.5 mm carriers.
"""
from geometry import *
from fabrication import split_at, sliding_profile
from surfaces import rounded_rectangle, illustrative_plate, round_lip_tips
from layer_locks import locking_profile
from shapely.affinity import translate

WIDTH=399


def plate_layer(module):
    H=module['height'];N=module['plate_count'];pitch=module['plate_pitch_mm']
    # Original dovetails are preserved, including their stopped lower ends.
    tongue=intersection(module['parts']['cassette_plates'],box(50,-1,-1,10.5,290,H+2))
    side=union([tongue,box(60.5,0,0,8,287,H)])
    for y in [-.1,266.7]:side=cut(side,box(63.2,y,2,6,20.4,4.1))
    for i in range(N):
        shelf=extrude(rounded_rectangle(68.4,0,9.1,274,1),6+i*pitch,1.5)
        side=union([side,shelf])
    stop=extrude(rounded_rectangle(62,272,22,10,2),6.3,H-8.3)
    side=union([side,stop])
    parts={'end_left':module['ends'][0].copy(),
           'end_right':move(module['ends'][1],[WIDTH-495,0,0]),
           'plate_carrier_left':side,'plate_carrier_right':mirror_x(side,WIDTH)}
    for name,y,tab_y in [('front_beam',0,0),('rear_beam',263,267)]:
        tab=box(63.5,tab_y,2,5.4,20,4)
        beam=union([box(68.8,y,0,WIDTH-137.6,24,6),tab,mirror_x(tab,WIDTH)])
        for j,m in enumerate(split_at(beam,0,WIDTH/2,[(y+12,12)],gap=.3),1):parts[f'{name}_{j}']=m
    profile=translate(illustrative_plate(),xoff=-48)
    for i in range(N):
        for dx in [-1,0,1]:
            plate=extrude(translate(profile,xoff=dx),7.5+i*pitch,1.5)
            for name,m in parts.items():
                assert overlap(plate,m)<.02,('compact plate seated',i,dx,name)
                for travel in [0,1,4,80,180,280]:
                    assert overlap(move(plate,[0,-travel,1]),m)<.02,('compact plate withdrawal',i,dx,travel,name)
            assert overlap(move(plate,[0,.3,0]),stop)>.1,('compact plate stop',i,dx)
    return parts


def split_drawer(mesh):
    # Vertical wall dovetails join two printable halves. The installed carrier
    # supports their common 2 mm floor; remove the drawer before separating them.
    x=mesh.bounds[0,0];w=mesh.extents[0]
    mask=rectangle(-10,-10,410,135.5)
    for cx in [x+3,x+w-3]:
        mask=mask.union(Polygon([(cx-.6,135.4),(cx-1.6,137.5),(cx+1.6,137.5),(cx+.6,135.4)]))
    parts=[intersection(mesh,extrude(mask,-20,100)),cut(mesh,extrude(mask.buffer(.3,join_style=2),-20,100))]
    assert len(parts)==2
    for dz in [0,.5,2,10,30,60]:assert overlap(move(parts[0],[0,0,dz]),parts[1])<.02
    for d in [[0,-1,0],[1,0,0],[-1,0,0]]:
        assert overlap(move(parts[0],d),parts[1])>.1,('compact drawer seam retention',d)
    return parts


def top_parts(common_top):
    outer=rounded_rectangle(0,0,WIDTH,287,15)
    opening=rounded_rectangle(30.5,17.5,338,254,8)
    body=extrude(outer.difference(opening),0,16)
    rim=outer.difference(outer.buffer(-3,join_style=1))
    ends=rectangle(-1,-1,60,288).union(rectangle(WIDTH-60,-1,WIDTH+1,288))
    lips=round_lip_tips(union([extrude(p,16,10) for p in rim.intersection(ends).geoms]),WIDTH)
    body=union([body,lips])
    original=union(common_top)
    foot=intersection(original,box(-1,-1,-3.1,61,289,3.1))
    body=union([body,foot,mirror_x(foot,WIDTH)])
    pocket=xz_extrude(locking_profile().buffer(.35,join_style=2),281,7)
    body=cut(body,union([pocket,mirror_x(pocket,WIDTH)]))
    male=sliding_profile(8,8,5,plane=WIDTH/2,length=5)
    female=male.buffer(.3,join_style=2)
    mask=union([box(-10,-10,-20,WIDTH/2+10,320,120),xz_extrude(male,-10,320)])
    clearance=union([box(-10,-10,-20,WIDTH/2+10.3,320,120),xz_extrude(female,-10,320)])
    parts=[intersection(body,mask),cut(body,clearance)]
    for travel in [0,.5,1,5,10,20]:assert overlap(move(parts[0],[0,travel,0]),parts[1])<.02
    for delta in [[-1.5,0,0],[0,0,1],[0,0,-1]]:
        assert overlap(move(parts[0],delta),parts[1])>.1,('compact top seam retention',delta)
    return parts
