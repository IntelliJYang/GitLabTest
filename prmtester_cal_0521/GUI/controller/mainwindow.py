#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import os
import traceback
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QStyle, QFileDialog, QMessageBox, QDesktopWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from GUI.resources import resources
from Configure import constant


class MainWindow(QMainWindow):
    disable_tools_signal = pyqtSignal(bool)

    def __init__(self, window_signal=None):
        super(MainWindow, self).__init__()

        self._window_signal = window_signal
        self.menu_file = self.menuBar().addMenu("&File")
        self.menu_tools = self.menuBar().addMenu("&Tools")
        self.menu_pdca = self.menu_tools.addMenu("PDCA")
        self.menu_audit = self.menu_tools.addMenu("ADUIT")
        self.menu_debug = self.menu_tools.addMenu("DEBUG")

        self.toolbar_file = self.addToolBar("File")
        self.toolbar_run = self.addToolBar("Run")
        self.toolbar_page = self.addToolBar("Page")
        self.toolbar_run.setFixedHeight(32)
        self.toolbar_file.setFixedHeight(32)
        self.toolbar_page.setFixedHeight(32)
        self.toolbar_file.setMovable(False)
        self.toolbar_page.setMovable(False)
        self.toolbar_run.setMovable(False)
        # actions
        self.open_action = QAction(self.style().standardIcon(56), "&Open", self)
        self.open_action.setStatusTip("select test plan")
        self.toolbar_file.addAction(self.open_action)

        self.start_action = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "&Start", self)
        self.toolbar_run.addAction(self.start_action)

        self.stop_action = QAction(self.style().standardIcon(QStyle.SP_MediaStop), "&Stop", self)
        self.toolbar_run.addAction(self.stop_action)

        self.loop_action = QAction(self.style().standardIcon(59), "&Loop", self)
        self.toolbar_run.addAction(self.loop_action)
        if constant.TP_ALL_SHOW and constant.OVER_ALL_SHOW:
            self.overview_action = QAction(self.style().standardIcon(52), "&overview", self)
            self.toolbar_page.addAction(self.overview_action)

            self.groupview_action = QAction(self.style().standardIcon(53), "&groupview", self)
            self.toolbar_page.addAction(self.groupview_action)

        self.open_pdca_action = QAction("&Open", self)
        self.close_pdca_action = QAction("&Close", self)
        self.menu_pdca.addAction(self.open_pdca_action)
        self.menu_pdca.addAction(self.close_pdca_action)
        if constant.PDCA:
            self.open_pdca_action.setDisabled(True)
            self.close_pdca_action.setEnabled(True)
        else:
            self.open_pdca_action.setEnabled(True)
            self.close_pdca_action.setDisabled(True)

        self.open_audit_action = QAction("&Open", self)
        self.close_audit_action = QAction("&Close", self)
        self.menu_audit.addAction(self.open_audit_action)
        self.menu_audit.addAction(self.close_audit_action)
        if constant.AUDIT:
            self.open_audit_action.setDisabled(True)
            self.close_audit_action.setEnabled(True)
        else:
            self.open_audit_action.setEnabled(True)
            self.close_audit_action.setDisabled(True)

        self.open_debug_action = QAction("&Open", self)
        # self.close_debug_action = QAction("&Close", self)
        self.menu_debug.addAction(self.open_debug_action)
        # self.menu_debug.addAction(self.close_debug_action)
        self.open_debug_action.setEnabled(True)
        # self.close_debug_action.setDisabled(True)

        self.disable_tools_signal.connect(self.menu_tools.setDisabled)

    def change_run_tool_state(self, flag):
        if flag:
            self.stop_action.setEnabled(True)
            self.start_action.setDisabled(True)
            # self.loop_action.setDisabled(True)
            self.disable_tools_signal.emit(True)
        else:
            self.stop_action.setDisabled(True)
            self.start_action.setEnabled(True)
            # self.loop_action.setEnabled(True)
            self.disable_tools_signal.emit(False)

    def set_window_center(self):
        screen = QDesktopWidget().screenGeometry()
        wd = screen.width()
        hg = screen.height()
        self.resize(wd * constant.SCREEN_WIDTH, hg * constant.SCREEN_HEIGHT)
        size = self.geometry()
        self.move((wd - size.width()) / 2,
                  (hg - size.height()) / 2)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            if self._window_signal:
                self._window_signal.emit('exit')
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
