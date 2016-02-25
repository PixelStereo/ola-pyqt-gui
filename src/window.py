#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main window handles :

main window (of course !)
Menus and all documents-related functions
such as new / open / save / save as…
"""

import os
import sys
# for development of pydular, use git version
#pydular_path = os.path.abspath('./../3rdparty/pydular')
#sys.path.append(pydular_path)

from universe import Universe

from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QSignalMapper, QPoint, QSize, QSettings, QFileInfo
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QMdiArea, \
                            QApplication, QMessageBox, QFileDialog, QWidget

import threading
import getopt
import textwrap
import sys
from ola.ClientWrapper import ClientWrapper

        


def NewData(data):
    print data

class MainWindow(QMainWindow):
    """This create the main window of the application"""
    def __init__(self):
        super(MainWindow, self).__init__()
        # remove close & maximize window buttons
        #self.setWindowFlags(Qt.CustomizeWindowHint|Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(1000, 666)
        #self.setMaximumSize(1000,666)
        self.mdiArea = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdiArea)

        self.mdiArea.subWindowActivated.connect(self.updateMenus)
        self.mdiArea.setViewMode(QMdiArea.TabbedView)

        self.windowMapper = QSignalMapper(self)
        self.windowMapper.mapped[QWidget].connect(self.setActiveSubWindow)

        self.child = None

        self.createActions()
        self.createMenus()
        self.createStatusBar()
        self.updateMenus()
        self.readSettings()
        self.setWindowTitle("OLA GUI")

        mytoolbar = QToolBar()
        #self.toolbar = self.addToolBar()
        mytoolbar.addAction(self.newAct)
        mytoolbar.addAction(self.openAct)
        mytoolbar.addAction(self.saveAct)
        mytoolbar.addAction(self.saveAsAct)
        mytoolbar.addSeparator()
        mytoolbar.addAction(self.outputsAct)
        mytoolbar.addAction(self.scenarioAct)
        self.scenarioAct.setVisible(False)
        mytoolbar.setMovable(False)
        mytoolbar.setFixedWidth(60)
        self.addToolBar(Qt.LeftToolBarArea, mytoolbar)

        client = self.OLA_client()
        from time import sleep
        sleep(0.1)
        client = client.getclient()
        self.client = client


    class OLA_client(threading.Thread):
        """docstring for OLAUniverseCallback"""
        def __init__(self):
            threading.Thread.__init__(self)
            self.start()

        def run(self):
            print 'run'
            # OLA
            wrapper = ClientWrapper()
            client = wrapper.Client()
            self.client = client
            print 'da' ,self.client
            wrapper.Run()


        def getclient(self):
            return self.client
        


    def closeEvent(self, scenario):
        """method called when the main window wants to be closed"""
        self.mdiArea.closeAllSubWindows()
        if self.mdiArea.currentSubWindow():
            scenario.ignore()
        else:
            self.writeSettings()
            scenario.accept()

    def newFile(self):
        """creates a new project"""
        child = self.createUniverse()
        child.newFile()
        child.show()
        self.child = child

    def open(self):
        """open a project"""
        fileName, _ = QFileDialog.getOpenFileName(self)
        if fileName:
            existing = self.findUniverse(fileName)
            if existing:
                self.mdiArea.setActiveSubWindow(existing)
                return

            child = self.createUniverse()
            if child.loadFile(fileName):
                self.statusBar().showMessage("File loaded", 2000)
                child.show()
            else:
                child.close()

    def save(self):
        """called when user save a project"""
        if self.activeUniverse() and self.activeUniverse().save():
            self.statusBar().showMessage("File saved", 2000)

    def saveAs(self):
        """called when user save AS a project"""
        if self.activeUniverse() and self.activeUniverse().saveAs():
            self.statusBar().showMessage("File saved", 2000)

    def openFolder(self):
        """called when user calls 'reveal in finder' function"""
        if self.activeUniverse() and self.activeUniverse().openFolder():
            self.statusBar().showMessage("File revealed in Finder", 2000)

    def about(self):
        """called when user wants to know a bit more on the app"""
        QMessageBox.about(self, "About MDI",
                          "<b>Lekture</b> is an OSC sequencer"
                          "This release is an alpha version."
                          "Don't use it in production !!")

    def updateMenus(self):
        """update menus"""
        hasUniverse = (self.activeUniverse() is not None)
        self.saveAct.setEnabled(hasUniverse)
        self.saveAsAct.setEnabled(hasUniverse)
        self.outputsAct.setEnabled(hasUniverse)
        self.scenarioAct.setEnabled(hasUniverse)
        self.openFolderAct.setEnabled(hasUniverse)
        self.closeAct.setEnabled(hasUniverse)
        self.closeAllAct.setEnabled(hasUniverse)
        self.nextAct.setEnabled(hasUniverse)
        self.previousAct.setEnabled(hasUniverse)
        self.separatorAct.setVisible(hasUniverse)

    def updateWindowMenu(self):
        """unpates menus on the window toolbar"""
        self.windowMenu.clear()
        self.windowMenu.addAction(self.closeAct)
        self.windowMenu.addAction(self.closeAllAct)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.nextAct)
        self.windowMenu.addAction(self.previousAct)
        self.windowMenu.addAction(self.separatorAct)

        windows = self.mdiArea.subWindowList()
        self.separatorAct.setVisible(len(windows) != 0)

        for i, window in enumerate(windows):
            child = window.widget()

            text = "%d %s" % (i + 1, child.userFriendlyCurrentFile())
            if i < 9:
                text = '&' + text

            action = self.windowMenu.addAction(text)
            action.setCheckable(True)
            action.setChecked(child is self.activeUniverse())
            action.triggered.connect(self.windowMapper.map)
            self.windowMapper.setMapping(action, window)

    def createUniverse(self):
        """create a new project"""
        child = Universe()
        self.client.RegisterUniverse(1, self.client.REGISTER, child.update)
        self.mdiArea.addSubWindow(child)
        self.child = child
        return child

    def createActions(self):
        """create all actions"""
        self.newAct = QAction("&New", self,
                              shortcut=QKeySequence.New, statusTip="Create a new file",
                              triggered=self.newFile)

        self.openAct = QAction("&Open...", self,
                               shortcut=QKeySequence.Open, statusTip="Open an existing file",
                               triggered=self.open)

        self.saveAct = QAction("&Save", self,
                               shortcut=QKeySequence.Save,
                               statusTip="Save the document to disk", triggered=self.save)

        self.saveAsAct = QAction("Save &As...", self,
                                 shortcut=QKeySequence.SaveAs,
                                 statusTip="Save the document under a new name",
                                 triggered=self.saveAs)

        self.openFolderAct = QAction("Open Project Folder", self,
                                     statusTip="Reveal Project in Finder",
                                     triggered=self.openFolder)

        self.exitAct = QAction("E&xit", self, shortcut=QKeySequence.Quit,
                               statusTip="Exit the application",
                               triggered=QApplication.instance().closeAllWindows)

        self.closeAct = QAction("Cl&ose", self,
                                statusTip="Close the active window",
                                triggered=self.mdiArea.closeActiveSubWindow)

        self.outputsAct = QAction("Outputs", self,
                                  statusTip="Open the outputs panel",
                                  triggered=self.openOutputsPanel)

        self.scenarioAct = QAction("Scenario", self,
                                   statusTip="Open the scenario panel",
                                   triggered=self.openScenarioPanel)

        self.closeAllAct = QAction("Close &All", self,
                                   statusTip="Close all the windows",
                                   triggered=self.mdiArea.closeAllSubWindows)

        self.nextAct = QAction("Ne&xt", self, shortcut=QKeySequence.NextChild,
                               statusTip="Move the focus to the next window",
                               triggered=self.mdiArea.activateNextSubWindow)

        self.previousAct = QAction("Pre&vious", self,
                                   shortcut=QKeySequence.PreviousChild,
                                   statusTip="Move the focus to the previous window",
                                   triggered=self.mdiArea.activatePreviousSubWindow)

        self.separatorAct = QAction(self)
        self.separatorAct.setSeparator(True)

        self.aboutAct = QAction("&About", self,
                                statusTip="Show the application's About box",
                                triggered=self.about)

    def createMenus(self):
        """create all menus"""
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.openFolderAct)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.outputsAct)
        self.viewMenu.addAction(self.scenarioAct)

        self.windowMenu = self.menuBar().addMenu("&Window")
        self.updateWindowMenu()
        self.windowMenu.aboutToShow.connect(self.updateWindowMenu)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def createStatusBar(self):
        """create the status bar"""
        self.statusBar().showMessage("Ready")

    def readSettings(self):
        """read the settings"""
        settings = QSettings('Pixel Stereo', 'lekture')
        pos = settings.value('pos', QPoint(200, 200))
        size = settings.value('size', QSize(1000, 650))
        self.move(pos)
        self.resize(size)

    def writeSettings(self):
        """write settings"""
        settings = QSettings('Pixel Stereo', 'lekture')
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())

    def activeUniverse(self):
        """return the active project object"""
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        else:
            return None

    def findUniverse(self, fileName):
        """return the project"""
        canonicalFilePath = QFileInfo(fileName).canonicalFilePath()

        for window in self.mdiArea.subWindowList():
            if window.widget().currentFile() == canonicalFilePath:
                return window
        return None

    def setActiveSubWindow(self, window):
        """set the active sub window"""
        if window:
            self.mdiArea.setActiveSubWindow(window)

    def openOutputsPanel(self):
        """switch to the outputs editor"""
        if self.child:
            project = self.activeUniverse()
            project.scenario_group.setVisible(False)
            project.outputs_group.setVisible(True)
            self.scenarioAct.setVisible(True)
            self.outputsAct.setVisible(False)

    def openScenarioPanel(self):
        """switch to the scenario editors"""
        if self.child:
            project = self.activeUniverse()
            project.scenario_output_index_range()
            project.scenario_out_fill()
            project.outputs_group.setVisible(False)
            project.scenario_group.setVisible(True)
            self.scenarioAct.setVisible(False)
            self.outputsAct.setVisible(True)
