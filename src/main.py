#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main module for the app
It create QApplication and QMainWindow
"""
# import from python standard libs
import os
import sys
import signal
import getopt
import textwrap
from time import sleep
from random import randrange
# import from PyQt5 libs
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QVariant, QModelIndex, QFileInfo
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QCheckBox, QMainWindow, \
                            QAction, QListView, QPushButton, QToolBar, QFrame
# import from current module
from Ola import OLA
from universe import Universe
from universe import UniversesModel
from patch import PatchPanel
try:
    # stylesheet
    import qdarkstyle
except:
    pass

debug = 1


class MainWindow(QMainWindow):
    """
    This is the main window
    """
    def __init__(self):
        super(MainWindow, self).__init__()
        # initialize to None just to know if a universe has ever been seleted
        self.universe = None
        self.settings = None
		# create a vertical layout in a frame to add widgets
        frame = QFrame()
        self.vbox = QVBoxLayout(frame)
        self.setCentralWidget(frame)
        # create actions
        self.create_actions()
        # create a ToolBar
        self.create_toolBar()
		# set up the window
        self.setWindowTitle("OLA GUI")
        self.setFixedWidth(1086)
        self.setFixedHeight(480)
        self.move(0, 0)
        if debug:
            print 'main window created'
            print 'make a ola_connection request'
        # When creating the app, there is no universe selected
        self.universe_selected = None
        # display a message to say init is over
        self.status("Ready", 0)
        # Try tp create OLA client
        self.create_ola()
        # Show the current main window
        self.show()

    def status(self, message, timeout=2000):
        """
        Display a message on the Status bar
        """
        if timeout == 0:
            timeout = 999999999
        self.statusBar().showMessage(message, timeout)

    def create_actions(self):
        self.view_dmxList = QAction("Monitor", self,
                              shortcut=QKeySequence.New, statusTip="Monitor DMX values",
                              triggered=self.switch2dmxList)
        self.view_patch = QAction("Patch", self,
                              shortcut=QKeySequence.New, statusTip="Patch in/out ports",
                              triggered=self.switch2patch)
        self.new_universe = QAction("New Universe", self,
                              shortcut=QKeySequence.New, statusTip="Create a new universe",
                              triggered=self.create_universe)
        self.record_universe = QAction("RegisterUniverse", self,
                              shortcut=QKeySequence.New, statusTip="Register the new universe",
                              triggered=self.register_universe)

    def create_toolBar(self):
        """
        create the toolbar of the app
        it contains debug toggle, ola_connection toggle and universes_list
        """
        mytoolbar = QToolBar()
        # DMX values view
        mytoolbar.addAction(self.view_dmxList)
        self.view_dmxList.setVisible(False)
        # patch ports view
        mytoolbar.addAction(self.view_patch)
        self.view_patch.setVisible(True)
        self.view_patch.setEnabled(False)
        # new universe action
        mytoolbar.addAction(self.new_universe)
        # register universe action
        mytoolbar.addAction(self.record_universe)
        self.record_universe.setVisible(False)
        """
        self.devices = QPushButton('Devices')
        self.devices.setCheckable(True)
        self.devices.toggled.connect(self.switch_view)
        self.devices.setEnabled(False)
        self.record_universe = QPushButton('Save this new universe')
        self.record_universe.hide()
        self.record_universe.released.connect(self.register_universe)
        # create a button to add a new universe
        self.new_universe = QPushButton('new universe')
        self.new_universe.released.connect(self.create_universe)
        mytoolbar.addSeparator()
        mytoolbar.addWidget(self.devices)
        mytoolbar.addWidget(self.new_universe)
        mytoolbar.addWidget(self.record_universe)"""
        mytoolbar.setMovable(False)
        mytoolbar.setFixedWidth(110)
        self.addToolBar(Qt.LeftToolBarArea, mytoolbar)
        self.toolbar = mytoolbar

    def register_universe(self):
        """
        Record a new universe (button pressed)
        """
        if debug:
            print 'universe recorded'
        self.universe.id.setReadOnly(True)
        self.record_universe.setVisible(False)
        self.new_universe.setVisible(True)

    def create_settings(self):
        self.settings = PatchPanel(self)
        self.universe.grid.addWidget(self.settings,2, 0, 18, 10)
        self.ola.devicesList.connect(self.settings.devices_model.layoutChanged.emit)
        self.ola.inPortsList.connect(self.settings.inputs_model.layoutChanged.emit)
        self.ola.outPortsList.connect(self.settings.outputs_model.layoutChanged.emit)
        self.settings.setVisible(False)

    def switch2dmxList(self):
        """
        switch the view between universe view or devices view
        • universe view displays universe attributes (name, id and merge_mode) and DMX values
        • devices view displays devices attached to the universes (input and ouput ports)
        """
        self.universe.view.setVisible(True)
        self.settings.setVisible(False)
        self.view_patch.setVisible(True)
        self.view_dmxList.setVisible(False)

    def switch2patch(self):
        """
        switch the view between universe view or devices view
        • universe view displays universe attributes (name, id and merge_mode) and DMX values
        • devices view displays devices attached to the universes (input and ouput ports)
        """
        self.universe.view.setVisible(False)
        self.settings.setVisible(True)
        self.settings.display_ports(self.universe_selected)
        self.view_dmxList.setVisible(True)
        self.view_patch.setVisible(False)

    def create_universe(self):
        """
        create a new universe
        """
        if not self.universe:
            self.universe_mv_create()
            if debug:
                print 'create universe model and view'
        if debug:
            print 'make universe.id editable'
        self.universe.id.setReadOnly(False)
        self.new_universe.setVisible(False)
        self.record_universe.setVisible(True)
        # make patch panel active
        #self.devices.setChecked(True)

    def create_ola(self):
        """
        create the ola object (both server and client)
        Called when app is launched.
        """
        # create a OLA object (both server and client)
        ola = OLA()
        sleep(0.2)
        if ola.client:
            self.ola = ola
            self.status("connected to OLA", 0)
            # create the panel to display universe list
            self.create_universeList_panel()
            # please update universes list
            self.universes_refresh()
        else:
            self.status("can't connect to OLA. Is it running?", 0)
            # quit the app if no OLA server
            quit()

    def universes_refresh(self):
        """
        refresh the universes list.
        This method is just a link between the button from the toolbar and the ola_client
        """
        if debug:
            print 'refresh universe list'
        self.ola.client.FetchUniverses(self.list_model.update_universes_list)

    def create_universeList_panel(self):
        """
        create the panel with a qlistview to display universes list
        Called only once on MainWindow creation
        """
        self.toolbar.addSeparator()
        model = UniversesModel(self)
        self.list_model = model
        self.list_view = QListView()
        self.list_view.setModel(model)
        self.toolbar.addWidget(self.list_view)
        self.ola.universesList.connect(self.list_model.layoutChanged.emit)
        # Universe Selected Change
        self.list_view.selectionModel().selectionChanged.connect(self.universe_selection_changed)

    def universe_selection_changed(self, universe):
        """
        Universe Selection has changed
        This method will display Universe attributes
        such as Id, Name, MergeMode and dmx_list
        """
        row = universe.indexes()[0].row()
        universe = universe.indexes()[0].model().object(row)
        if not self.universe:
            # there is no universe interface created. Please do it
            self.universe_mv_create()
        # Fill in the universe_selected variable
        self.universe_selected = universe
        if debug:
            print 'selected universe :', universe
        self.universe.selection_changed(self.universe_selected)

    def universe_mv_create(self):
        """
        Create model and view for a universe
        """
        if debug:
            print 'create model and view for universe'
        # create the universe model
        self.universe = Universe(self)
        # create the patch model and view
        self.create_settings()
        self.view_patch.setVisible(True)
        self.view_patch.setEnabled(True)

    def closeEvent(self, event):
        """
        Call when the app is about to be closed
        """
        # why this is happenning twice?
        if self.ola:
            if self.ola.stop():
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    # create the current App
    app = QApplication(sys.argv)
    root = QFileInfo(__file__).absolutePath()
    path = root+'/icon/icon.png'
    app.setWindowIcon(QIcon(path))
    try:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    except:
        pass
    # create the Main Window and display it
    window = MainWindow()
    sys.exit(app.exec_())
