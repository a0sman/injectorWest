#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import mover_constants as mvc
from .logger import logger
from .motion import Motion
def get_movers():
    """Return MAD names of all movers that have models"""
    return mvc.MOVERS.keys()

class Mover(object):
    def __init__(self, name):
        if name not in mvc.MOVERS:
            raise ValueError('You have not specified a valid mover')
        self._mover_dict = {m: Motion(name + '_' + m) for m in mvc.MOVERS[name].keys()}
        self._name = name
        
    @property
    def name(self):
        return self._name
    @property
    def x(self):
        return self._mover_dict['X'].pos_rbv
    @x.setter
    def x(self, a):
        self._mover_dict['X'].pos_set = a
    @property
    def xp(self):
        return self._mover_dict['XP'].pos_rbv
    @xp.setter
    def xp(self, a):
        self._mover_dict['XP'].pos_set = a
    @property
    def y(self):
        return self._mover_dict['Y'].pos_rbv
    @y.setter
    def y(self, a):
        self._mover_dict['Y'].pos_set = a
    @property
    def yp(self):
        return self._mover_dict['YP'].pos_rbv
    @yp.setter
    def yp(self, a):
        self._mover_dict['YP'].pos_set = a
        
