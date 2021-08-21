#!/usr/local/lcls/package/python/current/bin/python

from PyQt5.QtCore import QThread, pyqtSignal
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
        self.bpm.acquire_data(self.readings);
        while self.bpm.gathering_data:
            QThread.usleep(SETTLE)
        print(self.bpm.current_data)
        self.signal.emit(self.bpm.x_ave, self.bpm.y_ave, self.bpm.x_std, self.bpm.y_std)
