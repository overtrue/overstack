"""Render current Overstack exports with Engineered Reality device STEP models.

See docs/render-assets.md for sources and conversion commands. Device files stay local.
"""
from pathlib import Path
import sys,math,json
import bpy
from mathutils import Vector, Matrix
from cad.blender import load
ROOT=Path(__file__).resolve().parents[1]
no_ht='--no-ht' in sys.argv
final='--final' in sys.argv;compact='--compact' in sys.argv or no_ht
key='no-ht' if no_ht else 'compact' if compact else 'full';top=.100 if compact else .280
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene

def material(name,color,rough=.4,metal=0,transmission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF']
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 p.inputs['Transmission Weight'].default_value=transmission;p.inputs['IOR'].default_value=1.46
 return m
shell=material('Graphite enclosure',(.035,.043,.047),.28)
glass=material('Smoked polycarbonate',(.66,.72,.73),.1,transmission=1)
white=material('Spool ivory',(.74,.77,.73),.38)
frame=material('Warm gray PETG',(.57,.62,.60),.63)
drawer=material('Muted teal PETG',(.12,.26,.27),.58)
accent=material('Rear keys',(.75,.30,.10),.5)
plate=material('Textured PEI',(.24,.18,.09),.68,.45)
spool_colors=[(.17,.38,.37),(.7,.35,.16),(.77,.7,.48),(.19,.22,.25)]
model=load(ROOT/'output/showcase'/f'{key}.glb')
rows={r['id']:r['name'] for r in json.loads((ROOT/'models/ams2pro+ht/parts.json').read_text())}
if no_ht:
 rows={r['id']:r['name'] for p in (ROOT/'models/ams2pro').glob('*/parts.json') for r in json.loads(p.read_text())}
for obj in scene.objects:
 if obj.type!='MESH':continue
 name=rows.get(obj.name,obj.name)
 mat=plate if obj.name.startswith('plate-') else accent if 'lock' in name else drawer if ('_drawer_' in name or name.startswith('drawer_') or 'side_bin' in name) else frame
 obj.data.materials.clear();obj.data.materials.append(mat)
 for p in obj.data.polygons:p.use_smooth=False

def cube(name,center,size,mat,bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Rounded molding','BEVEL');mod.width=bevel;mod.segments=5
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 o.data.materials.append(mat);return o

def cyl(name,center,radius,depth,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=radius,depth=depth,location=center,rotation=(0,math.pi/2,0))
 o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 mod=o.modifiers.new('Soft rim','BEVEL');mod.width=.001;mod.segments=3
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def device(key,xcenter,z,rotate=False):
 before=set(scene.objects)
 load(ROOT/'output/device-reference'/f'{key}.glb')
 bpy.context.view_layer.update()
 objects=[o for o in scene.objects if o not in before and o.type=='MESH']
 rotation=Matrix.Rotation(math.pi if rotate else 0,4,'Z')
 matrices={o:rotation@o.matrix_world.copy() for o in objects}
 points=[matrices[o]@Vector(v) for o in objects for v in o.bound_box]
 lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
 hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
 shift=Matrix.Translation(Vector((xcenter,.1435,z))-Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z)))
 for o in objects:
  o.parent=None;o.matrix_world=shift@matrices[o]
  o.data.materials.clear();o.data.materials.append(glass if 'Lid' in o.name else shell)
  # STEP tessellation already carries split normals; preserve its sharp edges.
 print(key,'unscaled dimensions (mm)',tuple(round((hi[i]-lo[i])*1000,2) for i in range(3)))
 positions=[xcenter] if key=='ams-ht' else [xcenter-.1305+i*.087 for i in range(4)]
 for i,cx in enumerate(positions):
  fil=material(key+f' filament {i}',spool_colors[i if key!='ams-ht' else 3],.63)
  cyl(key+f' filament {i}',(cx,.149,z+.119),.093,.059,fil)
  for side in [-1,1]:
   cyl(key+f' spool flange {i} {side}',(cx+side*.032,.149,z+.119),.099,.0035,white)
   cyl(key+f' spool hub {i} {side}',(cx+side*.034,.149,z+.119),.026,.004,shell)
# Keep original model scale. Rotate the HT to face the same way as the AMS 2 Pro.
device('ams-2-pro',.1995 if no_ht else .1875,top+.016)
if not no_ht:device('ams-ht',.4308,top+.0105,rotate=True)
floor=material('Studio background',(.78,.79,.75),.85)
cube('Studio floor',(.25,.1,-.008),(200,200,.01),floor,0)
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
center=Vector((.1995 if no_ht else .2475,.139,(top+.255)/2))
cam.location=center+Vector((.88,-1.60,.89));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=.70 if no_ht else .89 if not compact else .80
for name,position,power,size in [('Key',(-.5,-.5,1.4),95,1.0),('Fill',(.95,-.2,.9),45,.8),('Rim',(.3,.9,1.3),110,.65)]:
 l=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(l);l.location=position;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.22
scene.render.engine='CYCLES';scene.cycles.samples=160 if final else 24;scene.cycles.use_denoising=True
scene.cycles.transmission_bounces=12;scene.cycles.max_bounces=16
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
except (TypeError,RuntimeError):pass
scene.view_settings.view_transform='AgX'
scene.render.resolution_x=2000 if final else 1000;scene.render.resolution_y=1600 if final else 800;scene.render.resolution_percentage=100
out=ROOT/'docs/images'/f'showcase-{key}.png' if final else ROOT/'output/showcase'/f'{key}-draft.png'
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out)
bpy.ops.render.render(write_still=True)
print(out)
