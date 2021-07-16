#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import mover_constants as mvc
from .logger import logger

def get_movers():
    """Return MAD names of all movers that have models"""
    return mvc.MOVERS.keys()

class Mover(object):
    def __init__(self, name):
        if name not in mvc.MOVERS:
            raise ValueError('You have not specified a valid mover')
        mover_dict = mvc.MOVERS[name]
        self._name = name
        
    @property
    def name(self):
        return self._name
        
