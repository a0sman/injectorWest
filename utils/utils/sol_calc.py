import scipy.constants as sc
import numpy as np
from numpy.linalg import pinv
from math import sin, cos, sqrt


# L - magnetic length of solenoid
# Bo - magnetic filed strength in solenoid
# Bp = Beta*gamma*m*c (beam momentum)
# gamma = 1 + (Egun / Eo)
# beta = sqrt(1 + (1/gamma)^2)
# d - distance from sol exit and bpm
# c = cos(KL)
# s = sin(KL)
# K = Bo / (2Bp)

# Convert kG to Tesla Bt = BkG / 10

# General scheme: Generate x and y rows for each solenoid setting,
# This is a one off class.  For each scan instantiate a new SolCorrection object
# This was done for simplicity, but we can think about reusing or data manipulation
# if that becomes a need.

class SolCorrection(object):
    def __init__(self, sol, e_gun, d):
        self.sol = sol
        self._L = float(self.sol.length)  # Leff
        self._e_gun = float(e_gun)  # MeV
        self._d = d  # distance from sol exit and bpm
        self._b = None
        self._p = None
        self._K = None
        self._c = None
        self._s = None
        self._x_arrays = None
        self._y_arrays = None
        self._results = None
        self._x_vals = []
        self._x_stds = []
        self._y_stds = []
        self._y_vals = []
        self._b_vals = []

    @property
    def x_vals(self):
        return self._x_vals

    @property
    def y_vals(self):
        return self._y_vals

    @property
    def x_stds(self):
        return self._x_stds

    @property
    def y_stds(self):
        return self._y_stds

    @property
    def b_vals(self):
        return self._b_vals

    def calc_b(self):
        """Convert kG to Tesla"""
        return self.sol.bact / 10.0

    def calc_p(self):
        """momentum calculation"""
        gamma = 1.0 + (self._e_gun / 0.511)
        beta = sqrt(1.0 - (1 / gamma) ** 2)
        return beta * gamma * sc.m_e * sc.c

    def calc_K(self, b, p):
        """Get the current K value"""
        return (b * sc.e) / (2 * p)

    def calc_c(self):
        """c term"""
        return cos(self._K * self._L)

    def calc_s(self):
        """s term"""
        return sin(self._K * self._L)

    def x11(self):
        """first term, x"""
        return self._c ** 2 - self._d * self._K * self._s * self._c

    def x12(self):
        """second term, x"""
        return self._s * self._c * (1 / self._K) + self._d * self._c ** 2

    def x13(self):
        """third term, x"""
        return self._s * self._c - self._d * self._K * self._s ** 2

    def x14(self):
        """fourth term, x"""
        return self._s ** 2 * (1 / self._K) + self._d * self._s * self._c

    def x15(self):
        """Default"""
        return 1

    def x16(self):
        """Default"""
        return 0

    def y11(self):
        """first term y"""
        return -self._s * self._c + self._d * self._K * self._s ** 2

    def y12(self):
        """second term y"""
        return -self._s ** 2 * (1 / self._K) - self._d * self._s * self._c

    def y13(self):
        """third term y"""
        return self._c ** 2 - self._d * self._K * self._s * self._c

    def y14(self):
        """fourth term y"""
        return self._s * self._c * (1 / self._K) + self._d * self._c ** 2

    def y15(self):
        """Default"""
        return 0

    def y16(self):
        """Default"""
        return 1

    def calc_props(self):
        """Update all the properties"""
        b = self.calc_b()
        self._b_vals.append(b)
        p = self.calc_p()
        self._K = self.calc_K(b, p)
        self._c = self.calc_c()
        self._s = self.calc_s()

    def add_data(self, x_val, y_val, x_std, y_std):
        """Add the data from a new scan, calculate new rows for x and y"""
        self.calc_props()
        self._x_vals.append(x_val)
        self._y_vals.append(y_val)
        self._x_stds.append(x_std)
        self._y_stds.append(y_std)

        if self._x_arrays is not None:
            self._x_arrays = np.vstack((self._x_arrays, self.gen_x_arr()))
        else:
            self._x_arrays = self.gen_x_arr()

        if self._y_arrays is not None:
            self._y_arrays = np.vstack((self._y_arrays, self.gen_y_arr()))
        else:
            self._y_arrays = self.gen_y_arr()

        print('x arrays ', self._x_arrays)
        print('y arrays ', self._y_arrays)

    def gen_x_arr(self):
        """The x array froma single measurement"""
        arr = np.array([
            self.x11(),
            self.x12(),
            self.x13(),
            self.x14(),
            self.x15(),
            self.x16()])

        return arr

    def gen_y_arr(self):
        """The y array from single measurement"""
        arr = np.array([
            self.y11(),
            self.y12(),
            self.y13(),
            self.y14(),
            self.y15(),
            self.y16()])

        return arr

    def calc_offsets(self):
        """Solve the problem"""
        r = np.array(self._x_vals + self._y_vals)
        print('here is r ', r)
        print('here is array ', np.vstack((self._x_arrays, self._y_arrays)))
        pseudo_inv = pinv(np.vstack((self._x_arrays, self._y_arrays)))
        print('here is result ', pseudo_inv.dot(r))
        return pseudo_inv.dot(r)
