"""Full AMS 2 Pro + HT stack, from the bottom up. Public part IDs stay stable."""
LAYERS = (
    ('A', '01-five-slot-plate-layer', 0),
    ('B', '02-eight-slot-plate-layer', 40),
    ('D', '04-double-drawer-layer', 100),
    ('E', '05-triple-drawer-layer', 160),
    ('F', '06-device-top', 220),
)

# F03 and F04 identify the two installed copies of the common rear key.
TOP_NAMES = ('device_adapter_1', 'device_adapter_2', 'top_rear_lock_1', 'top_rear_lock_2',
             'ht_top_rear', 'ht_foot_front', 'ht_foot_rear')
