"""Support-first orientation and brim-aware footprint packing for print profiles."""
from geometry import np,trimesh
from shapely.geometry import MultiPoint
from shapely.affinity import translate


def orient_for_area(mesh,area,height):
    x0,y0,x1,y1=area;limit=np.array([x1-x0-6,y1-y0-6,height])
    candidates=[]
    for axis,angle in [([1,0,0],0),([1,0,0],180),([1,0,0],90),
                       ([1,0,0],-90),([0,1,0],90),([0,1,0],-90)]:
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
            # Bed contact cannot compensate for a larger unsupported ceiling.
            score=(round(overhang,1),-round(bed,1),round(float(np.prod(m.extents[:2])),1),yaw)
            candidates.append((score,m,t,overhang,bed))
    assert candidates,('no fitting planar orientation',mesh.extents.tolist())
    # Thin plates/straps should rest on a broad face. A small ledge's support
    # saving does not justify standing the whole plate on its narrow edge.
    dimensions=sorted(mesh.extents)
    if dimensions[0]*4<=dimensions[1]+1e-6:
        flat=[c for c in candidates if c[1].extents[2]<=dimensions[0]+1e-6
              and c[4]>=MultiPoint(c[1].vertices[:,:2]).convex_hull.area*.5]
        if flat:candidates=flat
    _,m,t,overhang,bed=min(candidates,key=lambda c:c[0])
    return m,{'assembly_to_print':t.tolist(),'bounds_mm':m.extents.tolist(),
              'downward_area_mm2':overhang,'bed_contact_area_mm2':bed,
              'supports_required':overhang>1,'brim_mm':3,
              'required_extruder_area_mm':[x1-x0,y1-y0]}


def pack(inputs,parts,target):
    """First-fit convex footprints, expanded by the brim; keep tree-support parts separate."""
    x0,y0,x1,y1=target['area']
    plates=[];footprints=[]
    for path,part in zip(inputs,parts):
        mesh=trimesh.load_mesh(path)
        hull=MultiPoint(mesh.vertices[:,:2]).convex_hull.buffer(part['brim_mm']+.5)
        # A supported tall part's branches can extend beyond its projected mesh.
        separate=part['downward_area_mm2']>100 and part['bounds_mm'][2]>10
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
                        center=mesh.bounds.mean(axis=0)
                        obj.update(pos_x=[float(center[0]+x-target['bed'][0]/2)],
                                   pos_y=[float(center[1]+y-target['bed'][1]/2)])
                        objects.append(obj);occupied.append(candidate);placed=True;break
                    if placed:break
                if placed:break
        if not placed:
            # The source mesh is already centered in the permitted nozzle area.
            obj['_exclusive']=separate
            plates.append([obj]);footprints.append([hull])
    for group in plates:
        for obj in group:obj.pop('_exclusive',None)
    return plates
