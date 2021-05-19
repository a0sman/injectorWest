#!/usr/local/lcls/package/python/current/bin/python
import sys
from PyQt4 import QtGui, QtCore
from epics import caget,caput,PV
from InjectorAlignment_ui import Ui_MainWindow
from mpl_nosubplot import MplWidget
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from time import sleep
import lcls2_phase_scans
from threading import Thread
import physicselog
import shutil
import numpy as np
import lcls2_injector_devices as device

class InjectorAlignmentGUI(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.addLCLS2Picture()   
        self.connectElements()
        self.createMenu()
        self.configFile='/home/physics/zimmerc/python/test/Injector_Alignment_config.txt'
        self.loadConfig()#Loads config from file; objects for elements populated by config file are created in this method
        self.createCallbacks()
        self.numChargeValsToAvg=5#How many measurements to average for cathode alignment steps
        self.abortFlag=False
        self.setupPlots()
        self.buncher=device.Buncher()
        self.yag=device.Yag()
        self.solenoid=device.Magnet("SOLN:GUNB:212")
        self.solenoidInit,self.solenoidSettingForFocus=self.solenoid.readB()[0],.5
        self.numberBuncherYagShots=5
        self.chargeDevices={"ICT":"TORO:GUNB:360", "BPM1":"BPMS:GUNB:314", "BPM2":"BPMS:GUNB:925", "FCUP":"FARC:GUNB:999"}
        self.initMirrorX,self.initMirrorY,self.initCathodeCenterX,self.initCathodeCentery,self.initCathodePositionX,self.initCathodePositionY=self.getInitialSettings()
        self.setupChargeMeas()

    def connectElements(self):
        '''Connect GUI elements to methods'''
        self.ui.startCathAlignButton.pressed.connect(self.cathAlign)
        self.ui.abortButton.pressed.connect(self.abort)
        self.ui.startSolAlignButton.pressed.connect(self.solAlign)
        self.ui.startBunchAlignButton.pressed.connect(self.bunchAlign)
        self.ui.logButton.pressed.connect(self.Logbook)
        self.ui.cathodeXLineEdit.returnPressed.connect(self.cathodeXSet)
        self.ui.cathodeYLineEdit.returnPressed.connect(self.cathodeYSet)
        self.ui.chargeSelectionMenu.activated.connect(self.setupChargeMeas)

    def createCallbacks(self):
        self.mirrorX,self.mirrorY=device.Mirror('MIRR:LGUN:820:M3_MOTR_H'),device.Mirror('MIRR:LGUN:820:M3_MOTR_V')
        self.mirrorX.mirrorSetting.add_callback(self.updateMirrorX)
        self.mirrorY.mirrorSetting.add_callback(self.updateMirrorY)
        #self.mirrorX,self.mirrorY=device.Mirror('MIRR:IN20:162:M2_MOTR_H'),device.Mirror('MIRR:IN20:162:M2_MOTR_V')#3 lines TESTING
        #self.mirrorX.mirrorSetting.add_callback(self.updateMirrorX)
        #self.mirrorY.mirrorSetting.add_callback(self.updateMirrorY)
        #self.mirrorX,self.mirrorY=PV('DUMMYPV',callback=self.updateMirrorX),PV('DUMMYPV',callback=self.updateMirrorY)#Current mirror settings#REMOVE?!?
        self.lastPositionX,self.lastPositionY=PV('SIOC:SYS0:ML03:AO154',callback=self.updatePositionX),PV('SIOC:SYS0:ML03:AO155',callback=self.updatePositionY)
        
    def addLCLS2Picture(self):
        '''Add LCLS-II graphic in GUI, using a qGraphicsView'''
        scene=QtGui.QGraphicsScene()
        pixmap = QtGui.QPixmap("/home/physics/lcls2.png")
        scene.addPixmap(pixmap)
        gfxPixItem = self.ui.graphicsView.setScene(scene)

    def createMenu(self):     
        '''Set up file and panels menus'''
        self.file_menu = self.menuBar().addMenu("&File")
        logbook_action = self.create_action("LogBook",
            shortcut="Ctrl+P", slot=self.Logbook, 
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
            (logbook_action, save_config_action, load_config_action, None, quit_action))        
        self.panels_menu = self.menuBar().addMenu("&Panels...")
        laser_action = self.create_action("&Laser Panel", 
            shortcut='Ctrl+L', slot=self.laserPanel, 
            tip='Open EPICS Laser Panel')
        solenoid_action = self.create_action("&Solenoid Motion",
            shortcut='Ctrl+F', slot=self.solenoidPanel,
            tip='Open Solenoid Motion Panel')
        self.add_actions(self.panels_menu, (laser_action,solenoid_action))

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

    def setupChargeMeas(self):
        '''Handle user changing cathode align charge measurement device, create new chargemeas object'''
        self.charge=device.ChargeMeas(device=self.chargeDevices[str(self.ui.chargeSelectionMenu.currentText())])

    def getInitialSettings(self):
        '''Get initial mirror/cathode settings, mainly to have for abort and restore'''
        self.ui.initMirrorXLabel.setText(str(self.mirrorX.get()))
        self.ui.initMirrorYLabel.setText(str(self.mirrorY.get()))
        lastmirrorcenterx,lastmirrorcentery=caget('SIOC:SYS0:ML03:AO152'),caget('SIOC:SYS0:ML03:AO153')#Last measured mirror positions corresponding to cathode center
        return self.mirrorX.get(),self.mirrorY.get(),lastmirrorcenterx,lastmirrorcentery,self.lastPositionX.get(),self.lastPositionY.get()

    def setupPlots(self):
        '''Create subplots for adding data during measurements'''
        self.cathodePlot=self.ui.cathodePlot.canvas.fig.add_subplot(1,1,1)

    def updateMirrorX(self, value=None, **kwd):
        '''Callback function for x mirror motor, updates GUI display of current position'''
        self.ui.currentMirrorXLabel.setText(str(round(value,5)))

    def updateMirrorY(self, value=None, **kwd):
        '''Callback function for y mirror motor, updates GUI display of current position'''
        self.ui.currentMirrorYLabel.setText(str(round(value,5)))

    def updatePositionX(self, value=None, **kwd):
        '''Callback function for cathode position x'''
        self.ui.cathodeXLineEdit.setText(str(round(value,2)))

    def updatePositionY(self, value=None, **kwd):
        '''Callback function for cathode position y'''
        self.ui.cathodeYLineEdit.setText(str(round(value,2)))

    def cathodeXSet(self, setting=None):#Add motor movements!
        '''Handles user changing the desired x cathode position; translates to motor position and sets'''
        try:
            if setting==None: setting=float(self.ui.cathodeXLineEdit.text())
            else: setting=float(setting)
        except:
            self.updateStatus('Enter a valid number!')
            self.ui.cathodeXLineEdit.setText(self.lastPositionX.get())
            return
        if not (-2.5 <= setting <= 2.5):
            self.updateStatus('Enter a valid number!')
            self.ui.cathodeXLineEdit.setText(self.lastPositionX.get())
            return
        self.lastPositionX.put(self.ui.cathodeXLineEdit.text())
        centerx,rightx,leftx=float(caget('SIOC:SYS0:ML03:AO152')),float(caget('SIOC:SYS0:ML03:AO156')),float(caget('SIOC:SYS0:ML03:AO157'))
        if setting > 0:#If want to move right on cathode; consider the right edge and center
            mirrorsetting=centerx+((rightx-centerx)*(setting/2.5))
            print 'putting x mirror to',mirrorsetting
            if self.mirrorX.put(mirrorsetting)==False: self.updateStatus('Problem setting x mirror position!')
        elif setting < 0:
            mirrorsetting=centerx-((leftx-centerx)*(setting/2.5))
            print 'putting x mirror to',mirrorsetting
            if self.mirrorX.put(mirrorsetting)==False: self.updateStatus('Problem setting x mirror position!')
        else: 
            pass
            if self.mirrorX.put(centerx)==False: self.updateStatus('Problem setting x mirror position!')

    def cathodeYSet(self, setting=None):
        '''Handles user changing desired y cathode position, translates to motor position and sets'''
        try:
            if setting==None: setting=float(self.ui.cathodeYLineEdit.text())               
            else: setting=float(setting)
        except:
            self.updateStatus('Enter a valid number!')
            self.ui.cathodeYLineEdit.setText(self.lastPositionY.get())
            return
        if not (-2.5 <= setting <= 2.5):
            self.updateStatus('Enter a valid number (-2.5 to 2.5)!')
            self.ui.cathodeYLineEdit.setText(self.lastPositionY.get())
            return
        self.lastPositionY.put(self.ui.cathodeYLineEdit.text())
        centery,topy,bottomy=float(caget('SIOC:SYS0:ML03:AO153')),float(caget('SIOC:SYS0:ML03:AO158')),float(caget('SIOC:SYS0:ML03:AO159'))
        if setting > 0:#If want to move right on cathode; consider the right edge and center
            mirrorsetting=centery+((topy-centery)*(setting/2.5))
            print 'putting x mirror to',mirrorsetting
            #if self.mirrorY.put(mirrorsetting)==False: self.updateStatus('Problem setting y mirror position!')
        elif setting < 0:
            mirrorsetting=centery-((bottomy-centery)*(setting/2.5))
            print 'putting x mirror to',mirrorsetting
            #if self.mirrorY.put(mirrorsetting)==False: self.updateStatus('Problem setting y mirror position!')
        else:
            pass
            #if self.mirrorY.put(centery)==False: self.updateStatus('Problem setting y mirror position!')      

    def cathAlign(self):
        '''Connected to the perform cathode alignment button; scans laser position on cathode to find x and y edges'''
        self.abortFlag=False
        self.initMirrorX,self.initMirrorY,self.initCathodeCenterX,self.initCathodeCentery,self.initCathodePositionX,self.initCathodePositionY=self.getInitialSettings()
        self.cathodeXSet(setting=0.0)
        self.cathodeYSet(setting=0.0)
        smallstep,bigstep=float(self.ui.stepSizeBigCathodeEdit.text()),float(self.ui.stepSizeSmallCathodeEdit.text())
        startval,threshold=float(self.ui.startPositionCathodeLineEdit.text()),float(self.ui.chargeCathodeThresholdEdit.text())
        self.alignCathodeX(smallstep,bigstep,startval,threshold)
        if self.abortFlag==True: return
        self.alignCathodeY(smallstep,bigstep,startval,threshold)
        if self.abortFlag==True: return
        result = QtGui.QMessageBox.question(self, 'Confirm Cathode Alignment', "Do you want to update saved motor values corresponding to the cathode center?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result==QtGui.QMessageBox.Yes:
            for pv,setting in zip(['SIOC:SYS0:ML03:AO152','SIOC:SYS0:ML03:AO153','SIOC:SYS0:ML03:AO156','SIOC:SYS0:ML03:AO157','SIOC:SYS0:ML03:AO158','SIOC:SYS0:ML03:AO159'],[self.measuredcenterX,self.measuredCenterY,self.rightEdge,self.leftEdge,self.topEdge,self.bottomEdge]):
                caput(pv,setting)#Set support PVs with new measured values
        else:
            self.abort('Correction Not Applied')

    def updateCathodePlot(self):
        '''Update the cathode alignment scan plot with x and y charge values vs. mirror settings'''
        self.cathodePlot.clear()
        self.cathodePlot.plot(self.xmirrorsettings,self.xchargevals,'bo', label='X')
        self.cathodePlot.plot(self.ymirrorsettings,self.ychargevals,'go', label='Y')
        self.cathodePlot.set_title('Charge vs. MH2 Motor Positions')
        self.cathodePlot.legend()
        self.ui.cathodePlot.canvas.draw()
        QtGui.QApplication.processEvents()

    def alignCathodeX(self,smallstep,bigstep,startval,threshold):#
        '''scan the x mirror motor to determine the x edges of the cathode (where charge drops off) in relation to mirror position'''
        self.cathodeXSet(setting=startval)#Find right edge, start by setting requested offset 
        self.ui.cathodeXLineEdit.setText('0.0')#Just set text to zero so as to not confuse user; will end at zero position anyways
        self.xchargevals,self.xmirrorsettings,self.ychargevals,self.ymirrorsettings=[],[],[],[]
        charge=threshold+1#Simply so will go into while loop, cheap but effective kludge
        while charge > threshold:
            if self.mirrorX.put(self.mirrorX.get()+bigstep)==False: self.abort('Problem setting x mirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg)
            self.updateDataListsX(charge)
        self.mirrorX.put(self.mirrorX.get()-bigstep)
        charge=threshold+1
        while charge  > threshold:
            if self.mirrorX.put(self.mirrorX.get()+smallstep)==False: self.abort('Problem setting x mirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg)
            self.updateDataListsX(charge)
        self.rightEdge=self.mirrorX.get()-smallstep
        self.cathodeXSet(setting=-startval)#Find left edge, start by setting negative offset (move closer to edge to save time)
        self.ui.cathodeXLineEdit.setText('0.0')
        charge=threshold+1
        while charge > threshold:    
            if self.mirrorX.put(self.mirrorX.get()-bigstep)==False: self.abort('Problem setting x mirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg) 
            self.updateDataListsX(charge)
        self.mirrorX.put(self.mirrorX.get()+bigstep)
        charge=threshold+1
        while charge > threshold:           
            if self.mirrorX.put(self.mirrorX.get()-smallstep)==False: self.abort('Problem setting x mirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg) 
            self.updateDataListsX(charge)
        self.leftEdge=self.mirrorX.get()+smallstep
        self.measuredCenterX=(self.rightedge+self.leftedge)/2
        self.mirrorX.put(self.MeasuredCenterX)

    def updateDataListsX(self,charge):
        '''Just a method to update the mirror setting and charge setting lists, then calls the plotting method that plots these lists'''
        self.xchargevals.append(charge)
        self.xmirrorsettings.append(self.mirrorX.get())
        self.updateCathodePlot()
        
    def alignCathodeY(self,smallstep,bigstep,startval,threshold):
        '''scan the y mirror motor to determine the x edges of the cathode (where charge drops off) in relation to mirror position'''
        self.cathodeYSet(setting=startval)#Find top edge, start by setting offset (to get closer to edge)
        self.ui.cathodeYLineEdit.setText('0.0')
        charge=threshold+1
        while charge > threshold: 
            if self.mirrorY.put(self.mirrorY.get()+bigstep)==False: self.abort('Problem setting ymirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg)
            self.updateDataListsY(charge)
        self.mirrorY.put(self.mirrorY.get()-bigstep)
        charge=threshold+1
        while charge > threshold:           
            if self.mirrorY.put(self.mirrorY.get()+smallstep)==False: self.abort('Problem setting ymirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg)
            self.updateDataListsY(charge)
        self.topEdge=self.mirrorY.get()-smallstep
        self.cathodeYSet(setting=-startval)#Find bottom edge
        self.ui.cathodeYLineEdit.setText('0.0')
        charge=threshold+1
        while charge > threshold:
            if self.mirrorY.put(self.mirrorY.get()-bigstep)==False: self.abort('Problem setting ymirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg) 
            self.updateDataListsY(charge)
        self.mirrorY.put(self.mirrorY.get()+bigstep)
        charge=threshold+1
        while charge  > threshold:                     
            if self.mirrorY.put(self.mirrorY.get()-smallstep)==False: self.abort('Problem setting ymirror.  Aborting')
            if self.abortFlag==True: return
            charge=self.charge.acquireCharge(numberShots=self.numChargeValsToAvg) 
            self.updateDataListsY(charge)
        self.bottomEdge=self.mirrorY.get()+smallstep
        self.measuredCenterY=(self.topedge+self.bottomedge)/2
        self.mirrorY.put(self.MeasuredCenterY)

    def updateDataListsY(self,charge):
        self.ychargevals.append(charge)
        self.ymirrorsettings.append(self.mirrorY.get())
        self.updateCathodePlot()

    def abort(self,message='Aborted!'):
        self.abortFlag=True
        QtGui.QApplication.processEvents()
        #self.initMirrorX,self.initMirrorY,self.initCathodeCenterX,self.initCathodeCentery,self.initCathodePositionX,self.initCathodePositionY=self.getInitialSettings()
        self.mirrorX.put(self.initMirrorX)
        self.mirrorY.put(self.initMirrorY)
        self.lastPositionX.put(self.initCathodePositionX)
        self.lastPositionY.put(self.initCathodePositionY)
        self.solenoid.setB(self.solenoidInit)
        self.updateStatus(message)

    def solAlign(self):
        pass

    def bunchAlign(self):
        self.abortFlag=False
        self.solenoidInit=self.solenoid.readB()[0]
        self.buncher.flipPhase()#Set to debunching zero crossing (assumes that the buncher is phased properly
        if self.adjustSolenoidforYagFocus==False:
            self.abort('Solenoid not tracking; aborting')
            return
        if self.yag.insert()==False:
            self.abort('Yag not inserting; aborting')
            return           
        xdb,ydb=self.calculateCentroid(numberShots=self.numberBuncherYagShots)
        #Deact Buncher
        xoff,yoff=self.calculateCentroid(numberShots=self.numberBuncherYagShots)
        #ReactBuncher
        while xdb-xoff > .04:#40um, specified in Feng's commissioning paper
            #Adjust Xcor(s) negative?
            xdb,ydb=self.calculateCentroid(numberShots=self.numberBuncherYagShots)
        while xdb-xoff < .04:
            #Adjust Xcor(s) positive?
            xdb,ydb=self.calculateCentroid(numberShots=self.numberBuncherYagShots)
        while ydb-yoff > .04:
            #AdjustYcor negative?
            xdb,ydb=self.calculateCentroid(numberShots=self.numberBuncherYagShots)
        while ydb-yoff < .04:
            #AdjustYcor positive?
            xdb,ydb=self.calculateCentroid(numberShots=self.numberBuncherYagShots)
                
    def adjustSolenoidforYagFocus(self):
        '''Method for adjusting solenoid to focus beam at YAG screen; initially this will just set to fixed value'''
        return self.Solenoid.setB(self.solenoidSettingForFocus)        

    def solenoidPanel(self):
        print 'open sol panel'

    def laserPanel(self):
        print 'open laser panel'

    def Logbook(self):
        '''Save image of plot to physics elog and also save data to file'''
        p=QtGui.QPixmap.grabWidget(self)
        p.save('/tmp/lcls2InjAlign.png','png')
        physicselog.submit_entry(logbook='lcls2',username='LCLS2_Injector_Alignment', title='Screenshot', attachment='/tmp/lcls2InjAlign.png')
        self.updateStatus('Image saved to physics elog')
        
    def saveConfig(self):
        '''Save configuration file to populate defaults for certain GUI elements'''
        newlines=[]
        with open(self.configFile,'r') as f: lines = f.readlines()        
        for i, guiElement in enumerate(self.guiElements):
            try: newlines.append(str(guiElement.currentText())+'#'+lines[i].split('#')[1])
            except: newlines.append(str(guiElement.text())+'#'+lines[i].split('#')[1])
        with open(self.configFile,'w') as f: f.writelines(newlines)
        self.updateStatus('Saved new defaults to file')

    def loadConfig(self):
        '''Load configuration file to populate defaults on each panel (mirror step size, num steps etc.); called on startup'''
        with open(self.configFile) as f: lines = [line.rstrip('\n') for line in f]
        self.guiElements=[self.ui.stepSizeBigCathodeEdit,self.ui.stepSizeSmallCathodeEdit,self.ui.startPositionCathodeLineEdit,self.ui.chargeCathodeThresholdEdit,self.ui.solScanRangeEdit,self.ui.numStepsEdit]
        for i, guiElement in enumerate(self.guiElements):
            try: self.guiElements[i].setText(lines[i].split('#')[0])
            except: print 'Error setting configuration values!'
        self.updateStatus('Loaded defaults from file')

    def updateStatus(self,message):
        print(message)
        self.ui.statusbar.showMessage(message)
        QtGui.QApplication.processEvents()

    def restoreInitial(self):
        self.abort(message="Restored initial values")

    def closeEvent(self,event):
       	print 'Goodbye!  Until next time'


def main():
    app = QtGui.QApplication(sys.argv)
    window = InjectorAlignmentGUI()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
	main()
