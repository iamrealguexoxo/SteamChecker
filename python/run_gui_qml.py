#!/usr/bin/env python
"""Steam Workshop Checker - QML GUI Launcher"""
import sys
import os

# Add parent dir to path so steam_checker package is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from steam_checker.gui_qml import main

if __name__ == "__main__":
    main()
