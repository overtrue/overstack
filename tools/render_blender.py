"""Blender render with flat face normals and large softboxes; geometry unchanged."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from cad.blender import load
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
jobfile=ROOT/'output/illustrations/jobs.json'
if '--jobs' in args:
 i=args.index('--jobs');jobfile=Path(args[i+1]);del args[i:i+2]
jobs=json.loads(jobfile.read_text())
selected=[j for j in jobs if not args or j['key'] in args]
for j in selected:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene
 load(j['scene'])
 for obj in scene.objects:
  if obj.type=='MESH':
   # Imported averaged vertex normals caused triangular shading across flat walls.
   for face in obj.data.polygons:face.use_smooth=False
   obj.data.update()
   mat=bpy.data.materials.new(obj.name+'-matte');mat.diffuse_color=(.22,.36,.39,1);mat.use_nodes=True
   color=(.22,.36,.39,1)
   if j.get('component_colors'):
    if 'end_' in obj.name or 'top_' in obj.name or 'device_adapter' in obj.name:color=(.65,.71,.72,1)
    if ('drawer_' in obj.name and 'cassette' not in obj.name) or 'side_bin' in obj.name:color=(.60,.44,.26,1)
    if 'lock' in obj.name or 'ht_foot_' in obj.name:color=(.65,.24,.08,1)
   if j.get('split_colors'):
    if '__front' in obj.name:color=(.19,.42,.42,1)
    elif '__rear' in obj.name:color=(.64,.71,.70,1)
    elif '__pin' in obj.name:color=(.73,.32,.10,1)
    else:color=(.40,.46,.46,1)
   p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.76
   obj.data.materials.clear();obj.data.materials.append(mat)
 camera=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camera);scene.collection.objects.link(cam);scene.camera=cam
 c=j['camera'];cam.location=Vector(c['position'])*.001;target=Vector(c['target'])*.001;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 camera.type='ORTHO';camera.ortho_scale=2*c['orthographicHalfHeight']*.001*max(1,j['width']/j['height'])
 if j.get('labels'):
  rotation=cam.rotation_euler.to_quaternion();right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0));normal=rotation@Vector((0,0,1))
  plane=target+normal*.7
  def ink(name,color):
   mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear()
   emission=nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=color
   out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(emission.outputs[0],out.inputs[0]);return mat
  teal=ink('ID teal',(.025,.20,.21,1));white=ink('ID white',(1,1,1,1))
  for item in j['labels']:
   xy=item['position_mm'];point=plane+right*(xy[0]*.001)+up*(xy[1]*.001)
   anchor=Vector(item['anchor_mm'])*.001-target
   end=plane+right*anchor.dot(right)+up*anchor.dot(up)
   curve=bpy.data.curves.new(item['id']+' leader','CURVE');curve.dimensions='3D';curve.bevel_depth=.00055;curve.bevel_resolution=2
   spline=curve.splines.new('POLY');spline.points.add(1)
   for p,v in zip(spline.points,[end,point]):p.co=(*v,1)
   obj=bpy.data.objects.new(curve.name,curve);scene.collection.objects.link(obj);curve.materials.append(teal);obj.visible_shadow=False
   bpy.ops.mesh.primitive_plane_add(size=1,location=point,rotation=cam.rotation_euler)
   card=bpy.context.object;card.name=item['id']+' card';card.scale=(.052,.022,1);card.data.materials.append(teal);card.visible_shadow=False
   font=bpy.data.curves.new(item['id'],'FONT');font.body=item['id'];font.align_x='CENTER';font.align_y='CENTER';font.size=.014
   obj=bpy.data.objects.new(item['id'],font);scene.collection.objects.link(obj);obj.location=point+normal*.0002;obj.rotation_euler=cam.rotation_euler;obj.visible_shadow=False;font.materials.append(white)
 def area(name,offset,power,size):
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=target+Vector(offset);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 area('Key',(-.6,-.7,1.1),45,1.0);area('Fill',(.7,-.2,.5),15,1.1);area('Rim',(0,.8,.8),30,.9)
 world=bpy.data.worlds.new('Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1);world.node_tree.nodes['Background'].inputs[1].default_value=.25;scene.world=world
 scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
 scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
 scene.render.resolution_x=j['width'];scene.render.resolution_y=j['height'];scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX'
 scene.render.filepath=j['image'];bpy.ops.render.render(write_still=True)
 print('DONE',j['key'],flush=True)
