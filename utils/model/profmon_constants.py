#!/usr/local/lcls/package/python/current/bin/python

# There are likely redundancy issues and can be
# optimized further, this is just a POC.  A Database would be nice
# to reference as this is Database schema

# TODO: Make this a .yaml file for cleanliness and
# cross language reference if needed

# Error Strings
ALREADY_INSERTED = 'Profile Monitor is already inserted'
ALREADY_EXTRACTED = 'Profile Monitor is already extracted'

# Completed Action Strings
INSERTED = 'Profile Monitor has been inserted'
EXTRACTED = 'Profile Monitor has been extracted'

# Profile Monitor State
IN = 'IN'
OUT = 'OUT'

# Lamp Secondaries
HI = 'upper_ctrl_limit'
LO = 'lower_ctrl_limit'
LAMP_STEP = 0.1

# LCLS 1 Lamp enable/disable
ENABLE = 'Enable'
DISABLE = 'Disable'

# LCLS 2 Lamp On/Off
ON = 'On'
OFF = 'Off'

############# LCLS Lamp #################

def create_lamp_dict(base, style, name):
    lamp_dict = {
        'channel': base + ':LAMP_CH',
        'g_enable': base + ':G_LAMP_ENA',
        'g_dim': base + ':G_LAMP_DOWN',
        'g_bright': base + ':G_LAMP_UP',
        't_enable': base + ':T_LAMP_ENA',
        't_dim': base + ':T_LAMP_DOWN',
        't_bright': base + ':T_LAMP_UP',
        'style': style,
        'name': name
        }

    return lamp_dict

GP01 = create_lamp_dict('PFMC:IN20:GP01', 'lcls', 'GP01')
GP03 = create_lamp_dict('PFMC:IN20:GP03', 'lcls', 'GP03')

############# LCLS Profile Monitor ###########

def create_profmon_dict(base, lamp):
    profmon_dict = {
        'set': base + ':PNEUMATIC',
        'get': base + ':TGT_STS',
        'image': base + ':IMAGE',
        'res': base + ':RESOLUTION',
        'xsize': base + ':N_OF_COL',
        'ysize': base + ':N_OF_ROW',
        'rate': base + ':FRAME_RATE'
        }
    
    return profmon_dict

YAG01 = create_profmon_dict('YAGS:IN20:211', GP01)
OTR02 = create_profmon_dict('OTRS:IN20:571', GP03)

########### LCLS 2 Lamps ##############

# Has no MAD name yet? The convention (or lack of it) here is bizarre
YAG01B_LAMP = {
    'lamp_power': 'YAGS:GUNB:753:TGT_LAMP_PWR',
    'lamp_brightness': 'SIOC:GUNB:PM02:TGT_LAMP_CTRL',
    'on': 'On',
    'off': 'Off',
    'style': 'lcls2',
    'name': 'YAG01B_LAMP'
}

######### LCLS 2 Profile Monitors ######

def create_profmon2_dict(base, lamp):
    profmon_dict = {
        'set': base + ':PNEUMATIC',
        'get': base + ':TGT_STS',
        'image': base + ':Image:ArrayData',
        'res': base + ':RESOLUTION',
        'xsize': base + ':ArraySizeX_RBV',
        'ysize': base + ':ArraySizeY_RBV',
        'rate': base + ':FRAME_RATE',
        'lamp': YAG01B_LAMP
        }

    return profmon_dict

YAG01B = create_profmon2_dict('YAGS:GUNB:753', YAG01B_LAMP)

# Dict of Profile Monitors
PROFS = {
    'YAG01B': YAG01B,
    'YAG01': YAG01,
    'OTR02': OTR02
}
