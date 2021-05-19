#!/usr/local/lcls/package/python/current/bin/python
import sys
from PyQt4 import QtGui, QtCore
from lcls2phase_ui import Ui_MainWindow
from mpl_nosubplot import MplWidget
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from time import sleep
import lcls2_phase_scans
from threading import Thread
import pylog
import shutil
import numpy as np
import physicselog
from subprocess import Popen
from epics import caput

class LCLS2PhasingGUI(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.addLCLS2Picture()
        self.plotWindow=MplWidget()#Initialize plot window (widget) for displaying measurements
        self.connectGuiElements()
        self.configFile='/home/physics/zimmerc/python/test/lcls2_phase_scans_config.txt'
        self.tempFile='/home/physics/zimmerc/python/test/lcls2_phase_scans_config_temp.txt'
        self.loadConfig()#Populate GUI elements with proper values (start phases etc.)
        self.initializeScanObjects()#Instantiate phase scan classes
        self.plotObjects=[]#Initialize plotObjects, which will hold references to subplots on plotWindow widget
        self.navi_toolbar=NavigationToolbar(self.plotWindow.canvas,self)
        self.plotWindow.vb1.addWidget(self.navi_toolbar)
        self.createMenu()
        self.realtimeUpdateDelay=.1
        #self.loadStyleSheet()

    def loadStyleSheet(self):
	try:
            self.cssfile = "/home/physics/zimmerc/python/style.css"
            with open(self.cssfile,"r") as f:
			self.setStyleSheet(f.read())
	except IOError:
            print 'No style sheet found!'
            palette = QtGui.QPalette()
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
            self.ui.textBrowser.setPalette(palette)

    def addLCLS2Picture(self):
        '''Add LCLS-II graphic at top of GUI, using a qGraphicsView'''
        scene=QtGui.QGraphicsScene()
        pixmap = QtGui.QPixmap("/home/physics/lcls2.png")
        scene.addPixmap(pixmap)
        gfxPixItem = self.ui.graphicsView.setScene(scene)

    def connectGuiElements(self):
        '''Connect buttons to functions, etc.'''
        self.ui.laserScanButton.clicked.connect(self.laserPhaseScan)
        self.ui.buncherPhaseScanButton.clicked.connect(self.buncherPhaseScan)
        self.ui.gunAmpScanButton.clicked.connect(self.gunAmplitudeScan)
        self.ui.buncherAmpScanButton.clicked.connect(self.buncherAmplitudeScan)
        self.ui.generalStationScanButton.clicked.connect(self.generalPhaseScan)
        self.ui.generalStationBox1.activated.connect(self.setStation)
        self.ui.generalStationBox2.activated.connect(self.setStation)
        self.ui.abortButton.clicked.connect(self.abortScan)
        self.ui.logButton.clicked.connect(self.savePlot)

    def initializeScanObjects(self):
        '''Instantiate phase scan objects for different injector phase scans'''
        self.laser=lcls2_phase_scans.LaserPhase()
        print 'laserdone'
        self.buncherPhase=lcls2_phase_scans.BuncherPhase()
        print 'buncherdone'
        self.gunAmplitude=lcls2_phase_scans.GunAmplitude()
        print 'gundone'
        self.buncherAmplitude=lcls2_phase_scans.BuncherAmplitude()
        print 'buncherdone'
        self.generalScan=lcls2_phase_scans.GeneralPhaseScan()
        print 'donewithobjects'

    def setupPlotWindow(self, numPlots, titles):
        '''Function to reinitialize plot widget/window with requested number of plots'''
        for obj in self.plotObjects:
            obj.clear()
        self.plotObjects=[]
        for i in range(numPlots):
            self.plotObjects.append(self.plotWindow.canvas.fig.add_subplot(int(str(numPlots)+'1'+str(i+1))))
            self.plotObjects[i].set_title(titles[i])
        self.plotWindow.show()

    def abortScan(self):
        '''Set abort class variables for phasescan objects and copy config file'''
        self.laser.abortScan=True
        self.buncherPhase.abortScan=True
        self.gunAmplitude.abortScan=True
        self.buncherAmplitude.abortScan=True
        shutil.copyfile(self.tempFile,self.configFile)#Should this be here?  Kludge to make sure if user aborts, temporary file gets copied back to normal config file
        raise Exception('Aborted by User!!!')

    def laserPhaseScan(self):
        '''Perform laser phase scan and update realtime plot showing measurement progress and final data'''
        self.changeButtonState('Disable')
        shutil.copyfile(self.configFile,self.tempFile)#Copy current config file; saving what is currently in GUI to make things easy (will recopy back later)
        self.saveConfig()#Save values to file so lcls2_phase_scans.py picks up user edits to text fields
        self.updateStatus('Laser Phase Scan active...')
        self.setupPlotWindow(2,['Realtime Measurement Progress','Final (averaged) data'])
        t=ThreadWithReturnValue(target=self.laser.startPhaseScan)
        t.start()
        self.updateStatus('Laser scan in progress...')
        xvals,yvals=[],[]
        while t.isAlive():#While thread (i.e. measurement) is actively running, update realtime display plot
            xvals.append(self.laser.Laser.readPhase()[0])#I know this is confusing; laser is lcls2_phase_scans.py module class, Laser is lcls2_injector_devices.py module class
            yvals.append(self.laser.chargeMeas.acquireCharge())
            self.plotObjects[0].clear()
            self.plotObjects[0].set_title('Real-time Charge (pC) Vs. Phase (deg)')
            self.plotObjects[0].plot(xvals,yvals,'bx')
            self.plotWindow.canvas.draw()
            QtGui.QApplication.processEvents()
            sleep(self.realtimeUpdateDelay)
        shutil.copyfile(self.tempFile,self.configFile)
        data=t.join()#This joins the (now finished) thread and retrieves the returned values
        try:
            smallCharge,bigCharge,smallPhase,bigPhase,slope,zerocrossing,yzerocrossing=data
        except Exception as e:
            self.exceptionOccured(e)
            #caput('SIOC:SYS0:ML04:CALCOUT007.OUT','')#Disable phase control calcout PV as an extra safeguard
            return
        if slope==None:
            self.exceptionOccured('No small step data.  Did beam trip?')
            return
        fitdata=np.polyval([slope,zerocrossing],smallPhase)
        print smallPhase,smallCharge,bigPhase,bigCharge
        self.plotObjects[1].plot(smallPhase,fitdata,'g-',linewidth=2)#Plot linear fit of small data
        smallPhase.extend(bigPhase)
        smallCharge.extend(bigCharge)
        self.plotObjects[1].plot(smallPhase,smallCharge,'ro')#Adds data to final (lower) plot
        self.plotObjects[1].axvline(x=yzerocrossing)
        self.plotObjects[1].set_title('Final (averaged) data- zero crossing at '+str(round(yzerocrossing,2)))
        self.plotObjects[1].set_xlabel('Laser phase')
        self.plotObjects[1].set_ylabel('Charge (pC)')
        self.plotWindow.canvas.draw()
        self.updateStatus('Phase Scan Finished')
        self.changeButtonState('Enable')
        result = QtGui.QMessageBox.question(self, 'Confirm Correction', "Do you want to apply phase change (will set phase to "+str(round(yzerocrossing+float(self.ui.laserPhaseEdit.text()),2))+")?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes:
            self.laser.ApplyCorrection(zeroCrossing=yzerocrossing, desiredfinal=float(self.ui.laserPhaseEdit.text()))
        else:
            print 'Correction not applied'

    def buncherPhaseScan(self):
        '''Perform buncher phase scan and update realtime plot showing measurement progress and final data'''
        self.changeButtonState('Disable')
        shutil.copyfile(self.configFile,self.tempFile)
        self.saveConfig()
        self.updateStatus('Buncher Phase Scan active...')
        self.setupPlotWindow(2,['Realtime Measurement Progress','Final (averaged) data'])
        xvals,yvals=[],[]
        t=ThreadWithReturnValue(target=self.buncherPhase.startPhaseScan)
        t.start()
        i=0
        while t.isAlive():#While thread (i.e. measurement) is actively running, update realtime display plot
            xvals.append(i)
            yvals.append(self.buncherPhase.Buncher.readPhase()[1])
            self.plotObjects[0].clear()
            self.plotObjects[0].set_title('Buncher Phase (deg) vs. Time')#Test
            self.plotObjects[0].plot(xvals,yvals, 'bx')#Test
            self.plotObjects[0].axhline(y=self.buncherPhase.xPosGun, color='r', label='Gun Only Energy')
            self.plotWindow.canvas.draw()#Test
            QtGui.QApplication.processEvents()#Test
            sleep(self.realtimeUpdateDelay)#Test
            i+=1
        shutil.copyfile(self.tempFile,self.configFile)
        try:
            data=t.join()#Wait for thread to finish so we can get final data after scan finishes
            phases,energies,zeroCrossing,xPosGun=data#This joins the (now finished) thread and retrieves the returned values
            print 'data=',data
        except Exception as e:
            self.exceptionOccured(e)
            return
        self.plotObjects[1].clear()
        self.plotObjects[1].set_title("Energy (X position in mm) vs. Buncher Phase")
        self.plotObjects[1].plot(phases,energies,'bx')#Adds data to final (lower) plot
        self.plotObjects[1].axhline(y=xPosGun)
        self.plotWindow.canvas.draw()
        self.updateStatus('Phase Scan Finished')
        self.changeButtonState('Enable')
        result = QtGui.QMessageBox.question(self, 'Confirm Correction', "Do you want to apply phase offset change (true zero phase is "+str(zeroCrossing)+"deg)?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes:
            if self.buncherPhase.ApplyCorrection()==True:
                self.updateStatus('Scan complete, correction applied')
            else:
                self.updateStatus('Scan complete, correction FAILED')
        else:
            self.updateStatus('Scan complete, correction declined by user')

    def gunAmplitudeScan(self):
        '''Perform gun amplitude scan and update realtime plot showing measurement progress and final data'''
        self.changeButtonState('Disable')
        shutil.copyfile(self.configFile,self.tempFile)
        self.saveConfig()
        self.updateStatus('Gun Amplitude Scan active...')
        self.setupPlotWindow(2,['Realtime Measurement Progress','Final (averaged) data'])  
        xvals,yvals=[],[]
        t=ThreadWithReturnValue(target=self.gunAmplitude.startAmplitudeCalibrationMeas)
        t.start()
        i=0
        while t.isAlive():#While thread (i.e. measurement) is actively running, update realtime display plot
            xvals.append(i)
            yvals.append(self.gunAmplitude.Corrector.readB()[1])
            self.plotObjects[0].clear()
            self.plotObjects[0].set_title('XCOR setting (kG-m) vs. time (arbitrary units)')
            self.plotObjects[0].plot(xvals,yvals,'bx')
            self.plotWindow.canvas.draw()
            QtGui.QApplication.processEvents()
            sleep(self.realtimeUpdateDelay)
            i+=1
        shutil.copyfile(self.tempFile,self.configFile)
        data=t.join()
        try:
            positions,correctorVals,slope,offset,energy=data#This joins the (now finished) thread and retrieves the returned values
        except Exception as e:
            self.exceptionOccured(e)
            return
        fitdata=np.polyval([slope,offset],correctorVals)
        self.plotObjects[1].clear()
        self.plotObjects[1].plot(correctorVals,fitdata,'g-',linewidth=2)
        self.plotObjects[1].plot(correctorVals,positions,'bx')#Adds data to final (lower) plot
        self.plotObjects[1].set_title('Gun Amplitude Meas. Final: energy='+str(round(energy,4))+'keV, slope='+str(round(slope,3)))
        self.plotObjects[1].set_xlabel('Corrector Strength (kG-m)')
        self.plotObjects[1].set_ylabel('Position (um)')
        self.plotWindow.canvas.draw()
        self.updateStatus('Phase Scan Finished')
        self.changeButtonState('Enable')
        result = QtGui.QMessageBox.question(self, 'Confirm Correction', "The calculated energy is "+str(round(energy,4))+"keV, would you like to calibrate the gun energy setting/readback to match this?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes:
            caput('SIOC:SYS0:ML04:AO014',energy)#Save last accepted gun energy
            self.gunAmplitude.ApplyCorrection()
            self.updateStatus('Scan complete, correction applied')
        else:
            self.updateStatus('Scan complete, correction declined by user')
            
    def buncherAmplitudeScan(self):
        '''Perform buncher amplitude scan and update realtime plot showing measurement progress and final data'''
        result = QtGui.QMessageBox.question(self, 'Gun Amplitude Calibrated?!?', "Has the gun calibration been done successfully?  Has the buncher phase also been scanned and set to the bunching zero crossing?  These are prerequisites for the buncher amplitude calibration.  If not, please click no and calibrate the gun amplitude before attempting this measurement.  Press yes to proceed.", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes: print 'Gun energy calibration accuracy confirmed by user, proceeding'
        else: return
        self.changeButtonState('Disable')
        shutil.copyfile(self.configFile,self.tempFile)
        self.saveConfig()
        self.updateStatus('Buncher Amplitude Scan active...')
        self.setupPlotWindow(2,['Realtime Measurement Progress','Final (averaged) data'])
        xvals,yvals=[],[]
        t=ThreadWithReturnValue(target=self.buncherAmplitude.startAmplitudeCalibration)
        t.start()
        i=0
        while t.isAlive():#While thread (i.e. measurement) is actively running, update realtime display plot
            xvals.append(i)
            yvals.append(self.buncherAmplitude.Corrector.readB()[1])
            self.plotObjects[0].clear()
            self.plotObjects[0].set_title('XCOR Setting (kG-m) vs. time (arbitrary units)')
            self.plotObjects[0].plot(xvals,yvals,'bx')
            self.plotWindow.canvas.draw()
            QtGui.QApplication.processEvents()
            sleep(self.realtimeUpdateDelay)
            i+=1
        shutil.copyfile(self.tempFile,self.configFile)
        data=t.join()
        try:
            correctorVals,positions,combinedEnergy,buncherEnergy,m,b=data
        except Exception as e:
            self.exceptionOccured(e)
            return
        self.plotObjects[1].clear()
        fitdata=np.polyval([m,b],correctorVals)
        self.plotObjects[1].plot(correctorVals,fitdata,'g-',linewidth=2)
        self.plotObjects[1].plot(correctorVals,positions,'bx')#Adds data to final (lower) plot
        self.plotObjects[1].set_title('Gun+Buncher Amp. Meas- energy is '+str(round(buncherEnergy,2))+'keV, slope='+str(round(m,1)))
        self.plotObjects[1].set_xlabel('Corrector Strength (kG-m)')
        self.plotObjects[1].set_ylabel('Position (um)')
        self.plotWindow.canvas.draw()
        self.updateStatus('Amplitude Scan Finished')
        self.changeButtonState('Enable')
        result = QtGui.QMessageBox.question(self, 'Confirm Correction', "The calculated energy is "+str(round(buncherEnergy,2))+"keV (Gun+Buncher energy measured as "+str(round(combinedEnergy,2))+"keV), would you like to calibrate the buncher energy readback to match this?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes:
            self.buncherAmplitude.ApplyCorrection()
            self.updateStatus('Scan complete, correction applied')
        else:
            self.updateStatus('Scan complete, correction declined by user')

    def generalPhaseScan(self):###NEED TO FINISH (need motha f'in PVs, actual cryomodules, etc. BIOTCH###
        '''Phase scan general stations in the linac'''
        self.changeButtonState('Disable')
        shutil.copyfile(self.configFile,self.tempFile)
        self.saveConfig()
        self.updateStatus('Phase Scan Running...')
        self.setupPlotWindow(2,['Realtime Measurement Progress','Final (averaged) data'])
        yvals=[]
        t=ThreadWithReturnValue(target=self.generalScan.startPhaseScan)
        t.start()
        while t.isAlive():#While thread (i.e. measurement) is actively running, update realtime display plot
            #xvals.append(self.laser.readPhase()[1])
            #yvals.append(self.laser.readCharge())
            yvals.append(2)
            self.plotObjects[0].clear()#Test
            self.plotObjects[0].set_title('Realtime Measurement Progress')#Test
            self.plotObjects[0].plot(yvals)#Test
            self.plotWindow.canvas.draw()#Test
            QtGui.QApplication.processEvents()#Test
            sleep(self.realtimeUpdateDelay)#Test
        shutil.copyfile(self.tempFile,self.configFile)
        x,y=t.join()#This joins the (now finished) thread and retrieves the returned values
        self.plotObjects[1].plot(x,y)#Adds data to final (lower) plot
        self.plotWindow.canvas.draw()
        self.updateStatus('Phase Scan Finished')
        self.changeButtonState('Enable')

    def savePlot(self, data='None', title='None', text='None'):
        '''Save image of plot to physics elog and also eventually save data to file'''
        p=QtGui.QPixmap.grabWidget(self.plotWindow.canvas)
        p.save('/tmp/lcls2phasescan.png','png')
        physicselog.submit_entry(logbook='lcls2',username='LCLS2_Phase_Scans', title='Screenshot', attachment='/tmp/lcls2phasescan.png')
        self.updateStatus('Plot image saved')

    def saveConfig(self):
        '''Save configuration file containing settings for each panel when user requests from file menu'''
        newlines=[]
        with open(self.configFile,'r') as f: lines = f.readlines()
        nonguilines=lines[25:]#Only first 23 lines are used by GUI; so extend later config file lines at end
        for i, guiElement in enumerate(self.guiElements):
            try: newlines.append(str(guiElement.currentText())+'#'+lines[i].split('#')[1])
            except: newlines.append(str(guiElement.text())+'#'+lines[i].split('#')[1])
        newlines.extend(nonguilines)
        with open(self.configFile,'w') as f: f.writelines(newlines)
        self.updateStatus('Saved new defaults to file')
            
    def loadConfig(self):
        '''Load configuration file to populate defaults on each panel (phase change, num steps etc.); called on startup'''
        with open(self.configFile) as f: lines = [line.rstrip('\n') for line in f]
        self.guiElements=[self.ui.laserMeasSelectBox, self.ui.laserChargeEdit, self.ui.laserPhaseEdit, self.ui.laserInitPhaseShiftEdit,
               self.ui.laserNumShotsEdit, self.ui.buncherMeasBox, self.ui.buncherCorrectorBox, self.ui.buncherPhaseCorrectorChangeEdit, self.ui.buncherPhaseEdit, self.ui.buncherPhaseRangeEdit,
               self.ui.buncherPhaseNumShotsEdit, self.ui.gunAmpMeasBox, self.ui.gunAmpCorrectorBox, self.ui.gunCorrectorChangeEdit,
               self.ui.gunAmpNumShotsEdit, self.ui.bunchAmpMeasBox, self.ui.bunchAmpCorrectorBox, self.ui.buncherCorrectorChangeEdit,
               self.ui.buncherAmpNumShotsEdit, self.ui.generalStationMeasBox, self.ui.generalStationNumShotsEdit, self.ui.generalStationBox1,
               self.ui.generalStationBox2, self.ui.generalStationRange, self.ui.generalStationNumPoints]#All user editable elements in GUI

        for i, guiElement in enumerate(self.guiElements):
            try: self.guiElements[i].setCurrentIndex(self.guiElements[i].findText(lines[i].split('#')[0]))#Combobox
            except: self.guiElements[i].setText(lines[i].split('#')[0])#LineEdit
        self.updateStatus('Load successful')

    def setStation(self):
        self.generalScan.setStation(self.ui.generalStationBox1.currentText(),self.ui.generalStationBox2.currentText())

    def changeButtonState(self,desiredstate):
        buttons=[self.ui.laserScanButton,self.ui.buncherPhaseScanButton,self.ui.gunAmpScanButton,self.ui.buncherAmpScanButton,self.ui.generalStationScanButton]
        if desiredstate=="Enable":
            for button in buttons: button.setDisabled(False)
        elif desiredstate=="Disable":
            for button in buttons: button.setDisabled(True)

    def exceptionOccured(self, e):
        print e
        self.mbox=QtGui.QMessageBox.about(self, 'Issue during Scan!','Problem with scan: see xterm.')
        self.updateStatus('Phase Scan Done (exception encountered)')
        self.changeButtonState('Enable')   
            
    def llrfPanel(self):
        '''Open LLRF panel for currently selected station'''
        Popen(['edm','-x','/usr/local/lcls/tools/edm/display/lcls2/rf_gunb_main.edl'])

    def longitudinalPanel(self):
        '''Open panel for longitudinal feedback'''
        print 'longitudinal'
            
    def createMenu(self):     
        '''Set up file and panels menus'''
        self.file_menu = self.menuBar().addMenu("&File")
        load_file_action = self.create_action("Save Plot",
            shortcut="Ctrl+P", slot=self.savePlot, 
            tip="Save the plot")
        save_config_action = self.create_action("Save Config File",
            shortcut="Ctrl+S", slot=self.saveConfig, 
            tip="Save active settings (phases etc.) to config file")
        load_config_action = self.create_action("Load Config File",
            shortcut="Ctrl+L", slot=self.loadConfig, 
            tip="Load saved settings (phases etc.) from config file")
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, 
            (load_file_action, save_config_action, load_config_action, None, quit_action))
        
        self.panels_menu = self.menuBar().addMenu("&Panels...")
        llrf_action = self.create_action("&LLRF", 
            shortcut='Ctrl+L', slot=self.llrfPanel, 
            tip='Open LLRF panel for selected panel RF device')
        longitudinal_action = self.create_action("&Long. FB",
            shortcut='Ctrl+F', slot=self.longitudinalPanel,
            tip='Open Longitudinal Feedback Control Panel')
        self.add_actions(self.panels_menu, (llrf_action,longitudinal_action))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def updateStatus(self,message):
        self.ui.statusbar.showMessage(message)
        QtGui.QApplication.processEvents()

    def closeEvent(self,event):
       	print 'Goodbye!  Until next time'
	self.plotWindow.close()
        

class ThreadWithReturnValue(Thread):#Subclass to return a status from a thread.  Stupid that threading.Thread by default doesn't return a value. 
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self._return = None
    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args,
                                                **self._Thread__kwargs)
    def join(self):
        Thread.join(self)
        return self._return
        

def main():
    app = QtGui.QApplication(sys.argv)
    window = LCLS2PhasingGUI()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
	main()
