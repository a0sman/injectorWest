#!/usr/local/lcls/package/python/current/bin/python

import sys
import unittest
import inspect
from .magnet import Magnet, get_magnets
from mock_magnet import MockMagnet

ATTRS = [
    '_bact', 
    '_bcon', 
    '_bctrl', 
    '_bdes', 
    '_ctrl'
]

MAGS = [
    'SOL1B', 
    'SOL2B'
]

class MagnetTest(unittest.TestCase):
    """All these tests rely on EPICS functioning as we expect,
    but we have not testing framework for EPICS code, fun!
    """

    ###### Normal Magnet object ##########

    def test_properties(self):
        """Test that all the properties we expect exist"""
        m = Magnet()
        print(dir(type(m)))
        self.assertEqual(isinstance(type(m).name, property), True)
        self.assertEqual(isinstance(type(m).bctrl, property), True)
        self.assertEqual(isinstance(type(m).bact, property), True)
        self.assertEqual(isinstance(type(m).bdes, property), True)
        self.assertEqual(isinstance(type(m).ctrl_value, property), True)
        self.assertEqual(isinstance(type(m).length, property), True)
        self.assertEqual(isinstance(type(m).pv_props, property), True)
        self.assertEqual(isinstance(type(m).bdes, property), True)
        self.assertEqual(isinstance(type(m).tol, property), True)

    def test_methods(self):
        """Test that all the methods we expect exist"""
        m = Magnet()
        self.assertEqual(inspect.ismethod(m.trim), True)
        self.assertEqual(inspect.ismethod(m.perturb), True)
        self.assertEqual(inspect.ismethod(m.con_to_des), True)
        self.assertEqual(inspect.ismethod(m.save_bdes), True)
        self.assertEqual(inspect.ismethod(m.load_bdes), True)
        self.assertEqual(inspect.ismethod(m.undo_bdes), True)
        self.assertEqual(inspect.ismethod(m.dac_zero), True)
        self.assertEqual(inspect.ismethod(m.calibrate), True)
        self.assertEqual(inspect.ismethod(m.standardize), True)
        self.assertEqual(inspect.ismethod(m.reset), True)
        self.assertEqual(inspect.ismethod(m.find_pv_attrs), True)
        self.assertEqual(inspect.ismethod(m.add_clbk), True)
        self.assertEqual(inspect.ismethod(m.remove_clbk), True)

    def test_name(self):
        """Test we get expected default"""
        m = Magnet()
        self.assertEqual(m.name, 'SOL1B')

    def test_find_pv_attrs(self):
        """Test we have correct attributes"""
        m = Magnet()
        self.assertEqual(m.find_pv_attrs(), ATTRS)

    def test_tol(self):
        """Test tol float validation"""
        m = Magnet()
        self.assertEqual(m.tol, 0.05)
        m.tol = 'a'
        self.assertEqual(m.tol, 0.05)
        m.tol = 1
        self.assertEqual(m.tol, 0.05)
        m.tol = 0.1
        self.assertEqual(m.tol, 0.1)

    def test_length(self):
        """Test length float validation"""
        m = Magnet()
        self.assertEqual(m.length, 0.1)
        m.length = 'a'
        self.assertEqual(m.length, 0.1)
        m.length = 1
        self.assertEqual(m.length, 0.1)
        m.length = 0.05
        self.assertEqual(m.length, 0.05)

    def test_get_mangets(self):
        """Test we have the same magnets as expected"""
        self.assertEqual(get_magnets(), MAGS)

    ####### Mock Magnet Object ########

    def test_mock_name(self):
        """Test we get expected name"""
        m = MockMagnet()
        self.assertEqual(m.name, 'mock')

    def test_mock_tol(self):
        m = MockMagnet()
        self.assertEqual(m.tol, 0.1)

    def test_mock_length(self):
        m = MockMagnet()
        self.assertEqual(m.length, 1.0)

    def test_mock_bact(self):
        m = MockMagnet()
        self.assertEqual(m.bact, 5.0)

    def test_mock_bctrl(self):
        m = MockMagnet()
        self.assertEqual(m.bctrl, 5.0)
        self.assertEqual(m.bdes, 5.0)
        self.assertEqual(m.bdes, 5.0)
        m.bctrl = 'a'
        self.assertEqual(m.bctrl, 5.0)
        m.bctrl = 4.0
        self.assertEqual(m.bctrl, 4.0)
        self.assertEqual(m.bdes, 4.0)
        self.assertEqual(m.bdes, 4.0)

if __name__ == '__main__':
    unittest.main()
