"""Blender render with flat face normals and large softboxes; geometry unchanged."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
jobs=json.loads((ROOT/'output/illustrations/jobs.json').read_text())
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
selected=[j for j in jobs if not args or j['key'] in args]
for j in selected:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene
 bpy.ops.import_scene.gltf(filepath=j['scene'])
 for obj in scene.objects:
  if obj.type=='MESH':
   # Imported averaged vertex normals caused triangular shading across flat walls.
   for face in obj.data.polygons:face.use_smooth=False
   obj.data.update()
   mat=bpy.data.materials.new(obj.name+'-matte');mat.diffuse_color=(.22,.36,.39,1);mat.use_nodes=True
   p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.22,.36,.39,1);p.inputs['Roughness'].default_value=.76
   obj.data.materials.clear();obj.data.materials.append(mat)
 camera=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camera);scene.collection.objects.link(cam);scene.camera=cam
 c=j['camera'];cam.location=Vector(c['position'])*.001;target=Vector(c['target'])*.001;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 camera.type='ORTHO';camera.ortho_scale=2*c['orthographicHalfHeight']*.001*max(1,j['width']/j['height'])
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
