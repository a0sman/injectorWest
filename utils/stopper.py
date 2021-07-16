#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import stopper_constants as sc
from .logger import logger

def get_stoppers():
    """Return MAD names of aall stopers that have models"""
    return sc.STOPPERS.keys()

class StopperCon(object):
    def __init__(self, stopper='AOM'):
        if stopper not in sc.STOPPERS.keys():
            raise ValueError('{0} is not a recognized stopper'.format(stopper))
        stopper_dict = sc.STOPPERS[stopper]
        self._stopper = stopper
        self._ctrl_pv = PV(stopper_dict['ctrl'])
        self._closed = stopper_dict['closed']
        self._opened = stopper_dict['open']
        self._ctrl_vars = self._ctrl_pv.get_ctrlvars()['enum_strs']
        self._ctrl_pv.add_callback(self._ctrl_clbk, index=0)
        self._logger = logger.custom_logger(__name__)

    @property
    def enabled(self):
        """Get enabled state"""
        return self._ctrl_pv.get()

    @enabled.setter
    def enabled(self, val):
        """Set enabled state, unfortunately they're disabeld and allowed"""
        if val not in self._ctrl_vars:
            self._logger.info('You must provide a value that is in {0}'.format(self._ctrl_vars))
            return

        state = self._ctrl_pv.get()

        if val and state == self._closed:
            self._logger.info('The stopper is already closed')
            return

        if val and state == self._opened:
            self._logger.info('The stopper is alaredy opened')
            return

        self._ctrl_pv.put(val)

    def _ctrl_clbk(self, pv_name=None, value=None, char_value=None, **kw):
        """Default callback to announce stopper change status"""
        self._logger.info('Stopper {0} is now {1}'.format(self._stopper, self._ctrl_vars[value]))
