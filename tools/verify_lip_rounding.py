"""Check R3 lip ends on exported tops, including the retained bearing region."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/stacknest'))
from geometry import *

for width,paths in [
    (495,sorted((ROOT/'models/ams2pro+ht/06-device-top/parts').glob('*device_adapter*.stl'))),
    (399,sorted((ROOT/'models/ams2pro/device-top').glob('top_*.stl'))),
]:
    assert len(paths)==2
    top=union([trimesh.load_mesh(p) for p in paths])
    for right in [False,True]:
        for y in [1.5,285.5]:
            # Sample both sides of the R3 arc, away from its tessellated boundary.
            for angle in np.linspace(5,85,17):
                for radius,inside in [(2.8,True),(3.2,False)]:
                    a=np.radians(angle);x=57+radius*np.cos(a);z=23+radius*np.sin(a)
                    if right:x=width-x
                    probe=box(x-.02,y-.02,z-.02,.04,.04,.04)
                    v=overlap(top,probe)
                    assert (v>probe.volume*.99 if inside else v<1e-8),(width,right,y,angle,radius,v)
            # The lower lip and supporting frame remain solid at the end.
            x=width-59.5 if right else 59.5
            probe=box(x-.1,y-.1,15.9,.2,.2,6.9)
            assert abs(cut(probe,top).volume)<1e-6,(width,right,y,'bearing region')
    assert top.is_volume
print('PASS: all 8 exposed lip tips follow R3; lower lips and bearing faces retained.')
