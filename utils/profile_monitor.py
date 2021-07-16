#!/usr/local/lcls/package/python/current/bin/python

from epics import PV
from .model import profmon_constants as pc
from inspect import getmembers
from time import sleep
from threading import Thread
from numpy import array_equal
from .logger import logger
from functools import partial

# data '/u1/lcls/matlab/data/2019/2019-01/2019-01-25/ProfMon-CAMR_LGUN_210-2019-01-25-165017.mat'

def get_prof_mons():
    """Return MAD names of all profile monitors that have models"""
    return pc.PROFS.keys()

class LampCon(object):
    """Lamp Control for lcls"""
    def __init__(self, lamp_dict):  # I hate using dicts as default data structures, but...
        self._channel = PV(lamp_dict['channel'])
        self._t_enable = PV(lamp_dict['t_enable'])
        self._t_dim = PV(lamp_dict['t_dim'])
        self._t_bright = PV(lamp_dict['t_bright'])
        self._g_enable = PV(lamp_dict['g_enable'])
        self._g_dim = PV(lamp_dict['g_dim'])
        self._g_bright = PV(lamp_dict['g_bright'])
        self._lamp_name = lamp_dict['name']
        self._channel_vars = self._channel.get_ctrlvars()['enum_strs']
        self._g_lamp_vars = self._g_enable.get_ctrlvars()['enum_strs']
        self._t_lamp_vars = self._t_enable.get_ctrlvars()['enum_strs']
        self._logger = logger.custom_logger(__name__)
        
    @property
    def lamp_name(self):
        """Get generic lamp name"""
        return self._lamp_name

    @property
    def channel(self):
        """Get current lamp channel (profile monitor)"""
        return self._channel_vars[self._channel.get()]
    
    @channel.setter
    def channel(self, val):
        """Set lamp channel"""
        if val not in self._channel_vars:
            self._logger.info('Profile Monitor {0}, not available channel for lamp {1}' \
                  .format(val, self._lamp_name))
            return

        self._logger.info('Setting lamp {0} channel to {1}'.format(self._lamp_name, val))
        self._channel.put(val)

    @property
    def channels(self):
        """Get list of available channels"""
        return self._channel_vars 

    @property
    def t_lamp_enable(self):
        """Get t lamp enable status"""
        return self._t_lamp_vars[self._t_enable.get()]

    @t_lamp_enable.setter
    def t_lamp_enable(self, val):
        """Set the T Lamp to enabled/disabled"""
        state = self._t_lamp_vars[self._t_enable.get()]
        
        if state == val == pc.ENABLE:
            self._logger.info('{0}: T Lamp Already Enabled'.format(self._lamp_name))
            return

        if state == val == pc.DISABLE:
            self._logger.info('{0}: T Lamp Already Disabled'.format(self._lamp_name))
            return 

        self._t_enable.put(val)
        self._logger.info('T Lamp now {0}'.format(val)) 

    @property
    def g_lamp_enable(self):
        """Get g lamp enabled status"""
        return self._g_lamp_vars[self._g_enable.get()]

    @g_lamp_enable.setter
    def g_lamp_enable(self, val):
        """Set the G Lamp to enabled/disabled"""
        state = self._g_lamp_vars[self._g_enable.get()]

        if state == val == pc.ENABLE:
            self._logger.info('{0}: G Lamp Already Enabled'.format(self._lamp_name))
            return

        if state == val == pc.DISABLE:
            self._logger.info('{0}: G Lamp Already Disabled'.format(self._lamp_name))
            return 

        self._g_enable.put(val)
        self._logger.info('G Lamp now {0}'.format(val))

class LampCon2(object):
    """Lamp Control for lcls2 lamp"""
    def __init__(self, lamp_dict):
        self._lamp_power = PV(lamp_dict['lamp_power'])
        self._power_vars = self._lamp_power.get_ctrlvars()['enum_strs']
        self._bright_pv = PV(lamp_dict['lamp_brightness'])
        self._bright_vars = self._bright_pv.get_ctrlvars()
        self._bright_upper = self._bright_vars[pc.HI]
        self._bright_lower = self._bright_vars[pc.LO]
        self._lamp_name = lamp_dict['name']
        self._logger = logger.custom_logger(__name__)
    
    @property
    def lamp_name(self):
        """Generic name for lamp"""
        return self._lamp_name

    @property
    def brightness(self):
        """Get the current setting for the brightness"""
        return self._bright_pv.get()

    @brightness.setter
    def brightness(self, val):
        if not self._bright_lower < val < self._bright_upper:
            self._logger.info('{0} is not in range'.format(val))
            return
            
        self._bright_pv.put(val)

    @property
    def bright_up_lim(self):
        """Get the upper limit for the brightness"""
        return self._bright_upper

    @property
    def bright_lo_lim(self):
        """Get the lower limit for the brightness"""
        return self._bright_lower

    @property
    def lamp_power(self):
        """Get the on/off state for the lamp"""
        return self._power_vars[self._lamp_power.get()]

    @lamp_power.setter
    def lamp_power(self, val):
        """Power On/Off setter.  Val must be 'On' or 'Off'"""
        if val not in self._power_vars:
            self._logger.info('You must provide a value that is "On" or "Off"')
            return

        state = self._power_vars[self._lamp_power.get()]

        if val == state == pc.ON:
            self._logger.info("The lamp is already on")
            return

        if val == state == pc.OFF:
            self._logger.info("The lamp is already off")
            return
        
        self._logger.info('Turning lamp {0}'.format(val))
        self._lamp_power.put(val)

    @property
    def state(self):
        """Get the current state of the object class"""
        return self.__dict__

    def dim_lamp(self, step=pc.LAMP_STEP, callback_fn=None):
        """Dim lamp by a step"""
        new_val = self._bright_pv.get() - step

        if new_val < self._bright_lower:
            self._logger.info('You can not dim any further')
            return

        self._bright_pv.put(new_val)
        
    def brighten_lamp(self, step=pc.LAMP_STEP, callback=None):
        """Brighten the lamp"""
        new_val = self._bright_pv.get() + step

        if new_val > self._bright_upper:
            self._logger.info('You can not brighten any further')
            return
        
        self._bright_pv.put(new_val)
        
class ProfCon(LampCon, LampCon2):
    """Generic Profile Monitor Object Class that references profile monitor MAD name"""
    def __init__(self, prof_name='OTR02'):
        if prof_name not in pc.PROFS.keys():
            raise ValueError('You have not specified a valid profile monitor')
        prof_dict = pc.PROFS[prof_name]
        lamp_dict = prof_dict['lamp']  # That's right no error checking, don't break schema!
        if lamp_dict['style'] == 'lcls':
            LampCon.__init__(self, lamp_dict)
        else:
            LampCon2.__init__(self, lamp_dict)
        self._prof_name = prof_name
        self._prof_set = PV(prof_dict['set'])
        self._prof_get = PV(prof_dict['get'])
        self._prof_image = PV(prof_dict['image'])
        self._prof_res = PV(prof_dict['res'])
        self._x_size = PV(prof_dict['xsize'])
        self._y_size = PV(prof_dict['ysize'])
        self._rate = PV(prof_dict['rate'])
        self._images = []
        self._data_thread = None
        self._gathering_data = False
        self._get_vars = self._prof_get.get_ctrlvars()['enum_strs']
        self._set_vars = self._prof_set.get_ctrlvars()['enum_strs']
        self._motion_state = self._get_vars[self._prof_get.get()]
        self._prof_get.add_callback(self._state_clbk, index=1)
        self._insert_clbk = None
        self._extract_clbk = None
        self._logger = logger.custom_logger(__name__)

    def _state_clbk(self, pvName=None, value=None, char_value=None, **kw):
        """Keep track of position/motion state"""
        self._motion_state = self._get_vars[value]

    @property
    def prof_name(self):
        """Get the profile monitor MAD name"""
        return self._prof_name
        
    @property
    def cur_image(self):
        """Get the current image array"""
        return self._prof_image.get()

    @property
    def saved_images(self):
        """Get the images collected"""
        return self._images

    @property
    def resolution(self):
        """Get the resolution"""
        return self._prof_res.get()

    @property
    def arr_dims(self):
        """Get the x and y dimensions"""
        return (self._x_size.get(), self._y_size.get())

    @property
    def rate(self):
        """Get the current rate"""
        return self._rate.get()

    @property
    def motion_state(self):
        """Get the current motion state of the profile monitor"""
        return self._motion_state

    @property
    def state(self):
        """Get the overall state of the profile monitor"""
        return self.__dict__

    def insert(self, user_clbk=None):
        """Generic call to insert profile monitor, can specify callback to be run"""
        if self._motion_state == pc.IN:
            self._logger.info('{0}: {1}'.format(self._prof_name, pc.ALREADY_INSERTED))
            return

        if user_clbk:
            self._insert_clbk = user_clbk
        
        self._prof_get.add_callback(self._inserted, index=0)
        self._prof_set.put(pc.IN)

    def _inserted(self, pv_name=None, value=None, char_value=None, **kw):
        """Generic callback after profile monitor has been inserted, default"""
        if self._get_vars[value] == pc.IN:
            self._logger.info('{0}: {1}'.format(self._prof_name, pc.INSERTED))

            if self._insert_clbk:
                self._insert_clbk()
                self._insert_clbk = None

            self._prof_get.remove_callback(index=0)
    
    def extract(self, usr_clbk=None):
        """Extract profile monitor command, can specify callback to be run"""        
        if self._motion_state == pc.OUT:
            self._logger.info('{0}: {1}'.format(self._prof_name, pc.ALREADY_EXTRACTED))
            return

        if user_clbk:
            self._extract_clbk = user_clbk

        self._prof_get.add_callback(self._extracted, index=0)
        self._prof_set.put(pc.OUT)
        
    def _extracted(self, pv_name=None, value=None, char_value=None, **kw):
        """Generic Callback for profile monitor that has been extracted, default"""
        if self._get_vars[value] == pc.OUT:
            self._logger.info('{0}: {1}'.format(self._prof_name, pc.EXTRACTED))

            if self._extract_clbk:
                self._extract_clbk()
                self._extract_clbk = None

            self._prof_get.remove_callback(index=0)

    def acquire_images(self, images=1):
        """Start the thread"""
        self._data_thread = Thread(target=self._collect_image_data, args=(images,))
        self._data_thread.start()

    def _collect_image_data(self, images, callback):
        """Threaded data collection"""
        self._gathering_data = True
        delay = 1.0 / self._rate.get()  # Rate must be in Hz
        i = 0
        while i < images:
            image = self._prof_image.get()
            if len(self._images) > 0 and array_equal(image, self._images[-1]):
                sleep(0.01)
            else:
                self._images.append(image)
                sleep(delay)
                i += 1
        self._logger.info("we have gathered all images ")
        self._gathering_data = False
        return  # No join, waste of a function
