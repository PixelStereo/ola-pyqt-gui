
import sys
import getopt
import textwrap
from time import sleep
from random import randrange
from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException
from PyQt5.QtCore import QThread, QAbstractListModel, Qt, QVariant, pyqtSignal
from PyQt5.QtWidgets import QListView, QApplication, QGroupBox, QVBoxLayout, QPushButton, QSpinBox, QMainWindow, QFrame

universe_1 = [0 for i in range(512)]


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
            print 'connected to OLA server'
            self.wrapper.Run()
        except OLADNotRunningException:
            print 'CANNOT CONNECT TO OLA'

    def getclient(self):
        return self._client

    def stop(self):
        if self._client:
            self.wrapper.Stop()
            print 'connection to OLA is closed'

    def update(self, data):
        for index, value in enumerate(data):
            universe_1[index] = value
        self.universeChanged.emit()


class UniverseModel(QAbstractListModel):
    def __init__(self, parent=None):
        super(UniverseModel, self).__init__(parent)

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


class Universe(QGroupBox):
    """docstring for Universe"""
    def __init__(self, parent, ola, universe=1):
        super(Universe, self).__init__()
        self.selector = QSpinBox()
        self.selector.setRange(1,1)
        self.view = QListView()
        self.model = UniverseModel()
        self.view.setModel(self.model)
        vbox = QVBoxLayout()
        vbox.addWidget(self.selector)
        vbox.addWidget(self.view)
        self.setLayout(vbox)
        parent.vbox.addWidget(self)
        self.ola = ola
        self.old = None
        self.selector.valueChanged.connect(self.ola_connect)
        self.selector.setValue(1)
        self.ola_connect(1)

    def ola_connect(self, new):
        # NEXT :  HOW to unregister Universe??
        if self.ola.getclient():
            if self.old:
                # unregister the previous universe (self.old)
                self.ola.getclient().RegisterUniverse(self.old, self.ola.getclient().UNREGISTER, self.ola.update)
            # register the selected universe (new)
            self.ola.getclient().RegisterUniverse(new, self.ola.getclient().REGISTER, self.ola.update)
            self.ola.universeChanged.connect(self.model.layoutChanged.emit)
            self.old = new
            return True
        else:
            return False


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
        self.resize(480, 320)
        self.ola = None

    def ola_connect(self):
        print 'connecting to OLA server'
        # meke OLA wrapper running in parallel
        self.ola = OLA()
        # don't know why, but it seems to be necessary with QThread
        sleep(0.5)
        self.ola_client = self.ola.getclient()
        if self.ola_client:
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