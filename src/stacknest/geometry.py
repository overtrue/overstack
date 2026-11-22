"""Shared millimetre geometry for model, assembly tests and fit coupons."""
import trimesh
import numpy as np
from shapely.geometry import Polygon, box as rectangle


def box(x,y,z,w,d,h):
    m=trimesh.creation.box([w,d,h]);m.apply_translation([x+w/2,y+d/2,z+h/2]);return m


def move(m,t):
    m=m.copy();m.apply_translation(t);return m


def union(ms):
    return trimesh.boolean.union(ms,engine='manifold')


def cut(a,b):
    return trimesh.boolean.difference([a,b],engine='manifold')


def intersection(a,b):
    return trimesh.boolean.intersection([a,b],engine='manifold')


def overlap(a,b):
    if np.any(a.bounds[1] <= b.bounds[0]) or np.any(b.bounds[1] <= a.bounds[0]):return 0.
    return abs(intersection(a,b).volume)


def extrude(profile,z,h):
    return move(trimesh.creation.extrude_polygon(profile,h,engine='earcut'),[0,0,z])


def xz_extrude(profile,y,length):
    m=trimesh.creation.extrude_polygon(profile,length,engine='earcut')
    m.apply_transform(np.array([[1,0,0,0],[0,0,1,y],[0,1,0,0],[0,0,0,1]],float));return m


def mirror_x(m):
    m=m.copy();m.apply_transform(np.array([[-1,0,0,495],[0,1,0,0],[0,0,1,0],[0,0,0,1]],float));return m


def cylinder_y(x,y,z,r,length,sections=48):
    m=trimesh.creation.cylinder(radius=r,height=length,sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
    m.apply_translation([x,y+length/2,z]);return m


def rounded_xz(x,z,w,h,r,y,depth):
    profile=rectangle(x+r,z+r,x+w-r,z+h-r).buffer(r,quad_segs=8)
    return xz_extrude(profile,y,depth)


def lead_in(profile,z,height=.8,offset=.5):
    # Both profiles are convex, so their hull is an exact ruled entry taper.
    lower=np.c_[np.asarray(profile.exterior.coords)[:-1],np.full(len(profile.exterior.coords)-1,z)]
    expanded=profile.buffer(offset,join_style=2)
    upper=np.c_[np.asarray(expanded.exterior.coords)[:-1],np.full(len(expanded.exterior.coords)-1,z+height)]
    return trimesh.convex.convex_hull(np.vstack([lower,upper]))


def rear_label(text,x,z):
    segments={'a':[(0,5),(3,5)],'b':[(3,5),(3,2.5)],'c':[(3,2.5),(3,0)],
              'd':[(0,0),(3,0)],'e':[(0,0),(0,2.5)],'f':[(0,2.5),(0,5)],'g':[(0,2.5),(3,2.5)]}
    glyph={'0':'abcdef','1':'bc','2':'abged','3':'abgcd','4':'fgbc','5':'afgcd',
           '6':'afgecd','7':'abc','8':'abcdefg','9':'abfgcd','L':'fed','R':'abfge'}
    from shapely.geometry import LineString
    solids=[]
    for i,c in enumerate(text):
        for seg in glyph[c]:
            points=[(x+i*4.5+xx,z+zz) for xx,zz in segments[seg]]
            solids.append(xz_extrude(LineString(points).buffer(.25,cap_style=2),286.5,.6))
    return union(solids)
