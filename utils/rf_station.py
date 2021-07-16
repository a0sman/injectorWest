#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import rf_station_constants as sc
import numpy as np
from .logger import logger

def get_stations():
    """Return different stations that have models"""
    return sc.STATIONS.keys()

class RFCon(object):
    def __init__(self, station_name='GUN'):
        if station_name not in sc.STATIONS.keys():
            raise ValueError('You have not specified a valid RF Station')
        station_dict = sc.STATIONS[station_name]
        self._station_name = station_name
        self._am_lim = station_dict['a_lim']
        self._station_name = station_name
        self._mode = PV(station_dict['mode'])
        self._interval = PV(station_dict['interval'])
        self._amp_set = PV(station_dict['amp_set'])
        self._amp_get = PV(station_dict['amp_get'], form='time')
        self._phase_set = PV(station_dict['ph_set'])
        self._phase_get = PV(station_dict['ph_get'], form='time')
        self._detune = PV(station_dict['detune'])
        self._diff_nom = PV(station_dict['diff_nom'])
        self._freq_offset = PV(station_dict['freq_offset'])
        self._ssas_status = {name: PV(name) for name in station_dict['ssas_status']}
        self._ssa_status_vars = self._ssas_status.values()[0].get_ctrlvars()['enum_strs']
        self._ssas_on = PV(station_dict['ssas_on'])
        self._ssas_off = PV(station_dict['ssas_off'])
        self._amp_data = []
        self._phase_data = []
        self._readings = 1
        self._gathering_data = False
        self._logger = logger.custom_logger(__name__)

    @property
    def name(self):
        """Get stations generic name"""
        return self._station_name

    @property
    def mode(self):
        """Get detune mode"""
        return self._mode.get()

    @property
    def interval(self):
        """Get repetion period"""
        return self._interval.get()

    @property
    def phase(self):
        """Get current phase"""
        return self._phase_get.get()

    @phase.setter
    def phase(self, val):
        """Set phase"""
        if not isinstance(val, float) or isinstance(val, int):
            self._logger.info('You have not entered an int or float')
            return

        self._phase_set.put(val)
        
    @property
    def amplitude(self):
        """Get current amplitude"""
        return self._amp_get.get()

    @amplitude.setter
    def amplitude(self, val):
        """Set amplitude"""
        if not isinstance(val, float) or isinstance(val, int):
            self._logger.info('You have not entered an int or float')
            return

        if val > self.am_lim:
            self._logger.info('You are tyring to set the amplitude too high at {0}'.format(val))
            return

        if val < 0:
            self._logger.info('You are trying to set a negative amplitude, aborting')
            return

        self._amp_set.put(val)

    @property
    def detune(self):
        """Get detune value"""
        return self._detune.get()

    @property
    def diff_nominal(self):
        """Get diff from nominal"""
        return self._diff_nom.get()

    @property
    def freq_offset(self):
        """Get the frequency offset"""
        return self._freq_offset.get()

    @freq_offset.setter
    def freq_offset(self, val):
        """Set the frequency offset"""
        if not isinstance(val, float) or isinstance(val, int):
            self._logger.info('You have not entered an int or float')
            return

        self._amp_set.put(val)

    @property
    def amplitude_data(self):
        """Get the amplitude data"""
        return self._amp_data

    @property
    def phase_data(self):
        """Get the phase data"""
        return self._phase_data

    @property
    def amp_ave(self):
        """Get mean of amplitude data"""
        if not self._amp_data:
            self._logger.info('You have not gathering any amplitdue data')
            return None

        return np.mean(self._amp_data)

    @property
    def phase_ave(self):
        """Get the mean of the phase data"""
        if not self._phase_data:
            self._logger.info('You have not gathering any phase data')
            return None

        return np.mean(self._phase_data)

    @property
    def amp_std(self):
        """Get the std dev of the amplitude data"""
        if not self._amp_data:
            self._logger.info('You have not gathering any amplitdue data')
            return None

        return np.std(self._amp_data)

    @property
    def phase_std(self):
        """Get the std dev of the phase data"""
        if not self._phase_data:
            self._logger.info('You have not gathering any phase data')
            return None

        return np.std(self._phase_data)

    @property
    def ssas_status(self):
        """Get status of all SSAs for this rf station"""
        return [self._ssa_status_vars[ssa.get()] for ssa in self._ssas_status.values()]

    def turn_off_ssas(self):
        """Turn off all SSAs"""
        self._ssas_off.put(sc.OFF)

    def turn_on_ssas(self):
        """Turn on all SSAs"""
        self._ssas_on.put(sc.ON) 

    def acq_data(self, readings=1, clbk_fn=None):
        """Acquire a specified number of points to collect"""
        if not isinstance(readings, int):
            self._logger.info('You need to enter an int for number of readings')
            return
        
        if self._gathering_data:
            self._logger.info('You are currently gathering data')
            return

        self._readings = readings
        self._amp_data = []
        self._phase_data = []
        self._gathering_data = True
        self._amp_get.add_callback(self._amp_acq_clbk, index=0, with_ctrlvars=False)
        self._phase_get.add_callback(self._phase_acq_clbk, index=0, with_ctrlvars=False)
       
    def _amp_acq_clbk(self, pv_name=None, value=None, char_value=None, timestamp=None, **kw):
        """Amplitude callback"""
        self._amp_data.append(value)
        if len(self._amp_data) is self._readings:
            self._logger.info("finished gathering amplitude data")
            self._amp_get.remove_callback(index=0)
            self._check_data_acquire()

    def _phase_acq_clbk(self, pv_name=None, value=None, char_value=None, timestamp=None, **kw):
        self._phase_data.append(value)
        if len(self._phase_data) is self._readings:
            self._logger.info("finished gathering phase data")
            self._phase_get.remove_callback(index=0)
            self._check_data_acquire()
       
    def _check_data_acquire(self):
        if len(self._amp_data) == len(self._phase_data) == self._readings:
            self._logger.info('All the data has been acquired')
            self._gathering_data = False
   
