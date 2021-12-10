#!/usr/local/lcls/package/python/current/bin/python

def create_bpm_dict(base):
    bpm_dict = {
        'alarm': base + ':STA_ALH',
        'status': base + ':STA',
        'x': base + ':X_SLOW',
        'y': base + ':Y_SLOW',
        'tmit': base + ':TMIT_SLOW',
        'z': base + ':Z'
    }
    
    return bpm_dict

BPMS = {
    'BPM1B': create_bpm_dict('BPMS:GUNB:314'),
    'BPM2B': create_bpm_dict('BPMS:GUNB:925')
}
