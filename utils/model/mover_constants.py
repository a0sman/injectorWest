#!/usr/local/lcls/package/python/current/bin/python

import motor_constants as mtc

SOL1B_MOV = {
    'motors': {'SOL1B_M1': mtc.MOTORS['SOL1B_M1'],
               'SOL1B_M2': mtc.MOTORS['SOL1B_M2'],
               'SOL1B_M3': mtc.MOTORS['SOL1B_M3'],
               'SOL1B_M4': mtc.MOTORS['SOL1B_M4'],
               'SOL1B_M5': mtc.MOTORS['SOL1B_M5']},
    'off': 'ACSW:LI00:NW02:2POWEROFF',
    'on': 'ACSW:LI00:NW02:2POWERON',
    'power_state': 'ACSW:LI00:NW02:2POWERSTATE'
}

SOL2B_MOV = {
    'motors': {'SOL2B_M1': mtc.MOTORS['SOL2B_M1'],
               'SOL2B_M2': mtc.MOTORS['SOL2B_M2'],
               'SOL2B_M3': mtc.MOTORS['SOL2B_M3'],
               'SOL2B_M4': mtc.MOTORS['SOL2B_M4'],
               'SOL2B_M5': mtc.MOTORS['SOL2B_M5']},
    'off': 'ACSW:LI00:NW02:3POWEROFF',
    'on': 'ACSW:LI00:NW02:3POWERON',
    'power_state': 'ACSW:LI00:NW02:3POWERSTATE'
}

MOVERS = {
    'SOL1B_MOV': SOL1B_MOV,
    'SOL2B_MOV': SOL2B_MOV
}
