#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import motion_constants as mc
from .logger import logger

def get_motions():
    """Return MAD names of all movers that have models"""
    return mc.MOTIONS.keys()

class Motion(object):
    def __init__(self, name='SOL1B_X'):
        if name not in mc.MOTIONS.keys():
            raise ValueError('You have not specified a valid motion')
        motion_dict = mc.MOTIONS[name]
        self._name = name
        self._set = PV(motion_dict['set'])
        self._rbv = PV(motion_dict['rbv'])
        self._logger = logger.custom_logger(__name__)

    @property
    def name(self):
        return self._name

    @property
    def pos_set(self):
        return self._set.get()

    @pos_set.setter
    def pos_set(self, val):
        if not (isinstance(val, int) or isinstance(val, float)):
            self._logger.info('position must be int or float {0}'.format(val))
            return

        self._set.put(val)

    @property
    def pos_rbv(self):
        return self._rbv.get()

