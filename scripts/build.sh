#!/bin/sh

pyinstaller --onefile --windowed --icon=icon/ola-pyqt-gui.icns -n ola-pyqt-gui_$1 main.py