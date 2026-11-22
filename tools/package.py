"""Arrange the generated assembly into six named layers and numbered parts."""
from pathlib import Path
import sys,json,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from trimesh.exchange.threemf import export_3MF
LAYERS=[('A','01-five-slot-plate-layer',0),('B','02-eight-slot-plate-layer',40),('C','03-single-drawer-layer',100),('D','04-double-drawer-layer',160),('E','05-triple-drawer-layer',220),('F','06-device-top',280)]

def label(n):
    if 'layer_lock' in n or n.startswith('top_rear_lock'):return '层间锁片'
    if n.startswith('device_adapter_'):return '顶部左片' if n.endswith('_1') else '顶部右片'
    for key,zh in [('end_left','左端框'),('end_right','右端框'),('side_bin_left','左小抽屉'),('side_bin_right','右小抽屉'),('side_cover_left','左封板'),('side_cover_right','右封板'),('side_left','左侧承架'),('side_right','右侧承架'),('rear_beam','后横梁'),('front_beam','前横梁'),('divider','隔墙')]:
        if key in n:return zh
    if 'cassette_' in n:return {'1':'左侧承架','2':'右侧承架','3':'前横梁','4':'后横梁'}[n.rsplit('_',1)[1]]
    if n.startswith('standard_2_drawer_'):return '抽屉左半' if n.endswith('_1') else '抽屉右半'
    if 'drawer' in n:return '抽屉'+n.rsplit('_',1)[1]
    raise ValueError(n)

def write_layer_readme(path,records):
    slug=path.name
    image=f'../../../docs/images/{slug}-assembly-zh.png'
    text=f'# {slug}\n\n![装配预览 / Assembly preview](preview.png)\n\n'
    if slug in ('01-five-slot-plate-layer','02-eight-slot-plate-layer'):
        text+='**打印板适配：当前所有五槽／八槽板架仅针对 256 × 256 mm 打印面积规格的拓竹板设计，适用机型为 A1、P1P、P1S、P2S、X1、X1 Carbon（X1C）、X1E 和 X2D。** 不支持 A1 mini 或 H 系列板。256 × 256 mm 是打印面积，不是钢板完整外形；第三方板需另核外形与厚度，当前模型尚未实物试装。\n\n**Build plate compatibility: all current five- and eight-slot racks are designed only for Bambu plates in the 256 × 256 mm printable-area class: A1, P1P, P1S, P2S, X1, X1 Carbon (X1C), X1E and X2D.** A1 mini and H-series plates are not supported. 256 × 256 mm describes the printable area, not the full steel-sheet outline. Check third-party plate outlines and thickness separately; physical fit has not been tested.\n\n'
    if slug=='03-single-drawer-layer':
        text+='新版为左右两半，左半从后方向前滑合；旧前后两半需成对替换，不能混用。接缝加强筋在内侧凸起0.8 mm。 / The new left/right halves slide together from the rear. Replace both old front/rear halves; do not mix revisions. The seam has a local 0.8 mm interior ridge. [修复与验证 / Repair checks](../../../docs/drawer-repair.md).\n\n'
    if slug=='06-device-top':
        text+='两端挡边的四个外露上角已做 R3 mm 圆角，承托面和连接接口不变；打印后仍需检查毛刺。 / The four exposed upper lip ends have R3 mm rounds; bearing faces and joints are unchanged. Check printed parts for burrs.\n\n![R3 挡边端头 / Rounded lip tip](../../../docs/images/lip-r3-detail.png)\n\n'
    if slug=='01-five-slot-plate-layer':
        text+='40 mm 层高，5 个板位，槽距 6 mm；按板厚最大 1.5 mm 预留，顶槽上方净空 7 mm。 / 40 mm layer, 5 plate slots at 6 mm pitch, allowing up to 1.5 mm plate thickness with 7 mm top clearance.\n\n'
    text+='## 零件编号 / Part IDs\n\n编号对应下方爆炸图和 STL 文件名；点击编号下载对应零件。左右以面对抽屉／打印板入口为准。\n\n'
    text+='Match the IDs in the exploded view to the STL filenames. Click an ID to download that part. Left and right are viewed from the front opening.\n\n'
    text+=f'![带零件编号的爆炸图 / Numbered exploded view]({image})\n\n'
    text+='| 编号 / ID | 零件 |\n| --- | --- |\n'
    for r in records:text+=f'| [{r["id"]}](parts/{Path(r["packaged_file"]).name}) | {r["label"]} |\n'
    text+=f'\n[中文组装教程](../../../docs/pdf/{slug}-assembly-zh.pdf) · [English assembly guide](../../../docs/pdf/{slug}-assembly-en.pdf)\n\n'
    text+='STL单位毫米。3MF为装配几何，不含打印机配置，不是可直接发送的切片文件。零件未摆盘，切片前需调整方向与支撑。\n'
    (path/'README.md').write_text(text)


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
        write_layer_readme(path,[r for r in records if r['layer']==group])
    whole.export(dest/'stacknest-assembly.glb')
    (dest/'parts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    check=trimesh.load(dest/'stacknest-assembly.glb');assert len(check.graph.nodes_geometry)==58
    for prefix,folder,z in LAYERS:
        loaded=trimesh.load(dest/folder/'layer-assembly-geometry.3mf')
        assert len(loaded.graph.nodes_geometry)==sum(r['packaged_file'].startswith(folder+'/') for r in records)
    printing=json.loads((ROOT/'output/printing/checks.json').read_text())
    source_hashes={r['name']:r['sha256'] for r in data['parts']}
    assert {r['source_sha256'] for r in printing['unique_parts']}==set(source_hashes.values()),'incomplete manufacturing checks'
    for row in printing['unique_parts']:
        assert source_hashes[row['name']]==row['source_sha256'],('stale manufacturing check',row['name'])
    failures=[{'part':r['name'],'status':r['status'],'errors':r['errors']}
              for r in printing['unique_parts'] if r['status']!='ok']
    summary={'parts':len(records),'assembly_pairs':data['assembly_pairs_checked'],
             'distinct_geometries':len(printing['unique_parts']),
             'printing_statuses':sorted({r['status'] for r in printing['unique_parts']}),
             'warnings':sorted({w for r in printing['unique_parts'] for w in r['warnings']}),
             'printing_passed':sum(r['status']=='ok' for r in printing['unique_parts']),
             'printing_failures':failures,'physical_fit':'not_verified','load_rating':None,'sliced':False}
    (dest/'validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    repair=json.loads((source/'drawer-repair-checks.json').read_text())
    for name,pose in repair['poses'].items():
        assert pose['source_sha256']==source_hashes[name],('stale drawer check',name)
    (dest/'drawer-repair-checks.json').write_text(json.dumps(repair,indent=2)+'\n')
    print('PASS: six layers, 58 numbered STL parts, six geometry-only 3MF assemblies')
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'output/model');p.add_argument('--dest',type=Path,default=ROOT/'models/ams2pro+ht')
    a=p.parse_args();package(a.source,a.dest)
