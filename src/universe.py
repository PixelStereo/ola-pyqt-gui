#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Child module hosts a project-related class"""

#from pydular import project
#from pydular.functions import checkType


import sys
import threading
import subprocess
from PyQt5.QtCore import Qt, QModelIndex, QFileInfo, QFile, QPoint
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QApplication, QMenu, \
                            QMessageBox, QTableWidgetItem, QGroupBox, QGridLayout


import getopt
import textwrap
import sys
from ola.ClientWrapper import ClientWrapper

class Document(object):
    """docstring for Document"""
    def __init__(self, arg):
        super(Document, self).__init__()
        self.arg = arg
        self.modified = True

    def contentsChanged(self):
        pass

    def isModified(self):
        return self.modified

    def setModified(self):
        pass


class Universe(QGroupBox, QModelIndex):
    """This is the universe class"""
    sequenceNumber = 1

    def __init__(self):
        super(Universe, self).__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.isUntitled = True
        # I must change all 'document' class reference to 'project' class…
        # so I need to enhance project with modify flags and signals
        self.document = Document('unknown')
        self.listen(1)

    def listen(self, universe_index):
        """shortcut to run thread"""
        self.Listen(self, universe_index)


    class Listen(threading.Thread):
        """Instanciate a thread for Playing a scenario
        Allow to start twice or more each scenario in the same time"""
        def __init__(self, solo,universe_index):
            threading.Thread.__init__(self)
            self.universe_index = universe_index
            self.start()

        def run(self):
            """play a scenario from the beginning
            play an scenario
            Started from the first event if an index has not been provided"""
            universe = self.universe_index

            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
            self.client.RegisterUniverse(universe, self.client.REGISTER, self.NewData)
            self.wrapper.Run()

        def NewData(self, data):
            print(data)

    def newFile(self):
        """create a new project"""
        self.isUntitled = True
        self.curFile = "project %d" % Universe.sequenceNumber
        Universe.sequenceNumber += 1
        self.setWindowTitle(self.curFile + '[*]')

        #self.project.name = self.curFile
        #if not self.project.path:
        #    self.project_path.setText('Project has not been saved')
        #self.document().contentsChanged.connect(self.documentWasModified)

    def loadFile(self, fileName):
        """open an existing project file"""
        file = QFile(fileName)
        if not file.open(QFile.ReadOnly | QFile.Text):
            QMessageBox.warning(self, "MDI",
                                "Cannot read file %s:\n%s." % (fileName, file.errorString()))
            return False
        QApplication.setOverrideCursor(Qt.WaitCursor)
        # read a project and create scenario
        self.project.read(fileName)
        #self.outputs_refresh()
        self.scenario_list_refresh()
        self.project_display()
        self.protocol_display()
        QApplication.restoreOverrideCursor()
        self.setCurrentFile(fileName)
        #self.document().contentsChanged.connect(self.documentWasModified)
        return True

    def save(self):
        """save a project"""
        if self.isUntitled:
            return self.saveAs()
        else:
            return self.saveFile(self.curFile)

    def saveAs(self):
        """save as a project"""
        fileName, _ = QFileDialog.getSaveFileName(self, "Save As", self.curFile)
        if not fileName:
            return False
        else:
            fileName = fileName + '.json'
        return self.saveFile(fileName)

    def saveFile(self, fileName=None):
        """ save project"""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if fileName:
            self.project.write(fileName)
            self.project_path.setText(fileName)
            self.project.path = fileName
        else:
            self.project.write()
            self.project_path.setText(self.project.path)
        QApplication.restoreOverrideCursor()
        self.setCurrentFile(fileName)
        return True

    def openFolder(self):
        """ open project directory"""
        if self.project.path:
            path = self.project.path
            if sys.platform == 'darwin':
                subprocess.check_call(["open", "-R", path])
            elif sys.platform == 'win32':
                subprocess.check_call(['explorer', path])
            elif sys.platform.startswith('linux'):
                subprocess.check_call(['xdg-open', '--', path])
            return True
        else:
            return False

    def project_display(self):
        """display a project"""
        self.project_author.setText(self.project.author)
        self.project_version.setText(self.project.version)
        self.project_path.setText(self.project.path)

    def userFriendlyCurrentFile(self):
        """ return user friendly current file name (without path"""
        return self.strippedName(self.curFile)

    def currentFile(self):
        """ return current file object"""
        return self.curFile

    def closeEvent(self, event):
        """call when project is about to be closed"""
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def documentWasModified(self):
        """called when a modification happened on the document"""
        self.setWindowModified(self.document().isModified())

    def maybeSave(self):
        """return the modified state of the project"""
        if self.document.isModified():
            ret = QMessageBox.warning(self, "MDI",
                                      "'%s' has been modified.\nDo you want to save your "
                                      "changes?" % self.userFriendlyCurrentFile(),
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if ret == QMessageBox.Save:
                return self.save()

            if ret == QMessageBox.Cancel:
                return False

        return True

    def setCurrentFile(self, fileName):
        """set a current file"""
        self.curFile = QFileInfo(fileName).canonicalFilePath()
        self.isUntitled = False
        #self.document().setModified(False)
        self.setWindowModified(False)
        self.setWindowTitle(self.userFriendlyCurrentFile() + "[*]")

    def strippedName(self, fullFileName):
        """return the stripped name of the project (without the path)"""
        return QFileInfo(fullFileName). baseName()

