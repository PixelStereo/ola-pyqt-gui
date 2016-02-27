#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Child module hosts a project-related class"""

import sys
import threading
import subprocess
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt, QVariant, QModelIndex, QFileInfo, QPoint, QFile, QAbstractTableModel, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QMenu, QGridLayout, QTableView
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QGroupBox, QApplication,QHBoxLayout
import getopt
import textwrap
import sys

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
    dmx_changed = pyqtSignal()
    def __init__(self, parent=None, *args): 
        super(TableModel, self).__init__()  
        self.columns = 10
        self.rows = (512/self.columns)+1
        self.datatable = []
        for row in range(self.rows):
            self.datatable.append([0 for i in range(self.columns)])
            if self.rows-1 == row:
                delta = self.columns * self.rows
                delta = delta - 512
                delta = self.columns - delta
                self.datatable[row] = self.datatable[row][:delta]



    def update(self, dataIn):
        for index,value in enumerate(dataIn):
            column = index%self.columns
            row = int(index/self.columns)
            self.datatable[row][column] = value
            model_index = self.index(row, column)
            if value != model_index.data:
                # yes : value has changed
                self.setData(model_index, value)
                self.dmx_changed.emit()
            else:
                pass
        # if value is 0, OLA does not send the value
        if len(dataIn) < 512:
            for index in range(len(dataIn),512):
                column = index%self.columns
                row = int(index/self.columns)
                self.datatable[row][column] = 0
                model_index = self.index(row, column)
                if model_index.data != 0:
                    self.setData(model_index, 0)

    def rowCount(self, parent=QModelIndex()):
        return self.rows

    def columnCount(self, parent=QModelIndex()):
        return self.columns

    def data(self, index, role=Qt.DisplayRole):
        i = index.row()
        j = index.column()
        index_number = i - 1
        index_number = index_number * j
        index_number = index_number + j
        if index.isValid():
            if role == Qt.DisplayRole:
                try:
                    return QVariant(self.datatable[i][j])
                except IndexError:
                    # these cells does not exists
                    print(i,j,'is out of datatable')
            elif role == Qt.BackgroundRole:
                i = index.row()
                j = index.column()
                try:
                    value =  self.datatable[i][j]
                    green = 255 - value
                    color = QColor(green,255,green)
                    return QBrush(color)
                except IndexError:
                    # these cells does not exists
                    return QVariant()
            else:
                return QVariant()
        else:
            return QVariant()

    def flags(self, index):
        itemFlags = super(TableModel, self).flags(index)
        if index.column() != 0:
            return itemFlags | Qt.ItemIsEditable
        return itemFlags ^ Qt.ItemIsEditable #  First column not editable

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
        self.universe_group_box = QGroupBox()
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
        #universe_model.update(data)
        self.universe_display.setModel(universe_model)

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

