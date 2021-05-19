#!/usr/local/lcls/package/python/current/bin/python

import sys
import unittest
from PyQt4.QtGui import QApplication
from sol_align import SolAlign

SOL1B = 'SOL1B'
SOL2B = 'SOL2B'
BPM1B = 'BPM1B'
BPM2B = 'BPM2B'
SOL_VALS_POP = [5.0, 5.25]
SOL_VALS = [4.75, 5.0, 5.25]

class TestSolAlign(unittest.TestCase):
    def setUp(self):
        self.form = SolAlign(debug=True)

    def test_init_label_vals(self):
        self.assertEqual(self.form.ui.sol_combo.currentText(), 'SOL1B')
        self.assertEqual(self.form.ui.percent_sb.text(), '5')
        self.assertEqual(self.form.ui.bpm_readings.text(), '10')
        self.assertEqual(self.form.ui.meas_num_combo.currentText(), '3')
        self.assertEqual(self.form.ui.gun_energy.text(), '0.75')

    def test_Init_sol_vals(self):
        self.assertEqual(self.form.solenoid.bact, 5.0)
        self.assertEqual(self.form.ui.sol_upper.text(), '5.25')
        self.assertEqual(self.form.ui.sol_lower.text(), '4.75')
        self.assertEqual(self.form.ui.cur_sol_val.text(), '5')

    def test_initial_ui(self):
        self.form.set_idle_ui()
        self._confirm_idle_ui()

    def test_scanning_ui(self):
        self.form.set_scanning_ui()
        self._confirm_scanning_ui()

    def test_debug(self):
        """Test setting debug property"""
        self.assertEqual(self.form.debug, True)
        self.form.debug = False
        self.assertEqual(self.form.debug, False)
        self.form.debug = True
        self.assertEqual(self.form.debug, True)

    def test_get_sol(self):
        """Verify we get correct solenoid"""
        self.form.get_sol()
        self.assertEqual(self.form.solenoid.name, SOL1B)
        
    def test_percent_sb(self):
        """Verify we can set the values and limits are functional for percent spin box"""
        self.assertEqual(self.form.ui.percent_sb.value(), 5)
        self.assertEqual(self.form.ui.percent_sb.maximum(), 99)
        self.assertEqual(self.form.ui.percent_sb.minimum(), 0)
        self.assertEqual(self.form.ui.percent_sb.singleStep(), 1)
        self.form.ui.percent_sb.setValue(105)
        self.assertEqual(self.form.ui.percent_sb.value(), 99)
        self.form.ui.percent_sb.setValue(-5)
        self.assertEqual(self.form.ui.percent_sb.value(), 0)
        self.form.ui.percent_sb.setValue(5)
        self.assertEqual(self.form.ui.percent_sb.value(), 5)
        
    def test_sol_select(self):
        """Verify the correct solenoid/bpm are displayed when updating current solenoid"""
        self.assertEqual(self.form.ui.bpm_label.text(), BPM1B)
        idx = self.form.ui.sol_combo.findText(SOL2B)
        self.form.ui.sol_combo.setCurrentIndex(idx)
        self.form.sol_select()
        # Assert current bpm is correct
        self.assertEqual(self.form.ui.bpm_label.text(), BPM2B)
        self.assertEqual(self.form.bpm.name, BPM2B)
        # Assert sol combo text is correct
        self.assertEqual(self.form.ui.sol_combo.currentText(), SOL2B)

    def test_set_sol_hi_low(self):
        """Verify upper and lower limits of scan range set properly on bact"""
        self.form.solenoid.bctrl = 2.0
        self.form.set_sol_hi_low()
        self.assertEqual(self.form.ui.sol_upper.text(), '2.1')
        self.assertEqual(self.form.ui.sol_lower.text(), '1.9')

    def test_toggle_scan(self):
        """Verify toggle scan sets appropriate state"""
        # Start
        self.form.toggle_scan()
        self.assertEqual(self.form.ui.start_button.text(), 'Abort')
        self.assertEqual(self.form.abort, False)
        self._confirm_scanning_ui()
        # Abort
        self.form.toggle_scan()
        self.assertEqual(self.form.ui.start_button.text(), 'Start')
        self.assertEqual(self.form.abort, True)
        self._confirm_idle_ui()
        
    def test_start_scan(self):
        self.assertEqual(self.form.sol_vals, None)
        self.assertEqual(self.form.sol_cor, None)
        self.form.start_scan()
        self.assertEqual(self.form.sol_vals, SOL_VALS_POP)
        self.assertNotEqual(self.form.sol_cor, None)

    def test_run_step(self):
        self.form.sol_vals = self.form.get_sol_vals()
        self.assertEqual(self.form.sol_vals, SOL_VALS)
        self.form.run_step()
        self.assertEqual(self.form.sol_vals, SOL_VALS_POP)

    def test_run_sol_thread(self):
        self.form.sol_vals = self.form.get_sol_vals()
        self.form.run_sol_thread()

    def test_run_bpm_thread(self):
        self.form.run_bpm_thread()

    def test_restore(self):
        self.form.start_scan()

    def _confirm_idle_ui(self):
        self.assertEqual(self.form.ui.sol_combo.isEnabled(), True)
        self.assertEqual(self.form.ui.percent_sb.isEnabled(), True)
        self.assertEqual(self.form.ui.meas_num_combo.isEnabled(), True)
        self.assertEqual(self.form.ui.bpm_readings.isEnabled(), True)
        self.assertEqual(self.form.ui.apply_cor.isEnabled(), True)
        self.assertEqual(self.form.ui.sol_upper.isReadOnly(), False)
        self.assertEqual(self.form.ui.sol_lower.isReadOnly(), False)

    def _confirm_scanning_ui(self):
        self.assertEqual(self.form.ui.sol_combo.isEnabled(), False)
        self.assertEqual(self.form.ui.percent_sb.isEnabled(), False)
        self.assertEqual(self.form.ui.meas_num_combo.isEnabled(), False)
        self.assertEqual(self.form.ui.bpm_readings.isEnabled(), False)
        self.assertEqual(self.form.ui.apply_cor.isEnabled(), False)
        self.assertEqual(self.form.ui.sol_upper.isReadOnly(), True)
        self.assertEqual(self.form.ui.sol_lower.isReadOnly(), True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    unittest.main()
