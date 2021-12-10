#!/usr/local/lcls/package/python/current/bin/python

def create_motion_dict(base):
    motion_dict = {
        'set': base + ':DES',
        'rbv': base + ':ACT',
    }
    
    return motion_dict

MOTIONS = {
    'SOL1B_X': create_motion_dict('MOVR:GUNB:212:X'),
    'SOL1B_XP': create_motion_dict('MOVR:GUNB:212:XANG'),
    'SOL1B_Y': create_motion_dict('MOVR:GUNB:212:Y'),
    'SOL1B_YP': create_motion_dict('MOVR:GUNB:212:YANG'),
    'SOL2B_X': create_motion_dict('MOVR:GUNB:823:X'),
    'SOL2B_XP': create_motion_dict('MOVR:GUNB:823:XANG'),
    'SOL2B_Y': create_motion_dict('MOVR:GUNB:823:Y'),
    'SOL2B_YP': create_motion_dict('MOVR:GUNB:823:YANG'),
}

