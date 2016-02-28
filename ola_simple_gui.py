from random import randrange
from time import sleep
from sys import argv, exit
from PyQt5.QtCore import QThread, QAbstractListModel, Qt, QVariant, pyqtSignal
from PyQt5.QtWidgets import QListView, QApplication, QGroupBox, QVBoxLayout, QCheckBox

universe_1 = [0 for i in range(512)]


import getopt
import textwrap
import sys
from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException


class OLA(QThread):
    universeChanged = pyqtSignal()
    """docstring for OLAUniverseCallback"""
    def __init__(self):
        QThread.__init__(self)
        self._client = None
        self.start()

    def __del__(self):
        self.wait()

    def run(self):
        # OLA
        try:
            self.wrapper = ClientWrapper()
            client = self.wrapper.Client()
            self._client = client
            self.wrapper.Run()
            print 'CONNECTED TO OLA'
        except OLADNotRunningException:
            print 'CANNOT CONNECT TO OLA'

    def getclient(self):
        return self._client

    def stop(self):
        if self._client:
            self.wrapper.Stop()

    def update(self, data):
        for index, value in enumerate(data):
            universe_1[index] = value
        self.universeChanged.emit()

class Universe(QAbstractListModel):
    def __init__(self, parent=None):
        super(Universe, self).__init__(parent)

    def rowCount(self, index):
        return len(universe_1)

    def data(self, index, role=Qt.DisplayRole):
        index = index.row()
        if role == Qt.DisplayRole:
            try:
                return universe_1[index]
            except IndexError:
                return QVariant()
        return QVariant()


class Viewer(QGroupBox):
    def __init__(self):
        super(Viewer, self).__init__()
        # create button and list_view
        self.ola_switch = QCheckBox('ola connection')
        self.ola_switch.setCheckable(True)
        self.list_view = QListView()
        # create a vertical layout and add widgets
        vbox = QVBoxLayout()
        vbox.addWidget(self.ola_switch)
        vbox.addWidget(self.list_view)
        # Model and View setup
        self.model = Universe()
        self.list_view.setModel(self.model)
        # meke a process running in parallel 
        self.ola = OLA()
        from time import sleep
        sleep(0.5)
        self.ola_client = self.ola.getclient()
        self.ola_switch.stateChanged.connect(self.ola_connect)
        # set the layout on the groupbox
        vbox.addStretch(1)
        self.setLayout(vbox)

    def ola_connect(self, state):
        if state:
            if self.ola_client:
                self.ola_switch.setChecked(True)
                self.ola_client.RegisterUniverse(1, self.ola_client.REGISTER, self.ola.update)
                self.ola.universeChanged.connect(self.model.layoutChanged.emit)
        else:
            # HOW to unregister Universe??
            pass


if __name__ == "__main__":
  app = QApplication(argv)
  group_widget = Viewer()
  group_widget.show()
  exit(app.exec_())