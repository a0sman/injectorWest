import sys
import unittest
import bpm_constants as bc
import magnet_constants as mc
import profmon_constants as pc
import rf_station_constants as rsc

##### Expected Results #######

BPM = {
    'alarm': 'test:STA_ALH',
    'status': 'test:STA',
    'x': 'test:X_SLOW',
    'y': 'test:Y_SLOW',
    'tmit': 'test:TMIT_SLOW',
    'z': 'test:Z'
}

BPM_KEYS = [
    'BPM1B',
    'BPM2B'
]

MAGNET = {
    'bctrl': 'test:BCTRL',
    'bact': 'test:BACT',
    'bdes': 'test:BDES',
    'bcon': 'test:BCON',
    'ctrl': 'test:CTRL',
    'tol': 0.1,
    'length': 0.1
}

MAGNET_KEYS = [
    'SOL1B',
    'SOL2B'
]

LAMP = {
    'channel': 'test:LAMP_CH',
    'g_enable': 'test:G_LAMP_ENA',
    'g_dim': 'test:G_LAMP_DOWN',
    'g_bright': 'test:G_LAMP_UP',
    't_enable': 'test:T_LAMP_ENA',
    't_dim': 'test:T_LAMP_DOWN',
    't_bright': 'test:T_LAMP_UP',
    'style': 'lcls',
    'name': 'test_name'
}

PROF = {
    'set': 'test:PNEUMATIC',
    'get': 'test:TGT_STS',
    'image': 'test:IMAGE',
    'res': 'test:RESOLUTION',
    'xsize': 'test:N_OF_COL',
    'ysize': 'test:N_OF_ROW',
    'rate': 'test:FRAME_RATE',
    'lamp': LAMP
}

YAG01B_LAMP = {
    'lamp_power': 'YAGS:GUNB:753:TGT_LAMP_PWR',
    'lamp_brightness': 'SIOC:GUNB:PM02:TGT_LAMP_CTRL',
    'on': 'On',
    'off': 'Off',
    'style': 'lcls2',
    'name': 'YAG01B_LAMP'
}

PROF2 = {
    'set': 'test:PNEUMATIC',
    'get': 'test:TGT_STS',
    'image': 'test:Image:ArrayData',
    'res': 'test:RESOLUTION',
    'xsize': 'test:ArraySizeX_RBV',
    'ysize': 'test:ArraySizeY_RBV',
    'rate': 'test:FRAME_RATE',
    'lamp': YAG01B_LAMP
}

STATION = {
    'mode': 'test:DETUNE_MODE',
    'interval': 'test:REP_PERIOD',
    'amp_set': 'test:AOPEN',
    'amp_get': 'test:AACT',
    'ph_set': 'test:POPEN',
    'ph_get': 'test:PACT',
    'a_lim': 1000,
    'detune': 'test:DFACT',
    'diff_nom': 'test:FREQ_OFFSET',
    'freq_offset': 'test:DELTA_FREQDES'
}

STATIONS = [
    'BUNCHER',
    'GUN'
]

class ConstantsTest(unittest.TestCase):
    """Way to make sure changes to constants structure does not break things"""

    ######## BPM Tests ########

    def test_create_bpm_dict(self):
        self.assertEqual(bc.create_bpm_dict('test'), BPM)

    def test_BPMS(self):
        self.assertEqual(sorted(bc.BPMS.keys()), BPM_KEYS)

    ######## Magnet Tests ########

    def test_create_mag_dict(self):
        self.assertEqual(mc.create_mag_dict('test', 0.1, 0.1), MAGNET)

    def test_Magnets(self):
        self.assertEqual(sorted(mc.MAGNETS.keys()), MAGNET_KEYS)

    ######## Profmon Tests #########

    def test_create_lamp_dict(self):
        self.assertEqual(pc.create_lamp_dict('test', 'lcls', 'test_name'), LAMP)

    def test_create_profmon_dict(self):
        self.assertEqual(pc.create_profmon_dict('test', LAMP), PROF)

    def test_yag01b_lamp(self):
        self.assertEqual(pc.YAG01B_LAMP, YAG01B_LAMP)

    def test_create_profmon2_dict(self):
        self.assertEqual(pc.create_profmon2_dict('test', YAG01B_LAMP), PROF2)

    ###### RF Station ########

    def test_create_station_dict(self):
        self.assertEqual(rsc.create_station_dict('test', 1000), STATION)
        
    def test_rf_stations(self):
        self.assertEqual(sorted(rsc.STATIONS.keys()), STATIONS)
                         
    ######## Stopper ########


if __name__ == '__main__':
    unittest.main()
