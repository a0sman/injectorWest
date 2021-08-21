#!/usr/local/lcls/package/python/current/bin/python

from PyQt5.QtCore import QThread
SETTLE = int(1e5)

class MagnetSet(QThread):
    def __init__(self, sol, bval, parent=None):
        super(MagnetSet, self).__init__(parent)
        self.sol = sol
        self.bval = bval

    def run(self):
        """Wait until we're in tol, then start get bpm thread"""
        self.sol.bctrl = self.bval
        QThread.usleep(int(5e6))
        while abs(self.bval-self.sol.bact) > self.sol.tol:
            QThread.usleep(SETTLE)
