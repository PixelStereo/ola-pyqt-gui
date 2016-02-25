#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Child module hosts a project-related class"""

#from pydular import project
#from pydular.functions import checkType


import sys
import threading
import subprocess

from PyQt5.QtCore import Qt, QVariant, QModelIndex, QFileInfo, QPoint, QFile, QAbstractTableModel
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QMenu, QGridLayout, QTableView, \
                            QMessageBox, QTableWidgetItem, QGroupBox, QApplication,QHBoxLayout
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


class TableModel(QAbstractTableModel): 
    def __init__(self, parent=None, *args): 
        super(TableModel, self).__init__()
        self.datatable = [[],[]]
        self.columns = 12
        self.rows = (512/self.columns)+1

    def update(self, dataIn):
        print 'Updating Model'
        self.datatable = dataIn
        print 'Datatable : {0}'.format(self.datatable)

    def rowCount(self, parent=QModelIndex()):
        return self.rows

    def columnCount(self, parent=QModelIndex()):
        return self.columns

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            i = index.row()
            j = index.column()
            #print 'here', self.datatable
            return '{0}'.format(self.datatable.iget_value(i, j))
        else:
            return QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled

class Universe(QGroupBox):
    """This is the universe class"""
    sequenceNumber = 1

    def __init__(self):
        super(Universe, self).__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.isUntitled = True
        # I must change all 'document' class reference to 'project' class…
        # so I need to enhance project with modify flags and signals
        self.document = Document('unknown')
        self.universe_index = 1
        """self.universe_group_box = QGroupBox()
        universe_layout = QHBoxLayout()
        self.universe_display = QTableView()
        universe_layout.addWidget(self.universe_display)
        self.universe_group_box.setLayout(universe_layout)   
        # Create the main layout
        self.mainLayout = QGridLayout()
        # Integrate the layout previously created
        self.mainLayout.addWidget(self.universe_group_box)
        # Integrate main layout to the main window
        self.setLayout(self.mainLayout)
        # create the model
        #data = [0,0,0]
        universe_model = TableModel()
        self.universe_model = universe_model
        print 'created model'
        #universe_model.update(data)
        self.universe_display.setModel(universe_model)"""

    def update(self, data):
        print data

    def NewData(self, data):
        print 'print data' ,  data
        #self.universe_model.update(data)
        """print len(data)
        for i in data:
            dimmer = data.index(i)+1
            value = i
            #print dimmer, ':', value
            cooked = str(dimmer) + ':' + str(value)
            column = 512%12
            row = int(512/12)
            #self.universe_display.setItem(row, column, QTableWidgetItem(cooked))"""


    def newFile(self):
        """create a new project"""
        self.isUntitled = True
        self.curFile = "universe %d" % Universe.sequenceNumber
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

