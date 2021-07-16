#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import motor_constants as mtc
from .logger import logger

def get_motors():
    """Return MAD names of all movers that have models"""
    return mtc.MOTORS.keys()

class Motor(object):
    def __init__(self, name='SOL1B_M1'):
        if name not in mtc.MOTORS.keys():
            raise ValueError('You have not specified a valid motor')
        motor_dict = mtc.MOTORS[name]
        self._name = name
        self._set = PV(motor_dict['set'])
        self._rbv = PV(motor_dict['rbv'])
        self._status = PV(motor_dict['status'])
        self._status_vars = self._status.get_ctrlvars()
        self._logger = logger.custom_logger(__name__)

    @property
    def name(self):
        return self._name

    @property
    def pos_set(self):
        return self._set.get()

    @pos_set.setter
    def pos_set(self, val):
        if not isinstance(val, int) or isinstance(val, float):
            self._logger('position must be int or float')
            return

        self._set.put(val)

    @property
    def pos_rbv(self):
        return self._rbv.get()

    @property
    def status_vars(self):
        return self._status_vars
