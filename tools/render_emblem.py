import bpy, math, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'render').mkdir(exist_ok=True)
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene
s.render.engine='CYCLES'; s.cycles.samples=48; s.cycles.use_denoising=False
s.render.resolution_x=480; s.render.resolution_y=480; s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.render.film_transparent=True
s.world.color=(.3,.35,.45)
s.view_settings.view_transform='AgX'
def mat(n,c,metal=0,emission=0):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=.25
 p.inputs['Emission Color'].default_value=(*c,1); p.inputs['Emission Strength'].default_value=emission
 return m
metal=mat('Obsidian titanium',(.023,.041,.085),.88)
teal=mat('Brand cyan orbit',(0,.32,.62),.5,.08)
purple=mat('Royal blue orbit',(.018,.065,.48),.55,.08)
# Extrude the official SVG paths exactly, preserving both brand colors.
import xml.etree.ElementTree as ET, re
shield=bpy.data.objects.new('Official MalGuard logo',None); bpy.context.collection.objects.link(shield)
blue=mat('Official royal blue',(.029,.147,1),.62,.24)
cyan=mat('Official cyan',(0,.51,.91),.55,.35)
root=ET.parse(str(ROOT/'assets/official-logo.svg')).getroot()
for j,path in enumerate(root):
 if not path.tag.endswith('path'): continue
 c=bpy.data.curves.new('Original SVG path '+str(j),'CURVE'); c.dimensions='2D'; c.fill_mode='BOTH'; c.extrude=.075; c.bevel_depth=.004; c.bevel_resolution=3; c.resolution_u=1
 for sub in path.attrib['d'].split('Z'):
  numbers=[float(v) for v in re.findall(r'-?\d+(?:\.\d+)?',sub)]
  if not numbers: continue
  pts=list(zip(numbers[0::2],numbers[1::2])); sp=c.splines.new('POLY'); sp.points.add(len(pts)-1)
  for p,(x,y) in zip(sp.points,pts): p.co=((x-180)/130,(180-y)/130,0,1)
  sp.use_cyclic_u=True
 o=bpy.data.objects.new('Official logo layer '+str(j),c); bpy.context.collection.objects.link(o); o.rotation_euler[0]=math.pi/2; o.data.materials.append(blue if j==0 else cyan); o.parent=shield
rings=[]
for i,(rad,rot,material) in enumerate([(1.56,(1.05,.36,.25),teal),(1.83,(.55,-.65,-.35),purple)]):
 bpy.ops.mesh.primitive_torus_add(major_radius=rad,minor_radius=.018,major_segments=128,minor_segments=8)
 o=bpy.context.object; o.name='Orbital ring '+str(i); o.rotation_euler=rot; o.data.materials.append(material); rings.append((o,rot))
 for poly in o.data.polygons: poly.use_smooth=True
# Elegant satellite accents.
sats=[]
for i in range(5):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.044 if i else .075)
 o=bpy.context.object; o.data.materials.append(teal if i%2==0 else purple); sats.append(o)
for pos,col,power,size in [((-3,-4,5),(.2,.75,1),850,5),((4,-1,2),(.6,.15,1),1000,4),((0,3,3),(.1,1,.7),1200,3)]:
 bpy.ops.object.light_add(type='AREA',location=pos); l=bpy.context.object; l.data.energy=power; l.data.color=col; l.data.shape='DISK'; l.data.size=size; l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.3,-8.5,3.15)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,.12))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=4.55; s.camera=cam
s.use_nodes=True; nodes=s.node_tree.nodes; nodes.clear(); rl=nodes.new('CompositorNodeRLayers'); gl=nodes.new('CompositorNodeGlare'); gl.glare_type='FOG_GLOW'; gl.quality='HIGH'; gl.threshold=3; gl.size=7; co=nodes.new('CompositorNodeComposite'); s.node_tree.links.new(rl.outputs['Image'],gl.inputs['Image']); s.node_tree.links.new(gl.outputs['Image'],co.inputs['Image'])
count=int(os.environ.get('FRAME_COUNT','90'))
for k in range(count):
 t=2*math.pi*k/90
 shield.rotation_euler[2]=.16*math.sin(t); shield.rotation_euler[0]=.06*math.cos(t); shield.location.z=.075*math.sin(t)
 for i,(o,rot) in enumerate(rings):
  o.rotation_euler=(rot[0]+.22*math.sin(t+i),rot[1]+.3*math.cos(t+i),rot[2]+t*(1 if i==0 else -1))
 for i,o in enumerate(sats):
  a=t+i*2*math.pi/5; o.location=(1.66*math.cos(a),.8*math.sin(a),1.15*math.sin(a+.6))
 s.render.filepath=str(ROOT/f'render/emblem-light-{k:03d}.png'); bpy.ops.render.render(write_still=True)
