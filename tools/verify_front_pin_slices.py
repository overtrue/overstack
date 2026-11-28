"""Inspect the F06 support paths and the printed outside arc of the F02 front corner."""
from collections import defaultdict
import json,re,zipfile
from pathlib import Path
import numpy as np
from shapely import MultiLineString,box,distance,intersects,linestrings,points

ROOT=Path(__file__).resolve().parents[1]
AXES=re.compile(rb'\b([XYE])([-\d.]+)')


def paths(gcode):
    feature=b'';xy=[0.,0.];z=0
    for line in gcode.splitlines():
        if line.startswith(b'; Z_HEIGHT: '):z=float(line[12:]);continue
        if line.startswith(b'; FEATURE: '):feature=line[11:].strip();continue
        if not line.startswith((b'G0 ',b'G1 ',b'G2 ',b'G3 ')):continue
        axes=dict(AXES.findall(line.split(b';',1)[0]))
        new=[float(axes.get(k,v)) for k,v in zip((b'X',b'Y'),xy)]
        if feature in (b'Support',b'Support interface',b'Outer wall',b'Overhang wall') and float(axes.get(b'E',0))>0 and new!=xy:
            assert line.startswith((b'G0 ',b'G1 ')),'arc toolpath requires an arc-aware distance check'
            yield feature,z,xy,new
        xy=new


def check(printer,profile,corner_id):
    folder=ROOT/'print-profiles'/printer/profile;work=ROOT/'output/print-profiles'/printer/profile
    parts={r['id']:r for r in json.loads((folder/'manifest.json').read_text())['parts']}
    layout=json.loads((work/'assembly.json').read_text())['plates']
    for plate_no,plate in enumerate(layout,1):
        offsets={}
        for obj in plate['objects']:
            ident=Path(obj['path']).stem.split('-')[0]
            offsets[ident]=128-np.array(parts[ident]['bounds_mm'][:2])/2+[obj['pos_x'][0],obj['pos_y'][0]]
        if corner_id not in offsets:continue
        pose=np.array(parts[corner_id]['assembly_to_print']);assert np.allclose(pose[2,:3],[0,0,1])
        # The R15 front-right arc is centred at (480, 15). Sample the nominal
        # centre of the outer extrusion, 0.20 mm inward, at one-degree spacing.
        angles=np.deg2rad(np.arange(-89,0));one=np.ones(len(angles))
        samples=np.column_stack((480+14.8*np.cos(angles),15+14.8*np.sin(angles),one,one))
        coords=(samples@pose.T)[:,:2]+offsets[corner_id]
        lo,hi=coords.min(axis=0)-1,coords.max(axis=0)+1
        for material,archive in [('Basic',work/'sliced.3mf'),('Matte',work/'matte/sliced.3mf')]:
            with zipfile.ZipFile(archive) as z:gcode=z.read(f'Metadata/plate_{plate_no}.gcode')
            supports=[];heights=[];walls=defaultdict(list)
            for feature,z,start,end in paths(gcode):
                if feature in (b'Support',b'Support interface'):
                    if corner_id=='P2':supports.append([start,end]);heights.append(z)
                elif min(start[0],end[0])<=hi[0] and max(start[0],end[0])>=lo[0] and min(start[1],end[1])<=hi[1] and max(start[1],end[1])>=lo[1]:
                    walls[z].append([start,end])
            if corner_id=='P2':
                assert heights and max(heights)<2.,(printer,material,'support reaches socket')
                lines=linestrings(np.array(supports))
                for ident,base in offsets.items():
                    bounds=box(*base,*(base+parts[ident]['bounds_mm'][:2])).buffer(.5)
                    assert bool(intersects(lines,bounds).any())==(ident=='P1'),(printer,material,ident,'support contact')
                # The front rim of the P1 socket starts beyond 5 mm in this pose.
                assert np.allclose(np.array(parts['P1']['assembly_to_print'])[2,:3],[0,1,0])
            assert {round(i*.2,2) for i in range(1,131)}<=set(walls),(printer,material,'missing R15 layer')
            for z,segments in walls.items():
                error=distance(points(coords),MultiLineString(segments)).max()
                # Allow the deliberate first-layer elephant-foot compensation.
                assert error<(.27 if z==.2 else .12),(printer,material,corner_id,z,'gap in sliced arc',error)
            print(printer,material,corner_id,'PASS: R15 outer wall present at 89 positions on all 130 layers',flush=True)
        return
    raise AssertionError((printer,profile,corner_id,'missing part'))


if __name__=='__main__':
    for printer in ['x2d','p2s']:
        check(printer,'fit-check/front-pin','P2')
        check(printer,'ams2pro-ht/06-device-top','F02')
