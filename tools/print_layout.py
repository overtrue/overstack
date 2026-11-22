"""Support-first orientation and brim-aware footprint packing for print profiles."""
from geometry import np,trimesh
from shapely.geometry import MultiPoint
from shapely.affinity import translate


def orient_for_area(mesh,area,height,preferred_yaw=None,rotation=None):
    x0,y0,x1,y1=area;limit=np.array([x1-x0-6,y1-y0-6,height])
    candidates=[]
    yaw_order=([preferred_yaw] if preferred_yaw is not None else [])+[0,90,45,40,50]
    yaw_order+= [a for a in range(0,91,5) if a not in yaw_order]
    rotations=[rotation] if rotation is not None else [([1,0,0],0),([1,0,0],180),
        ([1,0,0],90),([1,0,0],-90),([0,1,0],90),([0,1,0],-90)]
    for axis,angle in rotations:
        for yaw in range(0,91,5):
            t=trimesh.transformations.rotation_matrix(np.radians(yaw),[0,0,1])@trimesh.transformations.rotation_matrix(np.radians(angle),axis)
            m=mesh.copy();m.apply_transform(t)
            if np.any(m.extents>limit+1e-6):continue
            shift=-m.bounds[0];m.apply_translation(shift);t[:3,3]+=shift
            down=m.face_normals[:,2]<-.707;elevated=m.triangles_center[:,2]>.25
            overhang=float(m.area_faces[down&elevated].sum())
            flat=(m.face_normals[:,2]<-.99999)&(m.triangles_center[:,2]<.01)
            bed=float(m.area_faces[flat].sum())
            if bed<1:continue
            # Estimate support columns, rather than comparing overhang area alone.
            column=float((m.area_faces[down&elevated]*m.triangles_center[down&elevated,2]).sum())
            # Broad contact surfaces also cost interface material and cleanup.
            score=(round(column+5*overhang,1),float(m.extents[2]),-round(bed,1),yaw_order.index(yaw),round(float(np.prod(m.extents[:2])),1))
            candidates.append((score,m,t,overhang,bed,column))
    assert candidates,('no fitting planar orientation',mesh.extents.tolist())
    # Thin plates/straps should rest on a broad face. A small ledge's support
    # saving does not justify standing the whole plate on its narrow edge.
    dimensions=sorted(mesh.extents)
    # Do not stand long rails on their short ends when a lower pose fits.
    if dimensions[2]>2*dimensions[1]:
        lower=[c for c in candidates if c[1].extents[2]<=dimensions[1]+1e-6]
        if lower:candidates=lower
    if dimensions[0]*4<=dimensions[1]+1e-6:
        flat=[c for c in candidates if c[1].extents[2]<=dimensions[0]+1e-6
              and c[4]>=MultiPoint(c[1].vertices[:,:2]).convex_hull.area*.5]
        if flat:candidates=flat
    # A small overhang high above the bed can cost more than a broad shallow gap.
    # Within 10% of the estimated support cost, prefer fewer layers; actual slice time
    # and material are checked separately before a profile is accepted.
    minimum=min(c[0][0] for c in candidates)
    candidates=[c for c in candidates if c[0][0]<=minimum*1.1+1]
    score,m,t,overhang,bed,column=min(candidates,key=lambda c:(c[0][1],c[0][0],*c[0][2:]))
    return m,{'assembly_to_print':t.tolist(),'bounds_mm':m.extents.tolist(),
              'downward_area_mm2':overhang,'bed_contact_area_mm2':bed,'support_column_estimate_mm3':column,
              'supports_required':overhang>1,'brim_mm':3,
              'required_extruder_area_mm':[x1-x0,y1-y0]}


def pack(inputs,parts,target):
    """First-fit convex footprints, expanded for brim and tree-support clearance."""
    x0,y0,x1,y1=target['area']
    plates=[];footprints=[]
    for path,part in zip(inputs,parts):
        mesh=trimesh.load_mesh(path)
        height=part['bounds_mm'][2]
        clearance=part['brim_mm']+.5
        if part['supports_required'] and height>10:clearance+=min(12,height*.25)
        hull=MultiPoint(mesh.vertices[:,:2]).convex_hull.buffer(clearance)
        minx,miny,maxx,maxy=hull.bounds
        separate=maxx-minx>x1-x0 or maxy-miny>y1-y0
        obj={'path':path,'count':1,'filaments':[1]}
        placed=False
        if not separate:
            for objects,occupied,exclusive in zip(plates,footprints,[any(o.get('_exclusive') for o in p) for p in plates]):
                if exclusive:continue
                minx,miny,maxx,maxy=hull.bounds
                for y in np.arange(y0-miny,y1-maxy+.001,2):
                    for x in np.arange(x0-minx,x1-maxx+.001,2):
                        candidate=translate(hull,xoff=x,yoff=y)
                        if any(candidate.intersects(other) for other in occupied):continue
                        # Studio offsets the imported mesh center, not the physical bed center.
                        obj.update(pos_x=[float(x)],pos_y=[float(y)])
                        objects.append(obj);occupied.append(candidate);placed=True;break
                    if placed:break
                if placed:break
        if not placed:
            # Start at the corner: centering the first item can prevent a second
            # identical part from fitting even when their combined width fits.
            if not separate:
                dx=x0-minx;dy=y0-miny
                obj.update(pos_x=[float(dx)],pos_y=[float(dy)])
                hull=translate(hull,xoff=dx,yoff=dy)
            obj['_exclusive']=separate
            plates.append([obj]);footprints.append([hull])
    for group in plates:
        for obj in group:obj.pop('_exclusive',None)
    return plates
