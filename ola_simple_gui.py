#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
import textwrap
from time import sleep
from random import randrange
from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException
from PyQt5.QtCore import QThread, QAbstractTableModel, Qt, QVariant, pyqtSignal, QModelIndex
from PyQt5.QtWidgets import QTableView, QApplication, QGroupBox, QVBoxLayout, QGridLayout, QPushButton, QSpinBox, QLabel, QMainWindow, QFrame, QHeaderView
from PyQt5.QtGui import QColor, QBrush, QFont

class OLA(QThread):
    universeChanged = pyqtSignal()
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
            print 'new frame :', len(data), data
        if data:
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
        self.universe_label = QLabel('Universe')
        self.selector = QSpinBox()
        self.selector.setRange(1,2)
        self.view = QTableView()
        self.model = UniverseModel(self)
        self.view.setModel(self.model)
        # set up rows and columns
        for col in range(self.model.columnCount()):
            self.view.setColumnWidth(col, 30)
        for row in range(self.model.rowCount()):
            self.view.setRowHeight(row, 20)
        # set up headers
        dimmers_view = QHeaderView(Qt.Vertical)
        self.view.setVerticalHeader(dimmers_view)
        
        grid = QGridLayout()
        grid.addWidget(self.universe_label, 0, 0)
        grid.addWidget(self.selector, 0, 1)
        grid.addWidget(self.view,1, 0, 2, 10)
        self.setLayout(grid)
        parent.vbox.addWidget(self)
        self.ola = ola
        self.old = None
        self.selector.valueChanged.connect(self.ola_connect)
        self.selector.setValue(1)
        self.ola_connect(1)
        if debug:
            print 'new universe has been created'

    def ola_connect(self, new):
        if self.ola.client:
            if self.old:
                # unregister the previous universe (self.old)
                if debug:
                    print 'disconnect universe :', old
                self.ola.client.RegisterUniverse(self.old, self.ola.client.UNREGISTER, self.model.new_frame)
            # register the selected universe (new)
            # ask about universe values, in case no new frame is sent
            if debug:
                print 'connect universe :', new
            self.ola.client.FetchDmx(new, self.refresh)
            self.ola.client.RegisterUniverse(new, self.ola.client.REGISTER, self.model.new_frame)
            self.ola.universeChanged.connect(self.model.layoutChanged.emit)
            self.old = new
            return True
        else:
            return False

    def refresh(self, RequestStatus, universe, dmx_list):
        self.model.new_frame(dmx_list)

class MainWindow(QMainWindow):
    """This is the main window"""
    def __init__(self):
        super(MainWindow, self).__init__()
        # create a button to connect to OLA server
        self.ola_switch = QPushButton('Connect to OLA server')
        self.ola_switch.released.connect(self.ola_connect)
        # create a vertical layout and add widgets
        frame = QFrame()
        self.vbox = QVBoxLayout(frame)
        self.vbox.addWidget(self.ola_switch)
        # set the layout on the groupbox
        self.setCentralWidget(frame)
        self.setWindowTitle("OLA test GUI")
        self.resize(1050, 600)
        self.move(0, 0)
        self.ola = None
        if debug:
            print 'main window has been created'

    def ola_connect(self):
        if debug:
            print 'connecting to OLA server'
        # meke OLA wrapper running in parallel
        self.ola = OLA()
        # don't know why, but it seems to be necessary with QThread
        sleep(0.5)
        if self.ola.client:
            self.ola_switch.setVisible(False)
            # Create the universe layout (view and model)
            self.universe = Universe(self, self.ola, 1)

    def closeEvent(self, event):
        # why this is happenning twice?
        if self.ola:
            self.ola.stop()



if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = MainWindow()
  window.show()
  sys.exit(app.exec_())