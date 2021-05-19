#!/usr/local/lcls/package/python/current/bin/python

class MockMagnet(object):
    """Useful for unit tests of applications"""
    def __init__(self, name='mock'):
        self._name = name
        self._bctrl = 5.0
        self._bact = 5.0
        self._bdes = 5.0
        self._bcon = 3.0
        self._length = 1.0
        self._tol = 0.1

    @property
    def tol(self):
        return self._tol

    @property
    def length(self):
        return self._length

    @property
    def name(self):
        return self._name

    @property
    def bact(self):
        return self._bact

    @property
    def bctrl(self):
        return self._bctrl

    @bctrl.setter
    def bctrl(self, b_val):
        if not isinstance(b_val, float):
            return
        
        self._bctrl = b_val
        self._bdes = b_val
        self._bact = b_val

    @property
    def bdes(self):
        return self._bdes

    @bdes.setter
    def bdes(self, b_val):
        self._bdes = b_val

    def add_clbk(self, clbk):
        pass

    def remove_clbk(self, clbk):
        pass


        
        
