#!/usr/local/lcls/package/python/current/bin/python

def create_bpm_dict(base):
    bpm_dict = {
        'x': base + ':X',
        'y': base + ':Y',
        'tmit': base + ':TMIT',
        'z': base + ':Z'
    }
    
    return bpm_dict

BPMS = {
    'BPM1B': create_bpm_dict('BPMS:GUNB:314'),
    'BPM2B': create_bpm_dict('BPMS:GUNB:925')
}
