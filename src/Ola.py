#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module implements a OLA class that launch OLA server
and runs a dedicated Client for this server
"""

#import from standard python lib
import threading
import subprocess
from time import sleep
# import from OLA python module
from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException
#import from PyQt5 lib
from PyQt5.QtCore import pyqtSignal, QThread

debug = 1


class OlaServer(QThread):
    """
    Separate Thread that run OLA Server (launched by OLA client)
    """
    def __init__(self):
        QThread.__init__(self)
        # start the thread
        self.start()
        if debug:
            print 'try to launch OLA server'

    def __del__(self):
        self.wait()

    def run(self):
        """
        the running thread
        """
        try:
            cmd = "/usr/local/bin/olad -c ../config"
            #self.the_process = subprocess.Popen("exec " + cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
            self.the_process = subprocess.Popen("exec " + cmd, shell=True)
        except:
            print 'ola cannot be launched'

    def stop(self):
        """Stop the OLA server if it has been launch by this thread"""
        self.the_process.terminate()
        self.the_process.kill()


class OLA(QThread):
    """
    Separate Thread that launch OLA server and run OLA Client
    It runs only if OLA server is responding
    """
    # signal that there is a new frame for the selected universe
    universeChanged = pyqtSignal()
    # signal that there is a new universes_list to display
    universesList = pyqtSignal()
    # signal that there is a new list of devices to display
    devicesList = pyqtSignal()
    # signal that there is a new list of inputs portsto display
    inPortsList = pyqtSignal()
    # signal that there is a new list of inputs portsto display
    outPortsList = pyqtSignal()
    def __init__(self):
        QThread.__init__(self)
        self.server = None
        self.client = None
        try:
            # launch OLA server
            self.server = OlaServer()
        except:
            # OLA server does not work properly
            print 'OLA server not responding'
        sleep(0.1)
        # start the thread
        if self.server:
            self.start()
        else:
            print 'no server is running, cannot start a client'

    def __del__(self):
        self.wait()

    def run(self):
        """
        the running thread
        """
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
            if debug:
                print 'connected to OLA server'
            self.wrapper.Run()
        except OLADNotRunningException:
            if debug:
                print 'cannot connect to OLA'

    def stop(self):
        """
        stop the OLA client wrapper
        """
        if self.client:
            self.wrapper.Stop()
            if debug:
                print 'OLA client is stopped'
        if self.server:
            self.server.stop()
            if debug:
                print 'OLA server is stopped'
        return True
