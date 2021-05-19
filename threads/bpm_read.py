#!/usr/local/lcls/package/python/current/bin/python

from PyQt4.QtCore import QThread, pyqtSignal
import numpy as np

SETTLE = int(1e5)
DEBUG = True
TEST_X = [0.0, 0.0, 0.0]#np.linspace(0.001, -0.001, 3).tolist()
TEST_Y = np.linspace(-0.001, 0.001, 3).tolist()

class BPMRead(QThread):
    # Signal emits ave(x), ave(y), std(x), std(y)
    signal = pyqtSignal(float, float, float, float)
    def __init__(self, bpm, readings, parent=None):
        super(BPMRead, self).__init__(parent)
        self.bpm = bpm
        self.readings = readings

    def run(self):
        """Collect bpm data, should work in rate logic"""
        x = []
        y = []
        i = 0
        test_x = TEST_X.pop(0)
        test_y = TEST_Y.pop(0)
        while i < self.readings:
            if DEBUG:
                x.append(test_x)
                y.append(test_y)
            else:
                x.append(self.bpm.x)
                y.append(self.bpm.y)
            i+=1
            QThread.usleep(SETTLE)
        self.signal.emit(np.mean(x), np.mean(y), 1.0, 1.0)
