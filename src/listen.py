#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Child module hosts a project-related class"""

from PyQt5.QtCore import QThread

import getopt
import textwrap
import sys
from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException


class OLA_client(QThread):
    """docstring for OLAUniverseCallback"""
    def __init__(self):
        QThread.__init__(self)
        self.start()
        self.client = None

    def __del__(self):
        self.wait()

    def run(self):
        # OLA
        try:
            self.wrapper = ClientWrapper()
            client = self.wrapper.Client()
            self.client = client
            self.wrapper.Run()
        except OLADNotRunningException:
            print 'CANNOT CONNECT TO OLA'

    def getclient(self):
        return self.client

    def stop(self):
        if self.client:
            self.wrapper.Stop()