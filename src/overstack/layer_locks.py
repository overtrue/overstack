"""Plain rear inter-layer bowtie inserts, without pins or tail keepers."""
from geometry import *

REAR_LOCK_FILE = 'models/common/rear-lock.stl'
KEY_THICKNESS = 5.3


def locking_profile(cx=38):
    return Polygon([(cx-6,-8),(cx+6,-8),(cx+6,-5),(cx+3,0),(cx+6,5),(cx+6,8),(cx-6,8),(cx-6,5),(cx-3,0),(cx-6,-5)])


def layer_lock():
    return xz_extrude(locking_profile(),281.35,KEY_THICKNESS)


def flat_layer_lock():
    """The common spare in print coordinates, with its broad face at Z=0."""
    return extrude(locking_profile(cx=0),0,KEY_THICKNESS)


def pocket_profile():
    return locking_profile().buffer(.35,join_style=2)


def lock_pocket():
    return xz_extrude(pocket_profile(),281,7)


def lock_pockets(end,H,right=False):
    pocket=lock_pocket()
    cuts=union([move(pocket,[0,0,H]),pocket])
    return cut(end,mirror_x(cuts) if right else cuts)


def lock_parts(right=False):
    key=layer_lock()
    return [('layer_lock',mirror_x(key) if right else key)]


def check_layer_locks(lower,upper):
    for right in [False,True]:
        low=move(lower['ends'][int(right)],[0,0,-lower['height']])
        high=upper['ends'][int(right)]
        key=mirror_x(layer_lock()) if right else layer_lock()
        pieces=lock_parts(right)
        for _,part in pieces:
            assert overlap(part,low)<.01 and overlap(part,high)<.01,'layer lock seated interference'
        assert overlap(key,move(high,[0,0,.8]))>.1,'layer lock does not retain upper end'
        assert overlap(key,move(low,[0,0,-.8]))>.1,'layer lock does not retain lower end'
        for travel in [0,.3,1,3,6,10,20]:
            assert overlap(move(key,[0,travel,0]),low)<.01
            assert overlap(move(key,[0,travel,0]),high)<.01
        filled=box(36,270,-7,4,10,4)
        if right:filled=mirror_x(filled)
        assert abs(cut(filled,low).volume)<.01,'obsolete pin bore remains'
    assert abs(layer_lock().volume-locking_profile().area*5.3)<.01,'insert still has a pin hole'
    return {'rear_bowtie_locks':2,'retainer_pins':0,'tail_keepers':0,'uplift_blocked':True,'rear_withdrawal_free':True,'direct_rear_insertion_checked':True}
