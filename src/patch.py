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
                value = self.devices[row].name
                return QVariant(value)
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
    def __init__(self, parent):
        super(PatchPanel, self).__init__()
        
        self.ola = parent.ola

        self.parent = parent

        parent.vbox.addWidget(self)
        
        grid = QGridLayout()
        self.inputs_model = PortList()
        self.outputs_model = PortList()
        self.devices = QListView()
        self.devices_model = DeviceList()
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

    def display_ports(self, universe=None):
        """display ports"""
        self.ola.client.GetCandidatePorts(self.GetCandidatePortsCallback, universe)

    def GetCandidatePortsCallback(self, status, devices):
        """
        Function that fill-in universe menus with candidate devices/ports
        We need to make menus checkable to be able to patch ports
        """
        if status.Succeeded():
            if debug:
                print 'found', len(devices), 'devices'
            for device in devices:
                self.devices_model.devices.append(device)
                self.devices_model.layoutChanged.emit()
            print self.devices_model.devices

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
