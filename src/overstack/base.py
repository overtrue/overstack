"""Parametric modules. Dimensions in mm; H is body height, excluding 3 mm locating pins.
Fixed interface: XY axes, round corner pins/sockets, vertical dovetail cross-sections.
Plate slots use6mm pitch. Require7mm overhead. Physical fit/load unverified.
"""

def build_module(H, N, fit=.35):
 import trimesh,numpy as np
 from shapely.geometry import Polygon, LineString, box as rectangle
 from shapely.affinity import translate
 from geometry import lead_in, mirror_x, overlap
 from layer_locks import lock_pockets
 from corner_pins import circle,clearance,fixed_pin,receiver
 from storage import side_bays
 from structure import install_structure,BAR_DEPTH
 outline=rectangle(15,15,480,272).buffer(15,quad_segs=32)
 if not isinstance(N,int) or isinstance(N,bool) or N<1:raise ValueError('Plate count must be positive')
 pitch=6
 if not 40<=H<=60:raise ValueError('Supported module height is 40 to 60 mm')
 if not .25<=fit<=.5:raise ValueError('Fit must be 0.25 to 0.5 mm')
 if H<7.5+(N-1)*pitch+1.5+7:raise ValueError('Insufficient plate clearance')
 prism=trimesh.creation.extrude_polygon(outline,H,engine='earcut')
 def box(x,y,z,w,d,h):
  m=trimesh.creation.box([w,d,h]);m.apply_translation([x+w/2,y+d/2,z+h/2]);return m
 def U(ms):return trimesh.boolean.union(ms,engine='manifold')
 def cut(a,b):return trimesh.boolean.difference([a,b],engine='manifold')
 def inter(a,b):return trimesh.boolean.intersection([a,b],engine='manifold')
 def move(m,t):m=m.copy();m.apply_translation(t);return m
 def cyl(x,y,z,r,h):
  m=trimesh.creation.cylinder(radius=r,height=h,sections=96);m.apply_translation([x,y,z+h/2]);return m
 def rail(poly,y0,length):
  m=trimesh.creation.extrude_polygon(Polygon(poly),height=length,engine='earcut')
  m.apply_transform(np.array([[1,0,0,0],[0,0,1,y0],[0,1,0,0],[0,0,0,1]],float));return m
 def center_rail(left,offset=0,female=False):
  # Two short vertical dovetails per side; open above, stopped at Z4 below.
  y=40 if offset==0 else 247
  male=Polygon([(54.3,y-6),(60.5,y-3),(60.5,y+3),(54.3,y+6)])
  profile=male.buffer(fit,join_style=2) if female else male
  if not left:
   profile=Polygon([(495-x,yy) for x,yy in profile.exterior.coords])
  m=trimesh.creation.extrude_polygon(profile,height=H-3 if female else H-4,engine='earcut')
  m.apply_translation([0,0,4])
  if female:m=U([m,lead_in(profile,H-.8,.9,.5)])
  return m
 corners=[(right,back) for right in (False,True) for back in (False,True)]
 def boss_profile(right,back):
  return circle(right,back,3+clearance(right,back)+.4+3)
 def extrude_at(profile,z,height):
  return move(trimesh.creation.extrude_polygon(profile,height,engine='earcut'),[0,0,z])
 ends=[]
 for side in ['left','right']:
  x=0 if side=='left' else 435
  m=inter(box(x,0,0,60,287,H),prism)
  # Side ends use R3 inner corners; retain that rounded construction.
  cavity=rectangle(15,21,45,266).buffer(3,quad_segs=12)
  opening=rectangle(15,68,80,219).buffer(3,quad_segs=12)
  if side=='right':
   cavity=Polygon([(495-xx,yy) for xx,yy in cavity.exterior.coords])
   opening=Polygon([(495-xx,yy) for xx,yy in opening.exterior.coords])
  m=cut(m,extrude_at(cavity,4,H-3))
  m=cut(m,extrude_at(opening,-.1,H+.2))
  for right,back in corners:
   if right==(side=='right'):
    boss=boss_profile(right,back)
    assert outline.covers(boss),'corner socket extends outside the frame'
    m=U([m,extrude_at(boss,0,H)])
  # Wider dovetails get solid backing into the hollow, approximately6mm behind slot head and at both flanks.
  for yy in [40,247]:
   m=U([m,box(48 if side=='left' else 435,yy-12.35,0,12,24.7,H)])
  # Vertical insertion channels open only above; front and rear stay closed.
  for z in [0,22]:m=cut(m,center_rail(side=='left',z,True))
  for right,back in corners:
   if right==(side=='right'):
    m=cut(U([m,fixed_pin(right,back)]),receiver(right,back,H))
  m=lock_pockets(m,H,side=='right')
  ends.append(m)
 car=U([box(60.5,0,0,56,287,3),box(378.5,0,0,56,287,3),box(116.5,283,0,262,4,3),box(60.5,0,3,4,287,H-3),box(430.5,0,3,4,287,H-3),box(60.5,283,3,374,4,H-3)])
 tongues=[center_rail(left,z) for left in [True,False] for z in [0,22]]
 car=U([car,box(60.5,0,0,374,8,3),box(60.5,277,0,374,10,3)]+tongues)
 car=install_structure(car,H)
 drawer_car=U([car,box(89.5,0,3,3,279,H-3),box(402.5,0,3,3,279,H-3),box(60.5,0,3,31,4,H-3),box(403.5,0,3,31,4,H-3),box(92.5,8,3,5,263,5.5),box(397.5,8,3,5,263,5.5)])
 plate_parts=[car,box(109.5,0,3,8,280,H-3),box(377.5,0,3,8,280,H-3)]
 for i in range(N):
  for x in [117.5,369.5]:
   # Front160mm shelves:7mm nominal bearing,6mm at maximum1mm sideways offset.
   shelf=rectangle(x+1,1,x+7,159).buffer(1,quad_segs=6)
   plate_parts.append(extrude_at(shelf,6+i*pitch,1.5))
   #0.6mm front retention ramp; lift the plate1mm before pulling out.
   ramp=trimesh.convex.convex_hull(np.array([[x,0,7.5+i*pitch],[x+8,0,7.5+i*pitch],[x,3,7.5+i*pitch],[x+8,3,7.5+i*pitch],[x,1.5,8.1+i*pitch],[x+8,1.5,8.1+i*pitch]]))
   plate_parts.append(ramp)
 plate_car=U(plate_parts)
 plate_car,side_parts=side_bays(plate_car,H)
 top=[]
 # Preserve the carrier used as the dovetail template for both drawer widths.
 stop=U([box(83.5,14,3,9,16,H-3),box(91.5,20,10.35,2.65,4,4.3)])
 drawer_car=U([drawer_car,stop,mirror_x(stop)])
 drawer_car=U([drawer_car,box(92.5,0,2.9,17,2,3.1),box(385.5,0,2.9,17,2,3.1)])
 parts={'end_left':ends[0],'end_right':ends[1],'cassette_drawer':drawer_car,'cassette_plates':plate_car}
 parts.update({'device_top_'+n:k for n,k in top})
 parts.update(side_parts)
 checks=[]
 for name,cartridge in [('drawer',drawer_car),('plates',plate_car)]:
  for travel in [0,H/3,2*H/3,H]:
   m=move(cartridge,[0,0,travel])
   for side,e in zip(['left','right'],ends):
    v=abs(inter(m,e).volume);assert v<.01,(name,travel,side,v)
    checks.append({'insert':name,'travel':travel,'side':side,'overlap_mm3':float(v)})
 for e in ends:
  v=abs(inter(e,move(e,[0,0,H])).volume);assert v<.01,('stack',v)
 finish_checks=[]
 for finishname,ms in [('device',[m for _,m in top])]:
  for travel in [0,H/3,2*H/3,H]:
   for side,e in zip(['left','right'],ends):
    overlap=sum(abs(inter(move(m,[0,0,travel]),e).volume) for m in ms)
    assert overlap<.01,(finishname,travel,side,overlap)
    finish_checks.append({'finish':finishname,'travel':travel,'side':side,'overlap_mm3':float(overlap)})
 for i in range(N):
  for dx in [-1,0,1]:
   v=abs(inter(box(118.5+dx,4,7.5+pitch*i,258,276,1.5),plate_car).volume);assert v<.01,('plate',i,dx,v)
  for travel in [0,5,30,120,240]:
   v=abs(inter(box(118.5,4-travel,8.5+pitch*i,258,276,1.5),plate_car).volume);assert v<.01,('lifted plate travel',i,travel,v)
 for m in [drawer_car,plate_car]:
  assert np.allclose(m.bounds[:,2],[0,H])
  for e in ends:
   assert abs(inter(m,move(e,[0,0,H])).volume)<.01
   assert abs(inter(move(m,[0,0,H]),e).volume)<.01
  for _,adapter in top:
   assert abs(inter(m,adapter).volume)<.01
 for lower,upper in [(drawer_car,plate_car),(plate_car,drawer_car)]:
  assert abs(inter(lower,move(upper,[0,0,H])).volume)<.01
 for left,e in zip([True,False],ends):
  x=56 if left else 438
  for y in [0,280]:
   wall=box(x,y,7.75,1,7,.5)
   assert abs(inter(e,wall).volume-wall.volume)<.01,('end wall open',left,y)
  for y in [40,247]:
   mouth=box(x,y-.25,H-.5,1,.5,.5)
   stop=box(x,y-.25,3.5,1,.5,.5)
   assert abs(inter(e,mouth).volume)<.01,('top blocked',left,y)
   assert abs(inter(e,stop).volume-stop.volume)<.01,('bottom stop missing',left,y)
 for name,m in [('drawer',drawer_car),('plates',plate_car)]:
  assert abs(inter(m,box(125.5,BAR_DEPTH,0,244,287-2*BAR_DEPTH,3)).volume)<.01,('shelf remains',name)
  assert len(m.split())==1,('disconnected cassette',name)
 assert 'stacking_finish_frame' not in parts
 for e in ends:
  assert np.allclose(e.bounds[:,2],[-3,H])
  assert len(e.split())==1, [(q.volume,q.bounds.tolist()) for q in e.split()]
 for right,e in zip([False,True],ends):
  for r,back in corners:
   if r==right:
    wall=extrude_at(boss_profile(r,back).difference(circle(r,back,3+clearance(r,back)+.4)),H-3.5,3.5)
    assert abs(cut(wall,e).volume)<.01,('corner socket wall incomplete',right)
    assert abs(inter(receiver(r,back,H),e).volume)<.01
 for left,e in zip([True,False],ends):
  for yy in [40,247]:
   backing=box(48 if left else 441.5,yy-6,4,5.5,12,H-5)
   assert abs(cut(backing,e).volume)<.01,('slot backing missing',left,yy)
 for left,e in zip([True,False],ends):
  former_entry=inter(box(1 if left else 488,30,H-3,6,10,3),prism)
  assert former_entry.volume>0
  assert abs(cut(former_entry,e).volume)<.01,('legacy front slot remains',left)
 return {'height':H,'plate_count':N,'plate_pitch_mm':pitch,'parts':parts,'ends':ends,'top':top,'insert_checks':checks,'finish_checks':finish_checks,'fit':fit,'side_parts':side_parts}
