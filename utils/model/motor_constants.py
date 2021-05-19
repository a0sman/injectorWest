#!/usr/local/lcls/package/python/current/bin/python

def create_motor_dict(base):
    motor_dict = {
        'set': base + ':MOTR',
        'rbv': base + ':RBV',
        'status': base + ':MOTR.DMOV'
    }
    
    return motor_dict

MOTORS = {
    'SOL1B_M1': create_motor_dict('MOVR:GUNB:212:1'),
    'SOL1B_M2': create_motor_dict('MOVR:GUNB:212:2'),
    'SOL1B_M3': create_motor_dict('MOVR:GUNB:212:3'),
    'SOL1B_M4': create_motor_dict('MOVR:GUNB:212:4'),
    'SOL1B_M5': create_motor_dict('MOVR:GUNB:212:5'),
    'SOL2B_M1': create_motor_dict('MOVR:GUNB:823:1'),
    'SOL2B_M2': create_motor_dict('MOVR:GUNB:823:2'),
    'SOL2B_M3': create_motor_dict('MOVR:GUNB:823:3'),
    'SOL2B_M4': create_motor_dict('MOVR:GUNB:823:4'),
    'SOL2B_M5': create_motor_dict('MOVR:GUNB:823:5')
}

