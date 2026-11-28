"""Bed-flat AMS HT top sections and drop-in corner feet, in assembly coordinates."""
from geometry import Polygon, rectangle, box, cut, extrude, intersection, union, xz_extrude, mirror_x
from corner_pins import loose_pin,top_socket
from layer_locks import pocket_profile


def print_rotation(name):
    if name in ('device_adapter_2','ht_top_rear'):return ([1,0,0],0)
    if name in ('ht_foot_front','ht_foot_rear'):return ([1,0,0],0)
    if name in ('top_rear_lock_1','top_rear_lock_2'):return ([1,0,0],90)
    return None


def right_top_parts(blank):
    # Keep the device step and the two original AMS-side sliding joints. The
    # ledges at z=0 transfer weight directly onto the layer below each rail.
    frame=intersection(blank,box(240,-1,0,260,289,27))
    feet=[]
    # The removable dowels sit in the lower frame first. The underside sockets
    # have a short self-supporting roof and stop below the equipment shelf.
    for back in (False,True):
        frame=cut(frame,top_socket(True,back))
        feet.append(loose_pin(True,back))

    # Stagger the joints by 51 mm; the transition at x=430 is in the HT opening.
    front=rectangle(240,-2,430,115).union(rectangle(430,-2,500,166))
    # Keep the outer tongue wholly below the vertical lip at x=492; a tongue
    # crossing its inner edge leaves a feather-thin unsupported lip extension.
    for cx,y,neck,head in [(366.2,115,3.1,5.5),(489.15,166,1.45,2.45)]:
        tongue=Polygon([(cx-neck,y-1),(cx-neck,y+.6),(cx-head,y+5),
                        (cx-head,y+7),(cx+head,y+7),(cx+head,y+5),
                        (cx+neck,y+.6),(cx+neck,y-1)])
        tongue=tongue.buffer(-.45,join_style='round').buffer(.45,quad_segs=8)
        front=front.union(tongue)
    rear=cut(frame,extrude(front.buffer(.30,join_style='round'),-1,29))
    # Provide a printable ceiling above the standard bowtie. Keep its waist
    # and both retaining shoulders intact. The two slopes are 45 degrees.
    xmin,_,xmax,seat=pocket_profile().bounds
    cx=(xmin+xmax)/2
    half_bridge=.75
    crown=seat+(xmax-cx)-half_bridge
    roof=Polygon([(xmin,seat-.1),(xmax,seat-.1),(xmax,seat),
                  (cx+half_bridge,crown),(cx-half_bridge,crown),(xmin,seat)])
    rear=cut(rear,mirror_x(xz_extrude(roof,281,7)))
    parts=[intersection(frame,extrude(front,-1,29)),rear,*feet]
    assert all(part.is_volume and len(part.split())==1 for part in parts)
    return parts
