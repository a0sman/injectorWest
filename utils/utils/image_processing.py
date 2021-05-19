#!/usr/local/lcls/package/python/current/bin/python

import scipy.io as sio
from scipy.stats import norm
import numpy as np
from functools import partial
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import mlab
from matplotlib.patches import Ellipse
import scipy.ndimage as snd
from scipy.stats import norm
from scipy import optimize
import math

# data '/u1/lcls/matlab/data/2019/2019-01/2019-01-25/ProfMon-CAMR_LGUN_210-2019-01-25-165017.mat'

class ImageProcessing(object):
    def __init__(self):
        self.images = []
        self.file = None
        self.file_data = None

    def load_file(self, f):
        try:
            self.file = f
            self.file_data = sio.loadmat(f)
        except Exception as err:
            print('Unable to load file: {0}'.format(err))

    def image_array_from_file(self):
        if self.file_data:
            return np.array(self.file_data['data'][0][0][1])
            
    def fliplr(self, data):
        return np.fliplr(data)

    def flipud(self, data):
        return np.flipud(data)

    def plot_image_from_file(self, plot_mm=False):
        if self.file_data:
            image = self.image_array_from_file()
            if plot_mm:
                resolution = self.resolution_from_file()
                tick_set = self.generate_ticks(image, resolution)
                plt.xticks(tick_set[2], tick_set[0])
                plt.yticks(tick_set[3], tick_set[1])
                plt.xlabel('x (mm)')
                plt.ylabel('y (mm)')
            else:
                plt.xlabel('x (pixel)')
                plt.ylabel('y (pixel)')
            plt.imshow(image)
            plt.show()
        else:
            print('You have not loaded any file data')
    
    def resolution_from_file(self):
        if self.file_data:
            return self.file_data['data'][0][0][9]

    def generate_ticks(self, image, resolution):
        ticks_max_x = math.ceil(round(image.shape[2]*(resolution / 1000) / 2) / 2)*2
        ticks_max_y = math.floor(round(image.shape[1]*(resolution / 1000) / 2) / 2)*2
        ticks_mm_x = np.arange(-ticks_max_x, ticks_max_x + 0.5, 0.5)
        ticks_mm_y = np.arange(-ticks_max_y, ticks_max_y + 0.5, 0.5)           
        ticks_px_x = [i / (resolution / 1E3) + image.shape[2] / 2 for i in ticks_mm_x]
        ticks_px_y = [j / (resolution / 1E3) + image.shape[1] / 2 for j in ticks_mm_y]
        return (ticks_mm_x, ticks_mm_y, ticks_px_x, ticks_px_y)
