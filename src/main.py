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
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QVariant, QModelIndex, QFileInfo
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QCheckBox, QMainWindow, QListView, QPushButton, QToolBar, QFrame
# import from current module
from Ola import OLA
from universe import Universe
from universe import UniversesModel
from patch import PatchPanel
# stylesheet
#import qdarkstyle

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
        # create a ToolBar
        self.create_toolBar()
		# set up the window
        self.setWindowTitle("OLA GUI")
        self.setFixedWidth(1086)
        self.setFixedHeight(459)
        self.move(0, 0)
        # initialize ola to be sure it exists
        self.ola = None
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

    def switch_view(self, view):
        """
        switch the view between universe view or devices view
        • universe view displays universe attributes (name, id and merge_mode) and DMX values
        • devices view displays devices attached to the universes (input and ouput ports)
        """
    	if view:
            self.devices.setText('Universe')
            self.universe.setVisible(False)
            self.settings.setVisible(True)
            self.settings.display_ports(self.universe_selected)
        else:
            self.devices.setText('Settings')
            self.universe.setVisible(True)
            self.settings.setVisible(False)

    def status(self, message, timeout=2000):
        """
        Display a message on the Status bar
        """
        if timeout == 0:
            timeout = 999999999
        self.statusBar().showMessage(message, timeout)

    def create_toolBar(self):
        """
        create the toolbar of the app
        it contains debug toggle, ola_connection toggle and universes_list
        """
        mytoolbar = QToolBar()
        # temporary debug UI toggle
        self.devices = QPushButton('Devices')
        self.devices.setCheckable(True)
        self.devices.toggled.connect(self.switch_view)
        self.devices.setEnabled(False)
        mytoolbar.addWidget(self.devices)
        mytoolbar.setMovable(False)
        mytoolbar.setFixedWidth(110)
        self.addToolBar(Qt.LeftToolBarArea, mytoolbar)
        self.toolbar = mytoolbar

    def create_settings(self):
        self.settings = PatchPanel(self)
        self.ola.devicesList.connect(self.settings.devices_model.layoutChanged.emit)
        self.settings.setVisible(False)

    def create_universe(self):
        """
        create a new universe
        """
        print 'TODO : create a new universe'

    def create_ola(self):
        """
        create the ola client. Called when app is launched.
        If olad is not running at this time,
        """
        # check if there is not already a OLA client
        if not self.ola:
            # create a OLA client
            ola = OLA()
            sleep(0.1)
            if ola.client:
                self.ola = ola
                self.status("connected to OLA")
                # create a button to add a new universe
                new_universe = QPushButton('new universe')
                new_universe.released.connect(self.create_universe)
                self.toolbar.addWidget(new_universe)
                refresh_universes = QPushButton('refresh list')
                self.toolbar.addWidget(refresh_universes)
                # create the panel to display universe list
                self.create_universe_panel()
                # please update universes list
                self.universes_refresh()
                refresh_universes.released.connect(self.universes_refresh)
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

    def create_universe_panel(self):
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
            # MAYBE WE CAN DO THIS WHEN CREATING THE MAIN WINDOW?
            self.universe = Universe(self)
            self.create_settings()
            self.devices.setEnabled(True)
        # Fill in the universe_selected variable
        self.universe_selected = universe
        if debug:
            print 'selected universe :', universe
        self.universe.selection_changed(self.universe_selected)

    def closeEvent(self, event):
        """
        Called when app is about to closed
        """
        # why this is happenning twice?
        if self.ola:
            self.ola.stop()


if __name__ == "__main__":
    # create the current App
    app = QApplication(sys.argv)
    root = QFileInfo(__file__).absolutePath()
    path = root+'/icon/icon.png'
    app.setWindowIcon(QIcon(path))
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    # create the Main Window and display it
    window = MainWindow()
    sys.exit(app.exec_())
