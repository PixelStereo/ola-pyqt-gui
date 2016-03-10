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

debug = 1


class DeviceList(QAbstractListModel):
    """Model for a port list"""
    def __init__(self, parent):
        super(DeviceList, self).__init__()
        self.parent = parent
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
                value = self.devices[row].name
                return QVariant(value)
            else:
                return QVariant()
        else:
            return QVariant()


class PortList(QAbstractListModel):
    """Model for a port list"""
    def __init__(self, parent, mode):
        super(PortList, self).__init__()
        self.parent = parent
        self.mode = mode
        self.ports = []
        self.universe_selected = self.parent.parent.universe_selected

    def rowCount(self, index=None):
        return len(self.ports)

    def object(self, row):
        """
        return the port object for a given row
        """   
        return  self.ports[row]

    def flags(self, index):
        return (Qt.ItemIsUserCheckable|Qt.ItemIsEnabled)
        
    def data(self, index, role=Qt.DisplayRole):
        """
        return the name of the port
        """
        if index.isValid() and index.row() >= 0 and index.row() < self.rowCount():
            row = index.row()
            port = self.ports[row]
            if role == Qt.DisplayRole:
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
            elif role == Qt.CheckStateRole:
                # check if this port is patched to the selected universe
                check = Qt.Unchecked
                universe = self.parent.parent.universe_selected
                # for input ports
                if self.mode == 'input_mode':
                    if port.universe != None:
                        if universe.id != None:
                            if port.universe == universe.id:
                                check = Qt.Checked
                return QVariant(check)
            else:
                return QVariant()
        else:
            return QVariant()

    def setData(self, index, state, role=Qt.DisplayRole):
        """
        set the checkbox dor a port which enable it for the current universe
        """
        if index.isValid() and index.row() >= 0 and index.row() < self.rowCount():
            row = index.row()
            port = self.ports[row]
            if role == Qt.CheckStateRole:
                value = state
                print value
                return value
            else:
                return QVariant()
        else:
            return QVariant()

class PatchPanel(QGroupBox):
    """Group of widget to patch an universe"""
    def __init__(self, parent):
        super(PatchPanel, self).__init__()
        
        self.ola = parent.ola

        self.parent = parent

        self.universe = None

        parent.vbox.addWidget(self)
        
        grid = QGridLayout()
        self.inputs_model = PortList(self, 'input_mode')
        self.outputs_model = PortList(self, 'output_mode')
        self.devices = QListView()
        self.devices_model = DeviceList(self)
        self.devices.setModel(self.devices_model)
        self.inputs = QListView()
        self.inputs.setModel(self.inputs_model)
        self.inputs.setMinimumHeight(400)
        self.inputs.setMinimumHeight(150)
        self.outputs = QListView()
        self.outputs.setModel(self.outputs_model)
        self.outputs.setMinimumHeight(400)
        self.outputs.setMinimumHeight(150)

        # Universe Selected Change
        self.devices.selectionModel().selectionChanged.connect(self.device_selection_changed)

        devices_label = QLabel('Devices')
        grid.addWidget(devices_label, 0, 0, 1, 1)
        grid.addWidget(self.devices, 1, 0, 21, 1)
        inputs_label = QLabel('Inputs')
        grid.addWidget(inputs_label, 0, 1, 1, 1)
        grid.addWidget(self.inputs, 1, 1, 10, 1)
        outputs_label = QLabel('Outputs')
        grid.addWidget(outputs_label, 11, 1, 1, 1)
        grid.addWidget(self.outputs, 12, 1, 10, 1)
        grid.setSpacing(5)
        self.setLayout(grid)

    def display_ports(self, universe=None):
        """display ports"""
        if universe:
            universe=universe.id
        self.ola.client.FetchDevices(self.GetDecvicesCallback, universe)

    def GetDecvicesCallback(self, status, devices):
        """
        Function that fill-in universe menus with candidate devices/ports
        We need to make menus checkable to be able to patch ports
        """
        if status.Succeeded():
            if debug:
                print 'found', len(devices), 'devices'
            for device in devices:
                self.devices_model.devices.append(device)
        self.parent.ola.devicesList.emit()

    def device_selection_changed(self, device):
        # reset the models of inputs and outputs
        self.inputs_model.ports = []
        self.outputs_model.ports = []
        # tell me which is the row selected
        row = device.indexes()[0].row()
        # tell me which device is associated with this row
        device = device.indexes()[0].model().object(row)
        # Append input ports of this device to the inputs list model
        for port in device.input_ports:
            self.inputs_model.ports.append(port)
        # please refresh the inputs Qlistview
        self.inputs_model.layoutChanged.emit()
        # Append output ports of this device to the outputs list model
        for port in device.output_ports:
            self.outputs_model.ports.append(port)
        # please refresh the outputs Qlistview
        self.outputs_model.layoutChanged.emit()
        if debug:
            print 'selected device :', device.name
