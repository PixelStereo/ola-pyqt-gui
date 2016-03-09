#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Patch Window used to display available devices
Select a device will allow you to patch its port(s)
"""
import sys
from time import sleep
# import from PyQt5 libs
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QVariant, QModelIndex, QFileInfo, QAbstractListModel
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QCheckBox, QListView, QLabel
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QMenu, QWidgetAction
# import from current module
from Ola import OLA
from ola.OlaClient import Universe as OlaUniverse
from universe import Universe
from universe import UniversesModel

debug = 1

client = None

class DeviceList(QAbstractListModel):
    """Model for a port list"""
    def __init__(self,):
        super(DeviceList, self).__init__()
        self.devices = []

    def rowCount(self, index):
        return len(self.devices)

    def object(self, row):
        """
        return the port object for a given row
        """   
        return  self.devices[row]
        
    def data(self, index, role=Qt.DisplayRole):
        """
        return the name of the port
        """
        if index.isValid():
            row = index.row()
            if role == Qt.DisplayRole:
                try:
                    value = self.devices[row].name
                    return QVariant(value)
                except IndexError:
                    if debug:
                        # these cells does not exists
                        print(row, 'is out of port list')
                        return QVariant()
            else:
                return QVariant()
        else:
            return QVariant()


class PortList(QAbstractListModel):
    """Model for a port list"""
    def __init__(self,):
        super(PortList, self).__init__()
        self.ports = []

    def rowCount(self, index):
        return len(self.ports)

    def object(self, row):
        """
        return the port object for a given row
        """   
        return  self.ports[row]
        
    def data(self, index, role=Qt.DisplayRole):
        """
        return the name of the port
        """
        if index.isValid():
            row = index.row()
            port = self.ports[row]
            if role == Qt.DisplayRole:
                try:
                    rdm = port.supports_rdm
                    if rdm:
                        rdm = ' - RDM support'
                    else:
                        rdm = ''
                    if port.description != "":
                        value = 'Port ' + str(port.id) + ' - ' + port.description + rdm
                    else:
                        value = 'Port ' + str(port.id) + rdm
                    return QVariant(value)
                except IndexError:
                    if debug:
                        # these cells does not exists
                        print(row, 'is out of port list')
                        return QVariant()
            else:
                return QVariant()
        else:
            return QVariant()

class PatchPanel(QGroupBox):
    """Group of widget to patch an universe"""
    def __init__(self):
        super(PatchPanel, self).__init__()
        self.ola = None
        self.create_ola()
        self.show()
        self.move(0,0)

        grid = QGridLayout()
        self.inputs_model = PortList()
        self.outputs_model = PortList()
        self.devices = QListView()
        self.devices_model = DeviceList()
        self.devices.setModel(self.devices_model)
        self.inputs = QListView()
        self.inputs.setModel(self.inputs_model)
        self.inputs.setFixedWidth(300)
        self.inputs.setMinimumHeight(200)
        self.outputs = QListView()
        self.outputs.setModel(self.outputs_model)
        self.outputs.setFixedWidth(300)
        self.outputs.setMinimumHeight(200)

        # Universe Selected Change
        self.devices.selectionModel().selectionChanged.connect(self.device_selection_changed)
        self.inputs.selectionModel().selectionChanged.connect(self.port_selection_changed)
        self.outputs.selectionModel().selectionChanged.connect(self.port_selection_changed)

        devices_label = QLabel('Devices')
        grid.addWidget(devices_label, 0, 0, 1, 1)
        grid.addWidget(self.devices, 1, 0, 10, 1)
        inputs_label = QLabel('Inputs')
        grid.addWidget(inputs_label, 0, 1, 1, 1)
        grid.addWidget(self.inputs, 1, 1, 10, 1)
        outputs_label = QLabel('Outputs')
        grid.addWidget(outputs_label, 11, 1, 1, 1)
        grid.addWidget(self.outputs, 12, 1, 10, 1)
        grid.setSpacing(10)
        self.setLayout(grid)
        self.display_ports()

    def display_ports(self):
        """display ports"""
        self.ola.client.GetCandidatePorts(self.GetCandidatePortsCallback, None)

    def GetCandidatePortsCallback(self, status, devices):
        """
        Function that fill-in universe menus with candidate devices/ports
        We need to make menus checkable to be able to patch ports
        """
        if status.Succeeded():
            for device in devices:
                self.devices_model.devices.append(device)

    def device_selection_changed(self, device):
        self.inputs_model.ports = []
        self.outputs_model.ports = []
        row = device.indexes()[0].row()
        device = device.indexes()[0].model().object(row)
        for port in device.input_ports:
            self.inputs_model.ports.append(port)
        self.inputs_model.layoutChanged.emit()
        for port in device.output_ports:
            self.outputs_model.ports.append(port)
        self.outputs_model.layoutChanged.emit()

    def port_selection_changed(self, port):
        row = port.indexes()[0].row()
        port = port.indexes()[0].model().object(row)
        print "port has been choosed !!!!! please patch it ----------", port

    def create_ola(self):
        """
        create the ola client. Called when app is launched.
        If olad is not running at this time,
        """
        # check if there is not already a OLA client
        if not self.ola:
            # create a OLA client
            ola = OLA()
            sleep(0.5)
            if ola.client:
                self.ola = ola
            else:
                # quit the app if no OLA server
                quit()

if __name__ == "__main__":
    # create the current App
    app = QApplication(sys.argv)
    panel = PatchPanel()
    sys.exit(app.exec_())
