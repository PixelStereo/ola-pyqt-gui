#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
import textwrap
from time import sleep
from random import randrange
from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException
from PyQt5.QtCore import QThread, QAbstractTableModel, Qt, QVariant, pyqtSignal, QModelIndex, QFileInfo
from PyQt5.QtWidgets import QApplication, QGroupBox, QVBoxLayout, QGridLayout, QVBoxLayout, \
                            QTableView, QCheckBox, QSpinBox, QLabel, QMainWindow, \
                            QPushButton, QToolBar, QMenu, QFrame, QHeaderView, QAction, QRadioButton
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon

debug = 1

class OLA(QThread):
    universeChanged = pyqtSignal()
    universesList = pyqtSignal()
    """Separate Thread that run OLA client"""
    def __init__(self):
        QThread.__init__(self)
        self.client = None
        # start the thread
        self.start()
        if debug:
            print 'create a OLA client'

    def __del__(self):
        self.wait()

    def run(self):
        """the running thread"""
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
            if debug:
                print 'connected to OLA server'
            self.wrapper.Run()
        except OLADNotRunningException:
            if debug:
                print 'cannot connect to OLA'

    def stop(self):
        """stop the OLA client wrapper"""
        if self.client:
            self.wrapper.Stop()
            if debug:
                print 'connection to OLA is closed'


class UniverseModel(QAbstractTableModel):
    """List Model of a DMX universe (512 values 0/255)"""
    def __init__(self, parent):
        super(UniverseModel, self).__init__(parent)
        self.columns = 32
        self.rows = (512/self.columns)
        if int(self.rows)*self.columns < 512:
            self.rows = self.rows + 1
        self.dmx_list = []
        for row in range(self.rows):
            self.dmx_list.append([0 for i in range(self.columns)])
            if self.rows-1 == row:
                delta = self.columns * self.rows
                delta = delta - 512
                delta = self.columns - delta
                self.dmx_list[row] = self.dmx_list[row][:delta]
        self.parent = parent

    def rowCount(self, index=QModelIndex()):
        """return the size of the list"""
        return self.rows

    def columnCount(self, index=QModelIndex()):
        """return the number of columns per row"""
        return self.columns

    def data(self, index, role=Qt.DisplayRole):
        """return value for an index"""
        rows = index.row()
        columns = index.column()
        index_number = rows - 1
        index_number = index_number * columns
        index_number = index_number + columns
        if index.isValid():
            if role == Qt.DisplayRole:
                try:
                    value = self.dmx_list[rows][columns]
                    if value == 255:
                        value = 'FF'
                    elif value == 0:
                        value = ''
                    return QVariant(value)
                except IndexError:
                    if debug:
                        # these cells does not exists
                        print(rows,columns,'is out of dmx_list')
            elif role == Qt.BackgroundRole:
                try:
                    value =  self.dmx_list[rows][columns]
                    green = 255 - value
                    color = QColor(green,255,green)
                    return QBrush(color)
                except IndexError:
                    # these cells does not exists
                    return QVariant()
            elif role == Qt.FontRole:
                try:
                    font = QFont()
                    font.setFamily('Helvetica')
                    #font.setStretch('UltraCondensed')
                    font.setFixedPitch(True)
                    font.setPointSize(10)
                    return font
                except:
                    return QVariant()
            else:
                return QVariant()
        else:
            return QVariant()

    def new_frame(self, data):
        """receive the dmx_list when ola sends new data"""
        if debug:
        	print 'new frame received :', len(data), data
        # if data: does not work because the data list can be empty when fetching DMX
        if data != None:
            for index,value in enumerate(data):
                column = index%self.columnCount()
                row = int(index/self.columnCount())
                self.dmx_list[row][column] = value
                self.model_index = self.index(row, column)
                if value != self.model_index.data:
                    # yes : value has changed
                    self.setData(self.model_index, value)
                else:
                    pass
            # if value is 0, OLA does not send the value
            if len(data) < 512:
                for index in range(len(data),512):
                    column = index%self.columns
                    row = int(index/self.columns)
                    self.dmx_list[row][column] = 0
                    self.model_index = self.index(row, column)
                    if self.model_index.data != 0:
                        self.setData(self.model_index, 0)
            # this is send only once for a dmx_list
            # This is where the update is send to the GUI
            self.parent.ola.universeChanged.emit()


class Universe(QGroupBox):
    """docstring for Universe"""
    def __init__(self, parent, ola, universe=1):
        super(Universe, self).__init__()
        # make it available for the whole instance
        self.ola = ola
		# intialize variable used in ola_connect method
        self.old = None
        self.view = QTableView()
        self.model = UniverseModel(self)
        self.view.setModel(self.model)
        grid = QGridLayout()
        grid.addWidget(self.view,1, 0, 2, 10)
        self.settings = QLabel('Some Widgets to patch universes inputs & outputs')
        self.settings.setVisible(False)
        grid.addWidget(self.settings)
        # set up headers
        v_headers = QHeaderView(Qt.Vertical)
        self.view.setVerticalHeader(v_headers)
        h_headers = QHeaderView(Qt.Horizontal)
        self.view.setHorizontalHeader(h_headers)
        if debug : 
        	print 'how many lines : ', v_headers.count()
        	print 'how many columns : ', h_headers.count()
        # set up rows and columns
        for col in range(self.model.columnCount()):
            self.view.setColumnWidth(col, 28)
        for row in range(self.model.rowCount()):
            self.view.setRowHeight(row, 20)
        self.setLayout(grid)
        parent.vbox.addWidget(self)
        #parent.selector.valueChanged.connect(self.ola_connect)
        #parent.selector.setValue(universe)
        self.ola_connect(universe)
        if debug:
            print 'universe', universe, 'has been created'

    def ola_connect(self, new):
        if self.ola.client:
        	if new != self.old:
	            if self.old:
	                # unregister the previous universe (self.old)
	                if debug:
	                    print 'disconnect universe :', self.old
	                self.ola.client.RegisterUniverse(self.old, self.ola.client.UNREGISTER, self.model.new_frame)
	            # register the selected universe (new)
	            # ask about universe values, in case no new frame is sent
	            if debug:
	                print 'connect universe :', new
	            self.ola.client.RegisterUniverse(new, self.ola.client.REGISTER, self.model.new_frame)
	            self.ola.universeChanged.connect(self.model.layoutChanged.emit)
	            self.ola.client.FetchDmx(new, self.refresh)
	            self.old = new
	            return True
	        else:
	        	# ola wants to connect again to the universe it's already binding to
	        	if debug:
	        		# update dmx values
	        		#self.ola.client.FetchDmx(new, self.refresh)
	        		print 'universe already connected'
	        	return False
        else:
            return False

    def refresh(self, RequestStatus, universe, dmx_list):
    	if debug:
    		print 'refresh universe', universe
        self.model.new_frame(dmx_list)


class MainWindow(QMainWindow):
    """This is the main window"""
    def __init__(self):
        super(MainWindow, self).__init__()
		# create a vertical layout in a frame to add widgets
		# this might be done in a QToolbar
        frame = QFrame()
        self.vbox = QVBoxLayout(frame)
        self.setCentralWidget(frame)
        # create a button to connect to OLA server
        self.createLeftToolBar()
		# set up the window
        self.setWindowTitle("OLA test GUI")
        self.resize(1051, 400)
        self.move(0, 0)
        # initialize ola to be sure it exists
        self.ola = None
        if debug:
            print 'main window has been created'
        self.universes_list = None
        self.ola_create()
        sleep(0.1)
        if self.ola.client:
            self.ola.universesList.connect(self.update_universes_list)
            self.ola.client.FetchUniverses(self.universes)
        sleep(0.5)
        if self.universes_list:
            # if there is a universe, connect to the first one
            #universe_id = self.selectorLayout.itemAt(0).widget().text()
            #universe_id = int(universe_id)
            # Create the universe layout (view and model)
            self.universe = Universe(self, self.ola, self.universes_list[0].id)

    def debug_sw(self, state):
    	global debug
    	debug = state
    
    def createLeftToolBar(self):
        self.createActions()
        mytoolbar = QToolBar()
        # temporary debug UI toggle
        debug_UI = QCheckBox('Debug')
        global debug
        debug_UI.setChecked(debug)
        debug_UI.stateChanged.connect(self.debug_sw)
        mytoolbar.addWidget(debug_UI)
        mytoolbar.addSeparator()
        self.selectorMenu = QGroupBox()
        self.selectorLayout = QVBoxLayout()
        self.selectorMenu.setLayout(self.selectorLayout)
        new_universe = QPushButton('new universe')
        new_universe.released.connect(self.create_universe)
        mytoolbar.addWidget(new_universe)
        mytoolbar.addAction(self.settingsAct)
        mytoolbar.addAction(self.displayAct)
        mytoolbar.addWidget(self.selectorMenu)
        self.settingsAct.setVisible(True)
        self.displayAct.setVisible(False)
        mytoolbar.setMovable(False)
        mytoolbar.setFixedWidth(110)
        self.addToolBar(Qt.LeftToolBarArea, mytoolbar)
        self.toolbar = mytoolbar

    def createActions(self):
        """create all actions"""
        root = QFileInfo(__file__).absolutePath()

        self.settingsAct = QAction(QIcon(root + '/images/settings.svg'), "Settings", self,
                                  statusTip="Settings panel for the selected universe",
                                  triggered=self.openSettingsPanel)

        self.displayAct = QAction(QIcon(root + '/images/display.svg'),"Display", self,
                                  statusTip="Display value for the selected universe",
                                  triggered=self.openDisplayPanel)

    def openSettingsPanel(self):
        """switch to the settings editor"""
        if debug:
            print 'switch to the settings view'
        self.displayAct.setVisible(True)
        self.settingsAct.setVisible(False)
        self.universe.view.setVisible(False)
        self.universe.settings.setVisible(True)

    def openDisplayPanel(self):
        """switch to the universe display panel"""
        if debug:
            print 'switch to the display view'
        self.displayAct.setVisible(False)
        self.settingsAct.setVisible(True)
        self.universe.view.setVisible(True)
        self.universe.settings.setVisible(False)

    def create_universe(self):
        print 'TODO : create a new universe'

    def ola_create(self):
        # meke OLA wrapper running in parallel
        self.ola = OLA()

    def update_universes_list(self):
         for universe in self.universes_list:
            button = QRadioButton(str(universe.id))
            self.selectorLayout.addWidget(button)
            button.released.connect(self.choose_universe)

    def choose_universe(self, data=None):
        for i in range(self.selectorLayout.count()):
            if self.selectorLayout.itemAt(i).widget().isChecked():
                universe_id = self.selectorLayout.itemAt(i).widget().text()
                self.universe.ola_connect(int(universe_id))

    def universes(self, request, universes):
        # need to fetch universes to set range
        self.universes_list = universes
        self.ola.universesList.emit()

    def closeEvent(self, event):
        # why this is happenning twice?
        if self.ola:
            self.ola.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())