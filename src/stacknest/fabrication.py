"""Continuous outer ends, middle side rails and crossbars; drawer and top retain existing seams."""
from geometry import *
from structure import split_carrier


def split_at(mesh, axis, plane, teeth, gap=.2):
    # Teeth lie within original material. No cosmetic floating connectors are added.
    mask=rectangle(-100,-100,plane,500) if axis==0 else rectangle(-100,-100,600,plane)
    for center,head in teeth:
        neck=head*.65
        if axis==0:
            points=[(plane-.1,center-neck/2),(plane+5,center-head/2),
                    (plane+5,center+head/2),(plane-.1,center+neck/2)]
        else:
            points=[(center-neck/2,plane-.1),(center-head/2,plane+5),
                    (center+head/2,plane+5),(center+neck/2,plane-.1)]
        mask=mask.union(Polygon(points))
    cutter=extrude(mask,-20,300)
    clearance=extrude(mask.buffer(gap,join_style=2),-20,300)
    result=[intersection(mesh,cutter),cut(mesh,clearance)]
    return [m for m in result if len(m.faces) and abs(m.volume)>1]


def sliding_profile(z,head,neck,plane=247.5,length=4):
    return Polygon([(plane,z-neck/2),(plane+length,z-head/2),
                    (plane+length,z+head/2),(plane,z+neck/2)])


def drawer_front_back_split(mesh):
    # Transverse YZ dovetails, assembled along X from the right.
    plane=135.5;gap=.3
    def transverse(profile,x,length):
        m=xz_extrude(profile,x,length)
        m.apply_transform(np.array([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]]))
        return m
    profile=sliding_profile(8.5,2,1,plane=plane,length=2)
    front=box(-10,-10,-20,520,plane+10,120)
    tongues=[transverse(profile,x-15,30) for x in [140,247.5,355]]
    mask=union([front,*tongues])
    clearance=union([box(-10,-10,-20,520,plane+10+gap,120),
                     transverse(profile.buffer(gap,join_style=2),124.7,300),
                     box(400.3,135.8,9.4,2.3,2.2,.7)])
    parts=[intersection(mesh,mask),cut(mesh,clearance)]
    assert all(m.is_watertight and len(m.split())==1 for m in parts)
    for travel in [0,.5,1,3,8,20,40,80,160,320]:
        assert overlap(move(parts[0],[travel,0,0]),parts[1])<.01,('drawer transverse assembly',travel)
    for delta in [[0,-1.5,0],[0,0,1],[0,0,-1],[-1,0,0]]:
        assert overlap(move(parts[0],delta),parts[1])>.1,('drawer capture',delta)
    return parts


def sliding_split(name,mesh):
    if name=='drawer':return drawer_front_back_split(mesh)
    # XZ dovetails slide along Y: centered in solid section, not on a thin outer lip.
    gap=.3
    plane=247.5 if name=='device_adapter' else 202.5
    left=box(-10,-10,-20,plane+10,320,120)
    if name=='device_adapter':
        profile=sliding_profile(4.25,5.5,2.5)
        tongue=xz_extrude(profile,-10,320)
        mask=union([left,tongue])
        female_clearance=union([box(-10,-10,-20,plane+10+gap,320,120),
                                xz_extrude(profile.buffer(gap,join_style=2),-10,320)])
    else:
        profile=sliding_profile(8.5,2,1,plane=plane,length=2)
        tongues=[xz_extrude(profile,y-15,30) for y in [60,135.5,211]]
        mask=union([left,*tongues])
        # A channel open at the rear accepts all three pads in one longitudinal slide.
        female_clearance=union([box(-10,-10,-20,plane+10+gap,320,120),
                                xz_extrude(profile.buffer(gap,join_style=2),44.7,260)])
    parts=[intersection(mesh,mask),cut(mesh,female_clearance)]
    assert all(p.is_watertight and p.volume>0 and len(p.split())==1 for p in parts)
    assert overlap(*parts)<.01
    for travel in ([0,1,3,8,20,40,300] if name=='drawer' else [0,1,3,8,20,40]):
        assert overlap(move(parts[0],[0,travel,0]),parts[1])<.01,(name,'longitudinal assembly blocked',travel)
    for delta in [[-1.5,0,0],[0,0,1],[0,0,-1]]:
        assert overlap(move(parts[0],delta),parts[1])>.1,(name,'dovetail does not capture',delta)
    if name=='drawer':
        assert overlap(move(parts[0],[0,-1,0]),parts[1])>.1,'drawer front stop missing'
    return parts


def segment(name,mesh):
    if name in ['device_adapter','drawer']:
        return sliding_split(name,mesh)
    if name.startswith('cassette'):
        return split_carrier(mesh)
    if name in ['end_left','end_right']:
        # Whole287mm ends fit diagonally; keep the load path free of a glue seam.
        orient(mesh)
        assert mesh.is_watertight and len(mesh.split())==1
        return [mesh]
    parts=[mesh]
    b=mesh.bounds
    # All source coordinates stay in assembly space; orientations are recorded separately.
    if mesh.extents[0]>225:
        planes=[165,330] if mesh.extents[0]>450 else [247.5]
        yfront=2.5 if name=='device_adapter' else 4
        yback=284.5 if name=='device_adapter' else (268 if name=='drawer' else 285)
        for plane in planes:
            next_parts=[]
            for m in parts:
                if m.bounds[0,0]<plane<m.bounds[1,0]:
                    next_parts.extend(split_at(m,0,plane,([(yfront,2.5)] if name=='device_adapter' else [(yfront,5),(yback,3 if name=='drawer' else 1.5)])))
                else:next_parts.append(m)
            parts=next_parts
    if mesh.extents[1]>245:
        plane=139.5 if name=='drawer' else 143.5
        if name.startswith('end'):
            xs=[(4,6),(56,6)] if mesh.bounds[0,0]<100 else [(439,6),(491,6)]
        elif name=='drawer':xs=[(95.5,3),(399.5,3)]
        elif name.startswith('cassette'):
            xs=[(75,8),(113.5 if name=='cassette_plates' else 112.5,2.5 if name=='cassette_plates' else 4),(381.5 if name=='cassette_plates' else 382.5,2.5 if name=='cassette_plates' else 4),(420,8)]
        else:xs=[(4,5),(366.5,12),(491,5)]
        next_parts=[]
        for m in parts:
            if m.bounds[0,1]<plane<m.bounds[1,1]:next_parts.extend(split_at(m,1,plane,xs))
            else:next_parts.append(m)
        parts=next_parts
    # An intermediate partition can cross voids, but exported pieces must be connected.
    connected=[]
    for m in parts:
        for piece in m.split():
            if piece.volume<25:raise AssertionError((name,'sliver',piece.volume))
            assert piece.is_watertight and piece.volume>0
            connected.append(piece)
    total=sum(m.volume for m in connected)
    assert .96*mesh.volume<=total<=mesh.volume+.1,(name,'excessive seam removal',total,mesh.volume)
    for i,a in enumerate(connected):
        for b in connected[i+1:]:assert overlap(a,b)<.01,(name,'pieces overlap')
    return connected


def orient(mesh):
    # X2D primary nozzle:256mm square, with3mm brim per side.
    candidates=[]
    for axis,angle in [([1,0,0],0),([1,0,0],np.pi),([1,0,0],np.pi/2),
                       ([1,0,0],-np.pi/2),([0,1,0],np.pi/2),([0,1,0],-np.pi/2)]:
        rot=trimesh.transformations.rotation_matrix(angle,axis)
        for yaw in [0,np.pi/2,np.pi/4]:
            t=trimesh.transformations.rotation_matrix(yaw,[0,0,1])@rot
            m=mesh.copy();m.apply_transform(t)
            shift=-m.bounds[0];m.apply_translation(shift)
            t[:3,3]+=shift
            if np.any(m.extents>np.array([250,250,260])):continue
            down=m.face_normals[:,2]<-.707
            elevated=m.triangles_center[:,2]>.25
            overhang=float(m.area_faces[down&elevated].sum())
            bed=float(m.area_faces[down&~elevated].sum())
            score=overhang-2*bed
            candidates.append((score,m,t,overhang,bed))
    if not candidates:
        # Front/back drawer halves need a compound tilt to retain the 3mm brim.
        for roll in [0,90]:
            for pitch in np.arange(46.6,46.81,.05):
                for yaw in [0,90]:
                    t=(trimesh.transformations.rotation_matrix(np.radians(yaw),[0,0,1]) @
                       trimesh.transformations.rotation_matrix(np.radians(pitch),[0,1,0]) @
                       trimesh.transformations.rotation_matrix(np.radians(roll),[1,0,0]))
                    m=mesh.copy();m.apply_transform(t)
                    if np.any(m.extents>np.array([250,250,260.6])):continue
                    shift=-m.bounds[0];m.apply_translation(shift);t[:3,3]+=shift
                    down=m.face_normals[:,2]<-.707;elevated=m.triangles_center[:,2]>.25
                    overhang=float(m.area_faces[down&elevated].sum());bed=float(m.area_faces[down&~elevated].sum())
                    candidates.append((overhang-2*bed,m,t,overhang,bed))
    assert candidates,('no printable orientation',mesh.extents.tolist())
    _,m,t,overhang,bed=min(candidates,key=lambda q:q[0])
    return m,{'assembly_to_print':t.tolist(),'bounds_mm':m.extents.tolist(),
              'downward_area_mm2':overhang,'bed_contact_area_mm2':bed,
              'supports_required':overhang>1,'brim_mm':3,'required_extruder_area_mm':[256,256]}
