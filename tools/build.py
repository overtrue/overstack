"""Build every part from analytic geometry, with no mesh inputs."""
from pathlib import Path
import sys,json,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import *
from base import build_module
from fabrication import segment
from structure import crossbar_profile
from layer_locks import layer_lock,check_layer_locks
from multi_drawers import variant
from surfaces import top_parts,illustrative_plate
from shapely.affinity import translate


def extend_plate_sides(parts,H,N,pitch):
    stop=extrude(rectangle(112,274,132,280).buffer(2,quad_segs=8),6.3,H-8.3)
    beam_profile=crossbar_profile(False).buffer(.3,join_style=2)
    channel=extrude(beam_profile.union(translate(beam_profile,yoff=35)).convex_hull,1.7,4.6)
    for side,x in [(0,117.5),(1,369.5)]:
        shelf=rectangle(x+1,1,x+7,272).buffer(1,quad_segs=6)
        rails=[extrude(shelf,6+i*pitch,1.5) for i in range(N)]
        parts[side]=cut(union([parts[side],stop if side==0 else mirror_x(stop),*rails]),channel)
        for i in range(N):
            probe=box(x+.5,4,6.7+i*pitch,7,268,.7)
            assert abs(cut(probe,parts[side]).volume)<.01,('continuous bearing',side,i)
        for travel in [0,.3,1,3,6,10,20,35,60,100,300]:
            assert overlap(move(parts[3],[0,travel,0]),parts[side])<.01,('rear beam insertion',side,travel)
    profile=illustrative_plate()
    for i in range(N):
        for thickness in [.4,.7,1.5]:
            for dx in [-1,0,1]:
                sample=extrude(translate(profile,xoff=dx),7.5+i*pitch,thickness)
                for side,st in [(0,stop),(1,mirror_x(stop))]:
                    assert overlap(sample,parts[side])<.01,('plate seated',i,thickness,dx,side)
                    assert overlap(move(sample,[0,.3,0]),st)>.5,('plate rear stop',i,side)
                    for travel in [0,1,4,80,180,280]:
                        assert overlap(move(sample,[0,-travel,1]),parts[side])<.01,('plate withdrawal',i,side,travel)
    return parts


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    print('Building base modules',flush=True)
    modules={name:build_module(H,N) for name,H,N in [('low',40,5),('standard',60,8)]}
    instances={};groups={};local_parts={}
    def add(name,m,group,z):
        assert m.is_volume and m.is_watertight and len(m.split())==1,('solid',name)
        local_parts[name]=m;instances[name]=move(m,[0,0,z]);groups[name]=group
    for preset,kind,layer,z in [('low','plates',0,0),('standard','plates',1,40),('standard','drawer',2,100)]:
        module=modules[preset];p=module['parts']
        names=['end_left','end_right','cassette_'+kind]
        names+=['drawer'] if kind=='drawer' else ([] if preset=='low' else ['side_bin_left','side_bin_right'])
        for name in names:
            pieces=segment(name,p[name]) if name.startswith('cassette') or name=='drawer' else [p[name]]
            if name=='cassette_plates':pieces=extend_plate_sides(pieces,module['height'],module['plate_count'],module['plate_pitch_mm'])
            for i,m in enumerate(pieces,1):add(f'{preset}_{layer}_{name}_{i}',m,layer,z)
        if layer>0:
            for right in [False,True]:add(f'seam_{layer}_{right}_layer_lock',mirror_x(layer_lock()) if right else layer_lock(),layer,z)
    template={n.removeprefix('standard_2_'):m for n,m in local_parts.items() if n.startswith('standard_2_') and not n.startswith('standard_2_drawer_')}
    multi=[]
    for count,layer,z in [(2,3,160),(3,4,220)]:
        print('Building',count,'drawer module',flush=True)
        parts,tests=variant(count,template);multi+=tests
        for name,m in parts.items():add(f'{count}drawers_{name}',m,layer,z)
        for right in [False,True]:add(f'{count}drawers_seam_2_{right}_layer_lock',mirror_x(layer_lock()) if right else layer_lock(),layer,z)
    print('Building independent top frame',flush=True)
    tops=top_parts()
    for i,m in enumerate(tops,1):add(f'device_adapter_{i}',m,5,280)
    for i,right in enumerate([False,True],1):add(f'top_rear_lock_{i}',mirror_x(layer_lock()) if right else layer_lock(),5,280)
    # Complete assembly pair test, including every seam and locked drawer.
    pairs=0
    for i,(an,a) in enumerate(instances.items()):
        for bn,b in list(instances.items())[i+1:]:
            assert overlap(a,b)<.03,('assembly collision',an,bn,overlap(a,b))
            pairs+=1
    for lower in modules.values():
        for upper in modules.values():check_layer_locks(lower,upper)
    # Final top feet and locking keys enter the uppermost frame.
    end_names=['3drawers_end_left_1','3drawers_end_right_1']
    for dz in [0,.2,1,3,10,30]:
        for m in tops:
            for name in end_names:assert overlap(move(m,[0,0,280+dz]),instances[name])<.01,('top lowering',name,dz)
    for i,right in enumerate([False,True],1):
        key=instances[f'top_rear_lock_{i}']
        for travel in [0,.3,1,3,10,20]:
            for name in end_names+[f'device_adapter_{i}']:
                assert overlap(move(key,[0,travel,0]),instances[name])<.01,('top lock insertion',i,travel,name)
    # No imported models: illustrative plates are generated, kept separate from fabrication parts.
    scene=trimesh.Scene();records=[]
    for name,m in instances.items():
        mesh=m.copy();mesh.visual.vertex_colors=[195,201,204,255] if ('end_' in name or 'device_adapter' in name) else [134,163,178,255]
        if 'layer_lock' in name or 'top_rear_lock' in name:mesh.visual.vertex_colors=[207,139,76,255]
        mesh.apply_scale(.001);mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));scene.add_geometry(mesh,node_name=name)
        path=output/'parts'/f'{name}.stl';path.parent.mkdir(exist_ok=True);local_parts[name].export(path)
        records.append({'name':name,'layer':groups[name],'file':str(path.relative_to(output)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bounds_mm':local_parts[name].bounds.tolist()})
    scene.export(output/'assembly.glb')
    report={'name':'Overstack','construction':'analytic geometry only; no input STL, GLB, PLY, 3MF or traced sections',
            'parts':records,'assembly_pairs_checked':pairs,'multi_drawer_tests':multi,'source_mesh_inputs':[],
            'physical_fit':'not_verified','load_rating':None,'sliced':False,'sent':False}
    (output/'checks.json').write_text(json.dumps(report,indent=2))
    print('PASS',len(records),'parts;',pairs,'assembly pairs',flush=True)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'output/model')
    args=parser.parse_args();build(args.output)
