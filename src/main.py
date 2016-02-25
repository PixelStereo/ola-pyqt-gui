#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
main script
"""

import sys
from window import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    # this is for python2 only
    try:
        reload(sys)
        sys.setdefaultencoding('utf8')
    except NameError:
        pass
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
