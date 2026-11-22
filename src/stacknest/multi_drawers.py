from geometry import *
from fabrication import split_at

def orient_candidate(mesh):
    # Full-width drawers fit without seams by tilting the long axis.
    candidates=[]
    for pre in [0,90]:
        for roll in [0,90,180,-90]:
            for tilt in range(0,91,5):
                t=(trimesh.transformations.rotation_matrix(np.radians(tilt),[0,1,0]) @
                   trimesh.transformations.rotation_matrix(np.radians(roll),[1,0,0]) @
                   trimesh.transformations.rotation_matrix(np.radians(pre),[0,0,1]))
                for yaw in [0,45,90]:
                    posed=trimesh.transformations.rotation_matrix(np.radians(yaw),[0,0,1])@t
                    m=mesh.copy();m.apply_transform(posed)
                    if np.any(m.extents>np.array([250,250,260])):continue
                    shift=-m.bounds[0];m.apply_translation(shift);posed[:3,3]+=shift
                    down=m.face_normals[:,2]<-.707;up=m.triangles_center[:,2]>.25
                    support=float(m.area_faces[down&up].sum());bed=float(m.area_faces[down&~up].sum())
                    # Prefer a real planar bed face over an edge balanced on supports.
                    flat=(m.face_normals[:,2]<-.99999)&(m.triangles_center[:,2]<.01)
                    contact=float(m.area_faces[flat].sum())
                    if contact<20:continue
                    candidates.append((support-2*bed,m,posed,support,contact))
    assert candidates,('no candidate fits',mesh.extents)
    _,m,t,support,bed=min(candidates,key=lambda x:x[0])
    return m,{'transform':t.tolist(),'bounds_mm':m.extents.tolist(),'brim_mm':3,
              'support_area_mm2':support,'bed_area_mm2':bed,'slice_verified':False}


def drawer(x,w):
    from surfaces import lattice_floor
    floor=lattice_floor(x,w)
    walls=[box(x,0,8.5,w,8,51),box(x,0,8.5,6,271,51),
           box(x+w-6,0,8.5,6,271,51),box(x,265,8.5,w,6,51),
           box(x,0,6.5,w,2,2.1)]
    m=union([floor,*walls])
    handle=min(70,w-30)
    m=cut(m,rounded_xz(x+(w-handle)/2,38,handle,14,4,-1,10))
    for left in [True,False]:
        gx=x-.1 if left else x+w-2.1
        m=cut(m,box(gx,2,10,2.2,202,5))
        m=cut(m,box(gx,195.65,8.4,2.2,8.35,1.7))
    assert m.is_watertight and len(m.split())==1
    return m


def divider(x):
    wall=box(x,0,6,8,287,54)
    shelves=[box(x-4,8,6,4.1,255,2.5),box(x+7.9,8,6,4.1,255,2.5)]
    # Match the original groove/toe interface on both faces.
    toes=[box(x-2.15,20,10.35,2.65,4,4.3),box(x+7.5,20,10.35,2.65,4,4.3)]
    tabs=[box(x+1.3,y,2,5.4,12,4.1) for y in [8,267]]
    m=union([wall,*shelves,*toes,*tabs])
    assert m.is_watertight and len(m.split())==1
    return m


def middle_side(right):
    # Preserve the original vertical dovetails and the separate outer end frames.
    old=template['cassette_drawer_1']
    side=intersection(old,box(50,-1,-1,14.5,290,62))
    side=union([side,box(64.4,0,0,4.1,287,60),
                box(68.4,8,6,6.6,255,2.5),box(64.4,14,8.4,4.6,16,51.6),
                box(68,20,10.35,2.65,4,4.3)])
    for y in [-.1,266.7]:side=cut(side,box(63.2,y,2,6,20.4,4.1))
    if right:side=mirror_x(side)
    assert side.is_watertight and len(side.split())==1
    return side


def middle_beam(front):
    y=0 if front else 263
    tab_y=0 if front else 267
    tab=box(63.5,tab_y,2,5.4,20,4)
    return union([box(68.8,y,0,357.4,24,6),tab,mirror_x(tab)])


def variant(count, source_template):
    global template
    template=source_template
    parts={name:template[name].copy() for name in ['end_left_1','end_right_1']}
    parts.update(side_left=middle_side(False),side_right=middle_side(True),
                 front_beam=middle_beam(True),rear_beam=middle_beam(False))
    # Middle frame spans X60.5..434.5, with 8 mm sidewalls and 0.5 mm running gaps.
    width=(357-(count-1)*9)/count
    spans=[(69+i*(width+9),width) for i in range(count)]
    for i,(x,w) in enumerate(spans[:-1],1):
        dx=x+w+.5;parts[f'divider_{i}']=divider(dx)
        for key,y in [('front_beam',8),('rear_beam',267)]:
            parts[key]=cut(parts[key],box(dx+1,y-.3,2,6,12.6,4.1))
    for key,center in [('front_beam',12),('rear_beam',275)]:
        halves=split_at(parts.pop(key),0,247.5,[(center,12)],gap=.3)
        for i,m in enumerate(halves,1):parts[f'{key}_{i}']=m
    for prefix,direction in [('front_beam_',-1),('rear_beam_',1)]:
        for name,m in parts.items():
            if not name.startswith(prefix):continue
            for travel in [0,.3,1,5,10,20,40]:
                for side in ['side_left','side_right']:
                    assert overlap(move(m,[0,direction*travel,0]),parts[side])<.02,('beam insertion',count,name,side,travel)
    for side in ['side_left','side_right']:
        x=60.5 if side=='side_left' else 426.5
        assert abs(cut(box(x,100,20,8,.2,10),parts[side]).volume)<.01,('wall thickness',side)
        for dz in [0,1,5,30,60]:
            for end in ['end_left_1','end_right_1']:
                assert overlap(move(parts[side],[0,0,dz]),parts[end])<.02,('middle insertion',side,end,dz)
    stationary=list(parts.values())
    tests=[]
    for i,(x,w) in enumerate(spans,1):
        m=drawer(x,w)
        for travel in [0,1,30,90,150,180]:
            for key,b in parts.items():
                assert overlap(move(m,[0,-travel,0]),b)<.02,(count,i,travel,key)
        stop=sum(overlap(move(m,[0,-181,0]),b) for b in stationary)
        assert stop>.1,('stop',count,i,stop)
        for lift in np.linspace(0,7,29):
            for b in stationary:assert overlap(move(m,[0,-180,lift]),b)<.02,('lift',count,i,lift)
        for travel in np.linspace(180,300,25):
            for b in stationary:assert overlap(move(m,[0,-travel,7]),b)<.02,('remove',count,i,travel)
        parts[f'drawer_{i}']=m
        tests.append({'drawer':i,'outer_width_mm':w,'inner_width_mm':w-12,'travel_mm':180,'lift_out_mm':7,'stop_overlap_mm3':stop})
    # Closed-state part intersections, including slots and divider mounting tabs.
    for i,(an,a) in enumerate(parts.items()):
        for bn,b in list(parts.items())[i+1:]:
            assert overlap(a,b)<.02,('assembled',count,an,bn)
    # Dividers lower vertically into their two locating sockets before drawers go in.
    for name,m in parts.items():
        if not name.startswith('divider'):continue
        for dz in [0,.5,2,4,10,30,60]:
            for bn,b in parts.items():
                if bn==name or bn.startswith('drawer_'):continue
                assert overlap(move(m,[0,0,dz]),b)<.02,('divider insertion',count,name,bn,dz)
    return parts,tests

