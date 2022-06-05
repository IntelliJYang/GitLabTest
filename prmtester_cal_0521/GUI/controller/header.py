#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import time
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel, QFrame
from PyQt5.QtCore import QTimer
from GUI.resources.style.ui_style import KFont, KColor
from GUI.resources import resources
from Configure import constant

__VERSION__ = "TestSuite 2019.0.0.1"


class HeaderController(object):
    def __init__(self):
        self._start_time = 0
        self.view = HeaderView()
        self._count_timer = QTimer()
        self._count_timer.timeout.connect(self._run_counting)

    def display_tp_info(self, file_name):
        name_list = file_name.split('__')
        self.view.display_project_info(name_list[0])
        self.view.display_test_plan_verison(name_list[1])

    def _run_counting(self):
        t = round(time.time() - self._start_time, 1)
        self.view.set_lbl_run_counting(t)

    def start_header_timer(self):
        self.view.set_lbl_test_status('RUNNING')
        self._start_time = time.time()
        self._count_timer.start(100)

    def stop_header_timer(self, result):
        # self._count_timer.stop()
        if isinstance(result, list):
            if 'PASS' in result:
                self.view.set_lbl_test_status('PASS')
            elif 'IDLE' in result:
                self.view.set_lbl_test_status('IDLE')
            else:
                self.view.set_lbl_test_status('FAIL')

    def header_control_timer(self, flag):
        if flag:
            self.start_header_timer()
        else:
            self._count_timer.stop()
            #self.stop_header_timer([])

    def switch_pdca(self, pdca):
        self.view.switch_pdca(pdca)

    def switch_audit(self, audit):
        self.view.switch_audit(audit)


class HeaderView(QFrame):
    def __init__(self):
        super(HeaderView, self).__init__()
        # create all display labels
        self._lbl_project_info = QLabel()
        self._lbl_test_plan_version = QLabel()
        self._lbl_test_status = QLabel()
        self._lbl_test_status.setFixedWidth(200)
        self._lbl_test_status.setAlignment(Qt.AlignCenter)
        self._lbl_run_counting = QLabel()
        self._lbl_run_counting.setAlignment(Qt.AlignCenter)
        self._lbl_audit_status = QLabel()
        # self._lbl_audit_status.setFixedWidth(200)
        self._lbl_audit_status.setAlignment(Qt.AlignCenter)
        self._lbl_pdca_status = QLabel()
        # self._lbl_pdca_status.setFixedWidth(200)
        self._lbl_pdca_status.setAlignment(Qt.AlignCenter)
        self._lbl_prm_logo = QLabel()
        self._lbl_soft_version = QLabel()
        self._init_widget_value()
        self._layout_widgets()

    def _init_widget_value(self):
        """
        init all labels style
        :return:
        """
        self._set_logo()
        self._set_project_info()
        self._set_test_plan_version()
        self._set_test_status('IDLE')
        self._set_run_counting('0')
        self._set_audit()
        self._set_pdca()
        self._set_soft_vertion()
        self.switch_pdca(constant.PDCA)
        self.switch_audit(constant.AUDIT)

    def _layout_widgets(self):
        """
        layout all labels in gridlayout
        :return:
        """
        self.setContentsMargins(0, 0, 0, 0)
        # self.setFixedHeight(125)
        # self.setMaximumHeight(125)
        placeholder = QLabel("")
        placeholder.setHidden(True)
        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._lbl_project_info, 0, 0, 2, 4)
        main_layout.addWidget(placeholder, 1, 0, 1, 1)
        main_layout.addWidget(self._lbl_test_plan_version, 2, 0, 2, 4)
        main_layout.addWidget(placeholder, 3, 0, 1, 1)
        main_layout.addWidget(self._lbl_test_status, 0, 4, 2, 1)
        main_layout.addWidget(placeholder, 2, 4, 1, 1)
        main_layout.addWidget(self._lbl_run_counting, 3, 4, 1, 1)
        main_layout.addWidget(self._lbl_pdca_status, 0, 5, 2, 2)
        main_layout.addWidget(placeholder, 2, 5, 1, 2)
        main_layout.addWidget(self._lbl_audit_status, 3, 5, 2, 2)
        main_layout.addWidget(self._lbl_prm_logo, 0, 7, 2, 2)
        main_layout.addWidget(placeholder, 2, 7, 1, 1)
        main_layout.addWidget(self._lbl_soft_version, 3, 7, 1, 2, Qt.AlignRight | Qt.AlignBottom)

        self.setLayout(main_layout)

    def _set_logo(self):
        pix_map = QPixmap(':/images/logo.png')
        pix_map = pix_map.scaled(QSize(333, 60), Qt.KeepAspectRatio)
        self._lbl_prm_logo.setPixmap(pix_map)
        # self._lbl_prm_logo.setScaledContents(True)

    def _set_soft_vertion(self):
        self._lbl_soft_version.setText("sw: {}".format(__VERSION__))

    def _set_project_info(self):
        self._lbl_project_info.setText(constant.PROJECT)
        self._lbl_project_info.setFont(KFont.FONT_36)
        # self._lbl_project_info.setFixedWidth(333)

    def _set_test_plan_version(self):
        self._lbl_test_plan_version.setText(constant.DEFAULT_TESTPLAN_VERSION)

    def _set_test_status(self, status):
        self._lbl_test_status.setText(status)
        self._lbl_test_status.setFont(KFont.FONT_36)

    def _set_run_counting(self, time_str):
        self._lbl_run_counting.setText(time_str + ' s')
        self._lbl_run_counting.setFont(KFont.FONT_36)

    def _set_audit(self):
        self._lbl_audit_status.setText('AUDIT')
        self._lbl_audit_status.setFont(KFont.FONT_36)

    def _set_pdca(self):
        self._lbl_pdca_status.setText('NOPDCA')
        self._lbl_pdca_status.setFont(KFont.FONT_36)

    def switch_pdca(self, flag=True):
        self._lbl_pdca_status.setHidden(flag)
        if flag:
            self._lbl_pdca_status.setStyleSheet(KColor.bg_window + KColor.green)
        else:
            self._lbl_pdca_status.setStyleSheet(KColor.bg_yellow + KColor.red)

        self._set_pdca_mode(not flag)

    def switch_audit(self, flag=False):

        self._lbl_audit_status.setHidden(not flag)
        if flag:

            self._lbl_audit_status.setStyleSheet(KColor.bg_yellow + KColor.red)
        else:
            self._lbl_audit_status.setStyleSheet(KColor.bg_window + KColor.green)

        self._set_audit_mode(flag)

    def _set_audit_mode(self, audit):
        if audit:
            self.setStyleSheet(KColor.bg_purple)
            self._lbl_project_info.setStyleSheet(KColor.white)
            self._lbl_test_plan_version.setStyleSheet(KColor.white)
            self._lbl_soft_version.setStyleSheet(KColor.white)
        else:
            self.setStyleSheet(KColor.bg_window)
            self._lbl_test_plan_version.setStyleSheet(KColor.black)
            self._lbl_project_info.setStyleSheet(KColor.blue)
            self._lbl_soft_version.setStyleSheet(KColor.black)

    def _set_pdca_mode(self, pdca):
        if pdca:
            self.setStyleSheet(KColor.bg_orange)
            self._lbl_project_info.setStyleSheet(KColor.white)
            self._lbl_test_plan_version.setStyleSheet(KColor.white)
            self._lbl_soft_version.setStyleSheet(KColor.white)
        else:
            self.setStyleSheet(KColor.bg_window)
            self._lbl_test_plan_version.setStyleSheet(KColor.black)
            self._lbl_project_info.setStyleSheet(KColor.blue)
            self._lbl_soft_version.setStyleSheet(KColor.black)

    def set_lbl_run_counting(self, t):
        self._lbl_run_counting.setText("{} s".format(t))

    def display_project_info(self, info):
        self._lbl_project_info.setText(info)

    def display_test_plan_verison(self, version):
        self._lbl_test_plan_version.setText(version)

    def set_lbl_test_status(self, status):
        self._lbl_test_status.setText(status)
        if status == 'PASS':
            self._lbl_test_status.setStyleSheet("{}{}".format(KColor.bg_green, KColor.white))
        elif status == 'FAIL':
            self._lbl_test_status.setStyleSheet("{}{}".format(KColor.bg_red, KColor.white))
        else:
            self._lbl_test_status.setStyleSheet("{}{}".format(KColor.bg_window, KColor.black))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    he = HeaderController()
    he.view.show()
    sys.exit(app.exec_())
