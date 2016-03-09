#!/bin/sh

pyinstaller --onefile --windowed --icon=icon/icon.icns -n ola-pyqt-gui_$1 main.py