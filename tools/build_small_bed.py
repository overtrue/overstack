"""Generate the 256 mm cutting lists from the same assembled parts as the large beds."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/overstack'))
from geometry import box,cut,extrude,intersection,move,np,overlap,trimesh,union
from corner_pins import legacy_socket
from small_bed import split
from multi_drawers import middle_beam
from build_print_profiles import canonical_recipes
from print_layout import orient_for_area
from print_profile_targets import TARGETS

DEST=ROOT/'models/256'
X,Y=[1,0,0],[0,1,0]


def cut_family(name):
    if 'end_left' in name or 'end_right' in name:return 'end'
    if 'plate_carrier_' in name or re.search(r'cassette_plates_[12]$',name):return 'carrier'
    if re.search(r'(?:^|_)drawer_[123]$',name):return 'drawer'
    if name in ('top_1','top_2') or name.endswith('device_adapter_1'):return 'top'
    if 'divider_' in name:return 'divider'


def rotation(family,section):
    if family in ('end','drawer','carrier','top','divider'):
        return (X,90 if section==0 else -90)
    return None


def save(folder,ident,mesh,rotation,**fields):
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(ident+'.stl');mesh.export(path)
    row={'id':ident,'file':str(path.relative_to(ROOT)),**fields}
    if rotation:
        _,pose=orient_for_area(mesh,TARGETS['x2d']['area'],256,rotation=rotation)
        row['print_rotation']=np.array(pose['assembly_to_print'])[:3,:3].tolist()
    return row


def write(folder,rows):
    folder.mkdir(parents=True,exist_ok=True)
    index=folder/'parts.json'
    wanted={r['file'] for r in rows}
    if index.is_file():
        for old in json.loads(index.read_text()):
            source=ROOT/old['file']
            if source.parent==folder and old['file'] not in wanted:source.unlink(missing_ok=True)
    index.write_text(json.dumps(rows,indent=2)+'\n')


def build():
    for key,rows in canonical_recipes():
        if not key.startswith(('ams2pro/','ams2pro-ht/')):continue
        folder=DEST/key;folder.mkdir(parents=True,exist_ok=True);out=[]
        for row in rows:
            source=ROOT/row['file'];name=source.stem;ident=row['id']
            if key.startswith('ams2pro/') and '_beam_' in name:
                if name.endswith('_2'):continue
                front=name.startswith('front_');whole=middle_beam(front,399)
                if key.endswith('2-drawer-layer'):
                    whole=cut(whole,box(196.5,(8 if front else 267)-.3,2,6,12.6,4.1))
                pair=[r for r in rows if Path(r['file']).stem.split('_beam_')[0]==name.split('_beam_')[0]]
                for r in pair:
                    half=trimesh.load_mesh(ROOT/r['file'])
                    assert cut(half,whole).volume<.03,(key,ident,'beam changed outside the splice')
                out.append(save(folder,ident+'J',whole,None,parent_ids=[r['id'] for r in pair]))
                continue
            family=cut_family(name)
            if family:
                mesh=trimesh.load_mesh(source)
                right='right' in name or name.endswith(('cassette_plates_2','top_2'))
                for i,part in enumerate(split(mesh,family,right)):
                    out.append(save(folder,ident+'ab'[i],part,rotation(family,i),parent_ids=[ident],
                                    offset_mm=row.get('offset_mm',[0,0,0])))
            elif name.endswith('cassette_plates_3'):
                # Top face down keeps tree supports out of the 0.6 mm spring
                # clearance while the full 244 x 24 mm face stays on the bed.
                mesh=trimesh.load_mesh(source)
                _,pose=orient_for_area(mesh,TARGETS['x2d']['area'],256,rotation=(X,180))
                out.append({**row,'print_rotation':np.array(pose['assembly_to_print'])[:3,:3].tolist()})
            else:out.append(row)
        write(folder,out)
    for h in (40,60):
        folder=DEST/'common'/f'pegboard-{h}';rows=[]
        for right,hand in enumerate(['left','right']):
            source=ROOT/'models/common'/f'end_{hand}_{h}_pegboard.stl'
            mesh=trimesh.load_mesh(source)
            # The perforated exterior is a continuous first layer. Separate
            # left/right transforms keep the visible face on the build plate.
            _,pose=orient_for_area(mesh,TARGETS['x2d']['area'],256,rotation=(Y,90 if right else -90))
            rows.append({'id':f'G{h}'+hand[:1].upper(),'file':str(source.relative_to(ROOT)),
                         'parent_ids':[source.stem],'print_rotation':np.array(pose['assembly_to_print'])[:3,:3].tolist()})
        write(folder,rows)
    # A completed earlier HT-side top can keep its original curved feet.
    # These two end sections have round pins below and legacy seats above.
    for h in (40,60):
        folder=DEST/'compatibility'/f'ht-right-{h}';rows=[]
        source=ROOT/'models/common'/f'end_right_{h}_plain.stl'
        end=trimesh.load_mesh(source)
        for back in (False,True):
            pocket=legacy_socket(True,back)
            boss=extrude(pocket.buffer(3,quad_segs=12),0,h)
            end=cut(union([end,boss]),extrude(pocket,h-3.5,3.6))
        for i,part in enumerate(split(end,'end',True)):
            rows.append(save(folder,f'L{h}R'+'ab'[i],part,rotation('end',i),parent_ids=[source.stem]))
        write(folder,rows)
    # A three-piece test of the actual marked front corner, with no rear lock.
    folder=DEST/'fit-check/front-pin'
    top=ROOT/'models/ams2pro+ht/06-device-top/parts'
    corner=box(470,0,-9,26,25,36)
    lower=move(trimesh.load_mesh(ROOT/'models/common/end_right_60_plain.stl'),[0,0,-60])
    upper=trimesh.load_mesh(next(top.glob('F02-*.stl')))
    pin=trimesh.load_mesh(next(top.glob('F06-*.stl')))
    rows=[save(folder,'P1',intersection(lower,corner),(X,90),parent_ids=['end_right_60_plain']),
          save(folder,'P2',intersection(upper,corner),(X,0),parent_ids=['F02']),
          save(folder,'P3',pin,(X,0),parent_ids=['F06'])]
    write(folder,rows)
    # Exact portions of a production drawer floor/wall and carrier spine.
    folder=DEST/'fit-check/256-joints';rows=[]
    for prefix,key,parent,region in [
        ('W','ams2pro/2-drawer-layer','ND10',box(67,122,6,46,28,57)),
        ('R','ams2pro/8-slot-plate-layer','NB03',box(53,130,0,32,33,19)),
        ('S','ams2pro/8-slot-plate-layer','NB01',box(-1,133,0,16,25,18))]:
        parts=json.loads((DEST/key/'parts.json').read_text())
        for suffix in 'ab':
            row=next(r for r in parts if r['id']==parent+suffix)
            clipped=intersection(trimesh.load_mesh(ROOT/row['file']),region)
            assert clipped.is_volume and len(clipped.split())==1,(parent,suffix)
            rows.append(save(folder,prefix+suffix,clipped,(X,90 if suffix=='a' else -90),parent_ids=[row['id']]))
    ht=json.loads((ROOT/'models/fit-check/ht-top-parts.json').read_text())
    for row in ht:
        if row['id'] in ('HT01','HT02','HT04'):rows.append(row)
    write(folder,rows)
    print('256 mm layers, optional end panels and joint specimens generated',flush=True)


if __name__=='__main__':build()
