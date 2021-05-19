#!/usr/local/lcls/package/python/current/bin/python

def create_station_dict(base, alim):
    station_dict = {
        'mode': base + ':DETUNE_MODE',
        'interval': base + ':REP_PERIOD',
        'amp_set': base + ':AOPEN',
        'amp_get': base + ':AACT',
        'ph_set': base + ':POPEN',
        'ph_get': base + ':PACT',
        'a_lim': alim,
        'detune': base + ':DFACT',
        'diff_nom': base + ':FREQ_OFFSET',
        'freq_offset': base + ':DELTA_FREQDES'
        }

    return station_dict

STATIONS = {
    'GUN': create_station_dict('GUN:GUNB:100', 35000),
    'BUNCHER': create_station_dict('ACCL:GUNB:455', 25000)
} 
