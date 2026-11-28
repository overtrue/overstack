"""Check actual support toolpaths around the HT lock and rounded exterior."""
from collections import defaultdict
from pathlib import Path
import json
import numpy as np
from shapely import Polygon,box,intersects,linestrings
from print_profile_targets import TARGETS
from print_slice_metrics import metrics

ROOT=Path(__file__).resolve().parents[1]

def check(printer,project,archive,density):
    profile=Path(printer)/project
    work=ROOT/'output/print-profiles'/profile
    report=json.loads((ROOT/'print-profiles'/profile/'manifest.json').read_text())
    records={r['id']:r for r in report['parts']}
    paths=defaultdict(list)

    def record(plate,command,start,end):
        assert command in (b'G0',b'G1'),'arc support paths require an arc-aware contact check'
        paths[plate].append((start,end))

    result=metrics(work/archive,record,density=density)
    if project.startswith('replacement/'):
        assert 0<result['support_g']<1,(profile,archive,'support extrusion',result)
    plates=json.loads((work/'assembly.json').read_text())['plates']
    x0,y0,x1,y1=TARGETS[printer]['area'];centre=np.array([(x0+x1)/2,(y0+y1)/2])
    checked=set()
    for i,plate in enumerate(plates,1):
        extrusions=linestrings(np.asarray(paths[i]).reshape(-1,2,2))
        for obj in plate['objects']:
            part=Path(obj['path']).name.split('-')[0]
            if part not in ('F02','F03','F04','F05'):continue
            checked.add(part)
            row=records[part];matrix=np.array(row['assembly_to_print'])
            offset=centre-np.array(row['bounds_mm'][:2])/2+[obj.get('pos_x',[0])[0],obj.get('pos_y',[0])[0]]
            if part in ('F03','F04'):
                assert np.allclose(row['bounds_mm'],[12,16,5.3],atol=.001) and np.isclose(row['bed_contact_area_mm2'],162),(profile,part,'key not face-down')
                region=box(*offset,*(offset+row['bounds_mm'][:2])).buffer(.5)
                assert not intersects(extrusions,region).any(),(profile,archive,part,'support on key')
                continue
            assert np.allclose(matrix[2,:3],[0,0,1]),(printer,part,'flat print pose')
            ymin,ymax=(0,22) if part=='F02' else (265,287)
            zones=[(473,ymin,495,ymax),(433,ymin,440,ymax)]
            if part=='F05':zones.append((449,279,465,287))
            # The open F01 sliding joint still needs supports and is the positive control.
            for index,(x,y,xx,yy) in enumerate([*zones,(245,ymin,255,ymax)]):
                corners=np.array([[x,y,0,1],[xx,y,0,1],[xx,yy,0,1],[x,yy,0,1]])
                region=Polygon((corners@matrix.T)[:,:2]+offset).buffer(1)
                found=bool(intersects(extrusions,region).any())
                assert found==(index==len(zones)),(profile,archive,part,i,(x,y,xx,yy),'support contact',found)
    expected={'F02','F04','F05'} if project.startswith('replacement/') else {'F02','F03','F04','F05'}
    assert checked==expected,(profile,checked)


if __name__=='__main__':
    for printer,target in TARGETS.items():
        materials=[('sliced.3mf',1.25)]
        if target['group']=='256':materials.append(('matte/sliced.3mf',1.37))
        for archive,density in materials:
            for project in ('replacement/ht-top-right','ams2pro-ht/06-device-top'):
                check(printer,project,archive,density)
            sample=metrics(ROOT/'output/print-profiles'/printer/'fit-check/ht-top'/archive,density=density)
            assert sample['plate_count']==1 and sample['support_g']==0,(printer,archive,'corner fit plate',sample)
            print(printer,archive,'PASS: flat, support-free rear keys and F05 socket; one support-free test plate',flush=True)
