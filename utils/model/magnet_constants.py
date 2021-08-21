#!/usr/local/lcls/package/python/current/bin/python

CTRL = [
    'Ready',
    'TRIM',
    'PERTURB',
    'BCON_TO_BDES',
    'SAVE_BDES',
    'LOAD_BDES',
    'UNDO_BDES',
    'DAC_ZERO',
    'CALIB',
    'STDZ',
    'RESET'
]


def create_mag_dict(base, tol, length, d):
    mag_dict = {
        'bctrl': base + ':BCTRL',
        'bact': base + ':BACT',
        'bdes': base + ':BDES',
        'bcon': base + ':BCON',
        'ctrl': base + ':CTRL',
        'tol': tol,
        'length': length,
        'd': d
    }

    return mag_dict


MAGNETS = {
    'SOL1B': create_mag_dict('SOLN:GUNB:212', .002, .0861, .2),
    'SOL2B': create_mag_dict('SOLN:GUNB:823', 0.002, 0.0861, .2),
}
