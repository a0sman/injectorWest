#!/usr/local/lcls/package/python/current/bin/python

AOM = {
    'ctrl': 'SIOC:SYS0:MP01:DISABLE_AOM',
    'status': 'MPLN:GUNB:MP01:1:RTM_DO',
    'closed': 'AOM Disabled',
    'open': 'AOM Allowed'
}

MPS_SHUTTER = {
    'ctrl': 'SIOC:SYS0:MP01:DISABLE_BEAM',
    'status': 'SHUT:GUNB:100:CLOSED_STATUS_MPSC',
    'closed': 'Shutter Disabled',
    'open': 'Shutter Allowed'
}

STOPPERS = {
    'AOM': AOM,
    'MPS': MPS_SHUTTER
}
