"""Arrange the generated assembly into six named layers and numbered parts."""
from pathlib import Path
import sys,json,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from trimesh.exchange.threemf import export_3MF
LAYERS=[('A','01-three-slot-plate-layer',0),('B','02-eight-slot-plate-layer',30),('C','03-single-drawer-layer',90),('D','04-double-drawer-layer',150),('E','05-triple-drawer-layer',210),('F','06-device-top',270)]

def label(n):
    if 'layer_lock' in n or n.startswith('top_rear_lock'):return '层间锁片'
    if n.startswith('device_adapter_'):return '顶部左片' if n.endswith('_1') else '顶部右片'
    for key,zh in [('end_left','左端框'),('end_right','右端框'),('side_bin_left','左小抽屉'),('side_bin_right','右小抽屉'),('side_cover_left','左封板'),('side_cover_right','右封板'),('side_left','左侧承架'),('side_right','右侧承架'),('rear_beam','后横梁'),('front_beam','前横梁'),('divider','隔墙')]:
        if key in n:return zh
    if 'cassette_' in n:return {'1':'左侧承架','2':'右侧承架','3':'前横梁','4':'后横梁'}[n.rsplit('_',1)[1]]
    if n.startswith('standard_2_drawer_'):return '抽屉前半' if n.endswith('_1') else '抽屉后半'
    if 'drawer' in n:return '抽屉'+n.rsplit('_',1)[1]
    raise ValueError(n)

def package(source,dest):
    dest.mkdir(parents=True,exist_ok=True);data=json.loads((source/'checks.json').read_text());whole=trimesh.Scene();records=[]
    for group,(prefix,folder,z) in enumerate(LAYERS):
        path=dest/folder;(path/'parts').mkdir(parents=True,exist_ok=True);layer=trimesh.Scene();glb=trimesh.Scene()
        whole.graph.update(frame_to=folder,frame_from=whole.graph.base_frame,matrix=np.eye(4))
        rows=sorted([r for r in data['parts'] if r['layer']==group],key=lambda r:r['name'])
        for i,r in enumerate(rows,1):
            ident=f'{prefix}{i:02d}';name=r['name'];m=trimesh.load_mesh(source/r['file'])
            assert m.is_volume and m.is_watertight and len(m.split())==1,name
            title=label(name);filename=f'{ident}-{name}.stl';m.export(path/'parts'/filename)
            m.visual.vertex_colors=[104,142,148,255] if 'cassette' in name or 'side_' in name else [202,207,209,255]
            if 'drawer' in name and ('_drawer_' in name or 'side_bin' in name):m.visual.vertex_colors=[199,176,141,255]
            if 'layer_lock' in name or 'top_rear_lock' in name:m.visual.vertex_colors=[210,131,67,255]
            layer.add_geometry(m,node_name=ident,geom_name=ident)
            shown=m.copy();shown.unmerge_vertices();shown.vertex_normals=np.repeat(m.face_normals,3,axis=0);shown.apply_scale(.001);shown.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));glb.add_geometry(shown,node_name=ident)
            world=move(m,[0,0,z]);world.unmerge_vertices();world.vertex_normals=np.repeat(m.face_normals,3,axis=0);world.apply_scale(.001);world.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));whole.add_geometry(world,node_name=ident,geom_name=ident,parent_node_name=folder)
            record={**r,'id':ident,'label':title,'packaged_file':str((path/'parts'/filename).relative_to(dest))};records.append(record)
        glb.export(path/'layer-assembly.glb');(path/'layer-assembly-geometry.3mf').write_bytes(export_3MF(layer))
        (path/'README.md').write_text('# '+folder+'\n\n'+ '\n'.join(f'- {r["id"]} {r["label"]}' for r in records if r['layer']==group)+'\n\nSTL单位毫米。3MF为装配几何，不含打印机配置，不是可直接发送的切片文件。零件未摆盘，切片前需调整方向与支撑。\n')
    whole.export(dest/'stacknest-assembly.glb')
    (dest/'parts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    check=trimesh.load(dest/'stacknest-assembly.glb');assert len(check.graph.nodes_geometry)==58
    for prefix,folder,z in LAYERS:
        loaded=trimesh.load(dest/folder/'layer-assembly-geometry.3mf')
        assert len(loaded.graph.nodes_geometry)==sum(r['packaged_file'].startswith(folder+'/') for r in records)
    print('PASS: six layers, 58 numbered STL parts, six geometry-only 3MF assemblies')
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'output/model');p.add_argument('--dest',type=Path,default=ROOT/'models/ams2pro+ht')
    a=p.parse_args();package(a.source,a.dest)
