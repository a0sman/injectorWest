#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import bpm_constants as bc
import numpy as np
from .logger import logger
from threading import Thread

def get_bpms():
    """Return different bpms in model"""
    return bc.BPMS.keys()

class BPM(object):
    """Generic BPM Object class"""
    def __init__(self, bpm_name='BPM1B'):
        if bpm_name not in bc.BPMS.keys():
            raise ValueError('You have not specified a valid bpm')
        bpm_dict = bc.BPMS[bpm_name]
        self._name = bpm_name
        self._x = PV(bpm_dict['x'], form='time')
        self._y = PV(bpm_dict['y'], form='time')
        self._z = PV(bpm_dict['z'])
        self._tmit = PV(bpm_dict['tmit'], form='time')
        self._status = PV(bpm_dict['status'])
        self._alarm = PV(bpm_dict['alarm'])
        self._x_data = []
        self._y_data = []
        self._tmit_data = []
        self._readings = 1
        self._gathering_data = False
        self._logger = logger.custom_logger(__name__)
        self._data_clbk = None
        self._data_thread = None

    @property
    def name(self):
        """Get MAD name of bpm"""
        return self._name

    @property
    def x(self):
        """Get current x reading"""
        return self._x.get()

    @property
    def y(self):
        """Get current y reading"""
        return self._y.get()

    @property
    def z(self):
        """Get z position"""
        return self._z.get()

    @property
    def tmit(self):
        """Get current tmit reading"""
        return self._tmit.get()

    @property
    def current_data(self):
        """Get the current x, y, and tmit data tuple"""
        return (self._x_data, self._y_data, self._tmit_data)

    @property
    def gathering_data(self):
        """Get bool indicating whether the bpm is gathering data or not"""
        return self._gathering_data

    @property
    def x_ave(self):
        """Get the average of the x data list"""
        if not self._x_data:
            self._logger.info("You have no x data")
            return None

        return np.mean(self._x_data)

    @property
    def y_ave(self):
        """Get the average of the y data list"""
        if not self._y_data:
            self._logger.info("You have no y data")
            return None

        return np.mean(self._y_data)

    @property
    def tmit_ave(self):
        """Get the average of the tmit data list"""
        if not self._tmit_data:
            self._logger.info("You have no tmit data")
            return None

        return np.mean(self._tmit_data) 

    @property
    def x_std(self):
        """Get the average of the x data list"""
        if not self._x_data:
            self._logger.info("You have no x data")
            return None

        return np.std(self._x_data)

    @property
    def y_std(self):
        """Get the average of the y data list"""
        if not self._y_data:
            self._logger.info("You have no y data")
            return None

        return np.std(self._y_data)

    @property
    def tmit_std(self):
        """Get the average of the tmit data list"""
        if not self._tmit_data:
            self._logger.info("You have no tmit data")
            return None

        return np.std(self._tmit_data)
    
    @property
    def status(self):
        """Get the status of the bpm"""
        return self._status.get()

    @property
    def alarm(self):
        """Get the alarm status"""
        return self._alarm.get()

    def acquire_data(self, readings=1, user_clbk=None):
        """Acquire a number of readings, defaults to 1"""
        if not isinstance(readings, int):
            self._logger.info('You did not enter an int for number of readings')
            return

        if self._gathering_data:
            self._logger.info("You are already gathering data")
            return

        if user_clbk:
            self._data_clbk = user_clbk

        self._readings = readings
        self.clear_data()
        self._gathering_data = True

        self._data_thread = Thread(target=self.watcher)
        self._data_thread.start()
            
        self._x.add_callback(self._x_acq_clbk, index=0, with_ctrlvars=False)
        self._y.add_callback(self._y_acq_clbk, index=0, with_ctrlvars=False)
        self._tmit.add_callback(self._tmit_acq_clbk, index=0, with_ctrlvars=False)

    def watcher(self):
        """Watch for all the data to be done"""
        while not len(self._x_data) == len(self._y_data) == \
                len(self._tmit_data) == self._readings:
            time.sleep(0.1)
        if self._data_clbk:
            self._data_clbk()
            self._data_clbk = None
        return

    def _x_acq_clbk(self, pv_name=None, value=None, char_value=None, time_stamp=None, **kw):
        """x data callback"""
        self._x_data.append(value)
        if len(self._x_data) is self._readings:
            self._x.remove_callback(0)

    def _y_acq_clbk(self, pv_name=None, value=None, char_value=None, time_stamp=None, **kw):
        """y data callback"""
        self._y_data.append(value)
        if len(self._y_data) is self._readings:
            self._y.remove_callback(0)

    def _tmit_acq_clbk(self, pv_name=None, value=None, char_value=None, time_stamp=None, **kw):
        """tmit data callback"""
        self._tmit_data.append(value)
        if len(self._tmit_data) is self._readings:
            self._tmit.remove_callback(0)

    def clear_data(self):
        """Clear the x, y, tmit data"""
        self._x_vals = []
        self._y_vals = []
        self._tmit_vals = []
