# -*- coding: utf-8 -*-

# !/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import os
import time
import sys
from GUI.controller.application import Application
from PyQt5.QtWidgets import QApplication, QSplashScreen, qApp
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from Common.BBase import cShell

if __name__ == '__main__':
    os.system("pkill -9 Python")
    os.system("pkill -9 python")
    result, bool = cShell.RunShellWithTimeout('ps ax|grep python')
    print result


    # os.system("python ./ThirdPartylib/update_rtc")
    # app = QApplication(sys.argv)
    app = Application(sys.argv)
    time.sleep(10)

    sys.exit(app.exec_())

