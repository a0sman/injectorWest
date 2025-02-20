from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from pydm import Display
import sys
import os
import numpy as np
from threads import BPMRead, MagnetSet
import constants
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from time import sleep

sys.path.append('..')
from utils import BPM, Magnet
from utils import MockMagnet
from utils.utils import SolCorrection
from utils import logger


# TODO: Use enum module when available to keep scan state for clean living


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class SolAlign(Display):

    def __init__(self, parent=None, args=None, ui_filename="solenoidAlignment.ui"):
        super(SolAlign, self).__init__(parent=parent, args=args,
                                       ui_filename=ui_filename)
        self.connect_signals()
        self._debug = False
        self.bpm = BPM()
        self.solenoid = self.get_sol()
        self.set_initial_ui()
        self.sol_cor = None
        self.b_thread = None
        self.bpm_thread = None
        self.sol_vals = None
        self.abort = False
        self.results = None
        self.logger = logger.custom_logger(__name__)

        self.plotCanvas = MplCanvas()
        self.ui.plotLayout.addWidget(self.plotCanvas)
        self.setup_plot()
        # print(os.getcwd())

    ############ Setup Methods ############

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, debug):
        if not isinstance(debug, bool):
            self.log_msg('debug must be a boolean value')
            return

        self._debug = debug

    def connect_signals(self):
        """Connect the UI elements to their functions"""
        self.ui.sol_combo.activated.connect(self.sol_select)
        self.ui.meas_num_combo.activated.connect(self.meas_num_select)
        self.ui.start_button.pressed.connect(self.toggle_scan)
        self.ui.sol_upper.editingFinished.connect(self.upper_changed)
        self.ui.sol_upper.setValidator(QDoubleValidator())
        self.ui.sol_lower.editingFinished.connect(self.lower_changed)
        self.ui.sol_lower.setValidator(QDoubleValidator())
        self.ui.percent_sb.valueChanged.connect(self.set_sol_hi_low)
        self.ui.percent_sb.lineEdit().setValidator(QIntValidator(0, 99))
        self.ui.bpm_readings.setValidator(QIntValidator(1, 120))
        self.ui.percent_sb.lineEdit().editingFinished.connect(self.set_sol_hi_low)
        self.ui.apply_cor.pressed.connect(self.apply_correction)

    def set_initial_ui(self):
        """Set the ui after setting the solenoid"""
        # self.setWindowTitle(constants.WIN_TITLE)
        self.ui.statusbar.setText(constants.INIT_MSG)
        self.ui.bpm_label.setText(self.bpm.name)
        self.solenoid.add_clbk(self.bact_clbk)
        #self.set_sol_hi_low()
        self.set_binit(self.solenoid.bctrl)
        self.set_bact(self.solenoid.bact)
        self.ui.bpm_label.setText(self.bpm.name)
        # self.ui.statusbar.setStyleSheet('color: white')
        self.ui.apply_cor.setEnabled(False)

    def setup_plot(self):
        """Initial plot setup"""
        self.plotCanvas.axes.cla()
        self.plotCanvas.axes.set_title(constants.PLOT_TITLE)
        self.plotCanvas.axes.set_xlabel(constants.X_TEXT)
        self.plotCanvas.axes.set_ylabel(constants.Y_TEXT)

    ################ UI Methods ################

    def set_scanning_ui(self):
        """Convenience method to set the ui while we're scanning"""
        self.ui.start_button.setStyleSheet(constants.ABORT_BTN_CLR)
        self.ui.start_button.setText(constants.ABORT)
        self.set_binit(self.solenoid.bctrl)
        self.ui.sol_combo.setEnabled(False)
        self.ui.percent_sb.setEnabled(False)
        self.ui.sol_upper.setReadOnly(True)
        self.ui.sol_lower.setReadOnly(True)
        self.ui.meas_num_combo.setEnabled(False)
        self.ui.bpm_readings.setEnabled(False)
        self.ui.apply_cor.setEnabled(False)
        self.setup_plot()    

    def set_idle_ui(self):
        """Conveninece method to set the ui to be ready to start a scan"""
        self.ui.start_button.setStyleSheet(constants.START_BTN_CLR)
        self.ui.start_button.setText(constants.START)
        self.ui.sol_combo.setEnabled(True)
        self.ui.percent_sb.setEnabled(True)
        self.ui.sol_upper.setReadOnly(False)
        self.ui.sol_lower.setReadOnly(False)
        self.ui.meas_num_combo.setEnabled(True)
        self.ui.bpm_readings.setEnabled(True)
        #self.ui.apply_cor.setEnabled(True)

    ############### UI Helper Methods ##############

    def get_sol(self):
        """Get the solenoid based on debug"""
        name = np.unicode(self.ui.sol_combo.currentText())

        solenoid = Magnet(name=name) if not self._debug else MockMagnet(name=name)

        return solenoid

    def sol_select(self):
        """Solenoid selection combo box action"""
        cur_name = np.unicode(self.ui.sol_combo.currentText())

        if cur_name == self.solenoid.name:
            self.log_msg(constants.SELECTED.format(cur_name))
            return

        self.solenoid.remove_clbk(self.bact_clbk)
        self.solenoid = self.get_sol()
        self.solenoid.add_clbk(self.bact_clbk)
        self.set_initial_ui()
        self.bpm = BPM(constants.SOL_BPM[cur_name])
        self.ui.bpm_label.setText(self.bpm.name)
        self.log_msg(constants.NEW_SELECTED.format(cur_name))
        self.set_sol_hi_low()

    def upper_changed(self):
        """Log upper limit change for scan"""
        upper = float(self.ui.sol_upper.text())
        self.log_msg(constants.UPPER_SCAN.format(upper))

    def lower_changed(self):
        """Log lower limit change for scan"""
        lower = float(self.ui.sol_lower.text())
        self.log_msg(constants.LOWER_SCAN.format(lower))

    def meas_num_select(self):
        """Log number of measurements change for scan"""
        meas_num = int(self.ui.meas_num_combo.currentText())
        self.log_msg(constants.MEAS_NUM.format(meas_num))

    def set_sol_hi_low(self):
        """Get the upper and lower limits based on percent in spin box"""
        tol = self.solenoid.tol
        percent = self.ui.percent_sb.value() * 1.e-2
        upper = (percent) * tol if tol else None
        lower = (-percent) * tol if tol else None
        self.ui.sol_upper.setText('{:.3g}'.format(upper) if upper else None)
        self.ui.sol_lower.setText('{:.3g}'.format(lower) if lower else None)

    def bact_clbk(self, value=None, **kw):
        """Callback update bact for solenoid"""
        self.set_bact(value)

    def set_bact(self, bact):
        """Helper method to set bact in ui"""
        self.ui.cur_sol_val.setText('{:.3g}'.format(bact) if bact else None)

    def set_binit(self, binit):
        """Helper method to set binit at start of scan"""
        self.ui.init_sol_val.setText('{:.3g}'.format(binit))

    ################ Scan Actions ################

    def toggle_scan(self):
        """Start or Abort a scan"""
        if self.ui.start_button.text() == constants.ABORT:
            self.abort = True
            self.bpm_thread.stop()
            self.log_msg(constants.ABORT_MSG)
            self.restore()
            return
        self.abort = False
        self.start_scan()

    def start_scan(self):
        """Start the solenoid alignment scan"""
        self.log_msg(constants.START_MSG)
        self.set_scanning_ui()
        self.sol_vals = self.get_sol_vals()
        # Need to get actual z locations and Leff
        self.sol_cor = SolCorrection(self.solenoid, float(self.ui.gun_energy.text()))
        print("running step");
        self.run_step()

    def run_step(self):
        """Run this for each solenoid setting"""
        # Quit if abort requested and reset
        print("not aborted? {0}".format(self.abort))
        if self.abort:
            return
        # We've run through all sol vals
        print("# of sol vals? {0}".format(len(self.sol_vals)))
        if len(self.sol_vals) > 0:
            self.run_sol_thread()
            return

        # We've finished the scan
        self.restore()
        self.set_offsets()
        self.log_msg('scan finished')

    def run_sol_thread(self):
        """Run the solenoid thread to set B field"""
        sol_val = self.sol_vals.pop(0)
        self.log_msg('setting solenoid value to {0}'.format(sol_val))
        self.b_thread = MagnetSet(self.solenoid, sol_val)
        self.b_thread.finished.connect(self.run_bpm_thread)
        self.b_thread.start()

    def run_bpm_thread(self):
        """Collect BPM data"""
        self.log_msg('gathering bpm data')
        self.bpm_thread = BPMRead(self.bpm, int(self.ui.bpm_readings.text()))
        self.bpm_thread.signal.connect(self.update_data)
        self.bpm_thread.start()

    @pyqtSlot(float, float, float, float)
    def update_data(self, x, y, x_std, y_std):
        """Emit signal to update data on each iteration, update plot, run next step"""
        self.sol_cor.add_data(x, y, x_std, y_std)
        self.plot()
        self.run_step()

    def restore(self):
        """Restore UI to ready for scan state"""
        self.log_msg('restoring to idle state')
        self.set_idle_ui()
        self.solenoid.bctrl = float(self.ui.init_sol_val.text())

    def set_offsets(self):
        """Display results of scan calculation"""
        results = self.sol_cor.calc_offsets()
        self.ui.xo.setText('{:.3g}'.format(results[0]))
        self.ui.yo.setText('{:.3g}'.format(results[1]))
        self.ui.x_prime.setText('{:.3g}'.format(results[2]))
        self.ui.y_prime.setText('{:.3g}'.format(results[3]))
        self.ui.x_ref.setText('{:.3g}'.format(results[4]))
        self.ui.y_ref.setText('{:.3g}'.format(results[5]))
        self.results = results
        self.ui.apply_cor.setEnabled(True)
    def get_sol_vals(self):
        """Find the steps for the current scan"""
        upper = float(self.ui.sol_upper.text())
        lower = float(self.ui.sol_lower.text())
        steps = int(self.ui.meas_num_combo.currentText())
        sol_vals = np.linspace(lower, upper, steps).tolist()
        self.log_msg('calculated steps {0}'.format(sol_vals))

        return sol_vals

    def plot(self):
        """Update the plot"""
        #self.plotCanvas.axes.cla()
        self.plotCanvas.draw_idle()
        if len(self.sol_cor.b_vals) > 0:
            b = self.sol_cor.b_vals
            x = self.sol_cor.x_vals
            y = self.sol_cor.y_vals
            y_std = self.sol_cor.y_stds
            x_std = self.sol_cor.x_stds
            print('b ', b, 'x ', x, 'x std ', x_std)
            # err_x = pg.ErrorBarItem(x=b, y=x[-1], height=x_std, beam=0.5)
            # err_y = pg.ErrorBarItem(x=b, y=y[-1], height=y_std, beam=0.5)
            self.plotCanvas.axes.errorbar(b, x, x_std, fmt = 'bo')#, pen='r', clear=True)
            # self.ui.sol_plot.addItem(err_x)
            # self.ui.sol_plot.addItem(err_y)
            self.plotCanvas.axes.errorbar(b, y, y_std, fmt = 'go') #, pen='g')

    ############# Corrections ##################

    def apply_correction(self):
        self.log_msg('applying correction: {0}'.format(self.results))
        x0 = self.solenoid.mover.x
        y0 = self.solenoid.mover.y
        xp0 = self.solenoid.mover.xp
        yp0 = self.solenoid.mover.yp 
        self.solenoid.mover.x = x0 + self.results[0]
        self.solenoid.mover.y = y0 + self.results[1]
        self.solenoid.mover.xp = xp0 - self.results[2]
        self.solenoid.mover.yp = yp0 - self.results[3]
    ############# Log and status bar message #################

    def log_msg(self, msg):
        self.logger.info(msg)
        self.ui.statusbar.setText(msg)
