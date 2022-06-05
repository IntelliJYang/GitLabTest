#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFrame, QApplication, QSystemTrayIcon, QMenu


class LaunchController(QObject):
    def __init__(self):
        super(LaunchController, self).__init__()
        self.view = LaunchView()


class LaunchView(QFrame):
    def __init__(self):
        super(LaunchView, self).__init__()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    launch = LaunchController()
    launch.view.show()
    sys.exit(app.exec_())
