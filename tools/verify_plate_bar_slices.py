"""Inspect the print-in-place front spring on both 256 mm plate racks."""
import json,zipfile
from pathlib import Path
import numpy as np
from shapely import Polygon,intersects,linestrings
from verify_front_pin_slices import paths

ROOT=Path(__file__).resolve().parents[1]
for printer in ('x2d','p2s'):
    for layer,ident in [('01-five-slot-plate-layer','A03'),('02-eight-slot-plate-layer','B05')]:
        folder=ROOT/'print-profiles'/printer/'ams2pro-ht'/layer
        job=ROOT/'output'/folder.relative_to(ROOT)
        report=json.loads((folder/'manifest.json').read_text())
        bar=next(r for r in report['parts'] if r['id']==ident);pose=np.array(bar['assembly_to_print'])
        assert np.allclose(pose[2],[0,0,-1,6]) and bar['bed_contact_area_mm2']>5800
        plates=json.loads((job/'assembly.json').read_text())['plates']
        plate,obj=next((i,o) for i,p in enumerate(plates,1) for o in p['objects'] if Path(o['path']).stem.startswith(ident+'-'))
        offset=128-np.array(bar['bounds_mm'][:2])/2+[obj['pos_x'][0],obj['pos_y'][0]]
        corners=np.array([[x,y,0,1] for x,y in [(123.38,5.4),(124.42,5.4),(124.42,23.9),(123.38,23.9)]])
        spring=Polygon((corners@pose.T)[:,:2]+offset)
        for material,path in [('Basic',job/'sliced.3mf'),('Matte',job/'matte/sliced.3mf')]:
            with zipfile.ZipFile(path) as z:gcode=z.read(f'Metadata/plate_{plate}.gcode')
            supports=[];other=0
            for feature,z,a,b in paths(gcode):
                if z>6.2:break
                if not feature.startswith(b'Support'):continue
                # G-code Z is the upper surface of each 0.2 mm bead.
                model_z=6-(z-.1)
                if 2.<model_z<2.6 or 0.<model_z<.5:supports.append([a,b])
                else:other+=1
            assert other,(printer,ident,material,'missing support positive control')
            assert not supports or not intersects(linestrings(np.array(supports)),spring).any(),(printer,ident,material,'support inside spring clearance')
            print(printer,ident,material,'PASS: no support in spring clearance',flush=True)
