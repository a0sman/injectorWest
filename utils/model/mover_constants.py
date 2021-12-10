#!/usr/local/lcls/package/python/current/bin/python

from .motion_constants import MOTIONS

SOL1B_MOV = { 'X': MOTIONS['SOL1B_X'],
               'XP': MOTIONS['SOL1B_XP'],
               'Y': MOTIONS['SOL1B_Y'],
               'YP': MOTIONS['SOL1B_YP']
}
SOL2B_MOV = {'X': MOTIONS['SOL2B_X'],
               'XP': MOTIONS['SOL2B_XP'],
               'Y': MOTIONS['SOL2B_Y'],
               'YP': MOTIONS['SOL2B_YP']
}

MOVERS = {
    'SOL1B': SOL1B_MOV,
    'SOL2B': SOL2B_MOV
}
