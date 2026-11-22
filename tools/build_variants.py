"""Build AMS-only layers and shared plain/SKADIS-style ends from analytic source."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *
from base import build_module
from fabrication import segment,orient
from surfaces import top_parts
from layer_locks import layer_lock,check_layer_locks
from multi_drawers import variant
import compact,pegboard
from trimesh.exchange.threemf import export_3MF

OUT=ROOT/'models/no-ht';COMMON=ROOT/'models/common';CHECKS=ROOT/'output/variants'


def scene(parts):
    result=trimesh.Scene()
    for name,mesh in parts.items():
        m=mesh.copy();m.unmerge_vertices();m.vertex_normals=np.repeat(m.face_normals,3,axis=0)
        color=[157,182,184,255]
        if 'end_' in name or 'top_' in name:color=[205,211,215,255]
        if 'drawer_' in name:color=[204,181,145,255]
        if 'lock' in name:color=[213,128,66,255]
        m.visual.vertex_colors=color;m.apply_scale(.001)
        m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]))
        result.add_geometry(m,node_name=name)
    return result


def verify(parts,label):
    for name,m in parts.items():assert m.is_volume and len(m.split())==1,(label,name,'solid')
    pairs=0
    for i,(an,a) in enumerate(parts.items()):
        for bn,b in list(parts.items())[i+1:]:
            v=overlap(a,b);assert v<.03,(label,an,bn,v)
            pairs+=1
    return pairs


def build():
    for d in [OUT,COMMON,CHECKS]:d.mkdir(parents=True,exist_ok=True)
    print('Building common 30 / 60 mm modules',flush=True)
    modules={h:build_module(h,n) for h,n in [(30,3),(60,8)]}
    common={};report={'width_mm':399,'depth_mm':287,'three_drawer_available':False,'layers':[],
        'pegboard':{'slot_mm':[5,15],'panel_mm':5,'repeat_mm':40,'stagger_mm':20,'rear_clearance_mm':20,
                    'cross_layer_accessories':False,'physical_fit':'not_verified'},'parts':[]}
    for H,module in modules.items():
        for style in ['plain','pegboard']:
            for right,side in [(False,'left'),(True,'right')]:
                key=f'end_{side}_{H}_{style}'
                common[key]=module['ends'][right].copy() if style=='plain' else pegboard.end(module,right)
    for side,right in [('left',False),('right',True)]:common['lock_'+side]=mirror_x(layer_lock()) if right else layer_lock()
    common['pegboard_fit_coupon']=pegboard.coupon()
    for name,m in common.items():
        p=COMMON/(name+'.stl');m.export(p)
        report['parts'].append({'name':name,'file':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    scene({n:m for n,m in common.items() if n=='end_left_60_pegboard'}).export(COMMON/'pegboard-end.glb')
    template={'end_left_1':modules[60]['ends'][0],'end_right_1':modules[60]['ends'][1]}
    template.update({f'cassette_drawer_{i}':m for i,m in enumerate(segment('cassette_drawer',modules[60]['parts']['cassette_drawer']),1)})
    layers=[]
    for H,count in [(30,3),(60,8)]:
        layers.append((f'{count}-slot-plate-layer',H,compact.plate_layer(modules[H])))
    for count in [1,2]:
        print('Building compact drawer count',count,flush=True)
        parts,tests=variant(count,template,width=399)
        if count==1:
            drawer=parts.pop('drawer_1')
            for i,m in enumerate(compact.split_drawer(drawer),1):parts[f'drawer_half_{i}']=m
        layers.append((f'{count}-drawer-layer',60,parts))
        report.setdefault('drawer_travel',[]).extend({'count':count,**r} for r in tests)
    tops=compact.top_parts(top_parts())
    layers.append(('device-top',26,{f'top_{i}':m for i,m in enumerate(tops,1)}))
    assembly={};peg_assembly={};z=0
    for slug,H,parts in layers:
        folder=OUT/slug;folder.mkdir(exist_ok=True)
        for side,right in [('left',False),('right',True)]:
            if z>0:parts['lock_'+side]=move(common['lock_'+side],[399-495 if right else 0,0,0])
        records=[];peg_parts={}
        for name,m in parts.items():
            right='right' in name
            if name.startswith('end_'):
                shared=f'end_{"right" if right else "left"}_{H}_plain'
                file=COMMON/(shared+'.stl');peg=common[shared.replace('_plain','_pegboard')]
                peg=move(peg,[-96 if right else 0,0,0])
            elif name.startswith('lock_'):file=COMMON/(name+'.stl');peg=m
            else:
                file=folder/(name+'.stl');m.export(file);peg=m
                report['parts'].append({'name':slug+'/'+name,'file':str(file.relative_to(ROOT)), 'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
            records.append({'name':name,'file':str(file.relative_to(ROOT)),
                            'offset_mm':[-96 if right and (name.startswith('end_') or name.startswith('lock_')) else 0,0,0]})
            assembly[slug+'__'+name]=move(m,[0,0,z]);peg_assembly[slug+'__'+name]=move(peg,[0,0,z]);peg_parts[name]=peg
        pairs=verify(parts,slug);verify(peg_parts,slug+' pegboard')
        scene(parts).export(folder/'layer-assembly.glb')
        raw=trimesh.Scene()
        for name,m in parts.items():raw.add_geometry(m,node_name=name,geom_name=name)
        (folder/'layer-assembly-geometry.3mf').write_bytes(export_3MF(raw))
        (folder/'parts.json').write_text(json.dumps(records,indent=2)+'\n')
        report['layers'].append({'name':slug,'height_mm':H,'z_mm':z,'parts':len(parts),'pairs_checked':pairs})
        z+=H
    report['assembly_pairs_checked']=verify(assembly,'complete compact')
    report['pegboard_assembly_pairs_checked']=verify(peg_assembly,'complete pegboard compact')
    report['bounds_mm']=trimesh.util.concatenate(list(assembly.values())).extents.tolist()
    for lower in modules.values():
        for upper in modules.values():
            for style in ['plain','pegboard']:
                a={**lower,'ends':[common[f'end_{s}_{lower["height"]}_{style}'] for s in ['left','right']]}
                b={**upper,'ends':[common[f'end_{s}_{upper["height"]}_{style}'] for s in ['left','right']]}
                check_layer_locks(a,b)
    scene(assembly).export(OUT/'stacknest-no-ht.glb')
    scene(peg_assembly).export(OUT/'stacknest-no-ht-pegboard.glb')
    for name,m in common.items():
        if name.startswith('end_') and name.endswith('_pegboard'):
            normal=common[name.replace('_pegboard','_plain')]
            assert abs(cut(m,normal).volume)<.01,('pegboard expands envelope',name)
    # Deliberately move a plate into its sidewall: the interference test must fail.
    p=compact.plate_layer(modules[30]);probe=box(61,100,10,3,30,4)
    assert overlap(probe,p['plate_carrier_left'])>100
    report['negative_control']='plate deliberately inside sidewall detected'
    report.update(physical_fit='not_verified',load_rating=None,sliced=False)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS compact and pegboard assemblies',report['bounds_mm'],flush=True)
    return report


if __name__=='__main__':build()
