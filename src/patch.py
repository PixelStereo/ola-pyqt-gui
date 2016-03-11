#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Patch Window used to display available devices
Select a device will allow you to patch its port(s)
"""
import sys
# import from PyQt5 libs
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QVariant, QModelIndex, QFileInfo, QAbstractListModel
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QCheckBox, QListView, QLabel
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QMenu, QWidgetAction
# import from OLA package
from ola.OlaClient import OlaClient

debug = 1


class DeviceList(QAbstractListModel):
    """Model for a port list"""
    def __init__(self, parent):
        super(DeviceList, self).__init__()
        self.parent = parent
        self.devices = []

    def rowCount(self, index=None):
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
        if index.isValid() and index.row() >= 0 and index.row() < self.rowCount():
            row = index.row()
            if role == Qt.DisplayRole:
                value = self.devices[row].name
                return QVariant(value)
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
        return (Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable |Qt.ItemIsSelectable)

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
                if port.universe != None:
                    if universe.id != None:
                        if port.universe == universe.id:
                            check = Qt.Checked
                return QVariant(check)
        return QVariant()

    def setData(self, index, value, role=Qt.DisplayRole):
        """
        set the checkbox dor a port which enable it for the current universe
        """
        if index.isValid() and index.row() >= 0 and index.row() < self.rowCount():
            row = index.row()
            port = self.ports[row]
            if role == Qt.CheckStateRole:
                device = self.parent.device_selected.alias
                if self.mode == 'output_mode':
                    is_output = True
                else:
                    is_output = False
                if value == Qt.Unchecked:
                    action = OlaClient.UNPATCH
                if value == Qt.Checked:
                    action = OlaClient.PATCH
                universe = self.parent.parent.universe_selected
                result = self.parent.parent.ola.client.PatchPort(device, port.id, is_output, action, universe.id)
                self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.DisplayRole])
                self.layoutChanged.emit()
                self.parent.display_ports()
                return result
        return QVariant()

class PatchPanel(QGroupBox):
    """Group of widget to patch an universe"""
    def __init__(self, parent):
        super(PatchPanel, self).__init__()

        self.ola = parent.ola

        self.parent = parent

        self.device_selected = None

        self.universe = None

        grid = QGridLayout()
        self.inputs_model = PortList(self, 'input_mode')
        self.outputs_model = PortList(self, 'output_mode')
        self.devices = QListView()
        self.devices_model = DeviceList(self)
        self.devices.setModel(self.devices_model)
        self.inputs = QListView()
        self.inputs.setModel(self.inputs_model)
        self.inputs.setMinimumHeight(400)
        self.inputs.setMinimumHeight(120)
        self.outputs = QListView()
        self.outputs.setModel(self.outputs_model)
        self.outputs.setMinimumHeight(400)
        self.outputs.setMinimumHeight(120)

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
        else:
            if self.parent.universe_selected:
                universe = self.parent.universe_selected.id
            else:
                result = self.ola.client.GetCandidatePorts(self.GetCandidatePortsCallback, None)
                return result
        result = self.ola.client.FetchDevices(self.GetDecvicesCallback, universe)
        return result

    def GetCandidatePortsCallback(self, status, devices):
        """
        Called for a new universe
        """
        if status.Succeeded():
            # clear the list of devices
            self.devices_model.devices = []
            if debug:
                print 'found', len(devices), 'devices'
            for device in devices:
                self.devices_model.devices.append(device)
        self.parent.ola.devicesList.emit()
        self.refresh_ports()

    def GetDecvicesCallback(self, status, devices):
        """
        Fill-in universe menus with candidate devices/ports
        We need to make menus checkable to be able to patch ports
        """
        if status.Succeeded():
            # clear the list of devices
            self.devices_model.devices = []
            if debug:
                print 'found', len(devices), 'devices'
            for device in devices:
                self.devices_model.devices.append(device)
        self.parent.ola.devicesList.emit()
        self.refresh_ports()
        # if there was a selection before, restore it
        #if self.device_selected:
            #self.devices.setSelection(self.device_selected)

    def refresh_ports(self):
        device = self.device_selected
        print device
        if device:
            # reset the models of inputs and outputs
            self.inputs_model.ports = []
            self.outputs_model.ports = []
            print device.input_ports
            # Append input ports of this device to the inputs list model
            for port in device.input_ports:
                self.inputs_model.ports.append(port)
            # Append output ports of this device to the outputs list model
            for port in device.output_ports:
                self.outputs_model.ports.append(port)
            # please refresh Qlistview
            self.parent.ola.inPortsList.emit()
            self.parent.ola.outPortsList.emit()

    def device_selection_changed(self, device):
        # tell me which is the row selected
        row = device.indexes()[0].row()
        # tell me which device is associated with this row
        device = device.indexes()[0].model().object(row)
        self.device_selected = device
        # refresh ports list
        self.refresh_ports()
        if debug:
            print 'selected device :', device.name
