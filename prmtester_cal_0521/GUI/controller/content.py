#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
from Configure import constant
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QApplication, QFrame, QStackedLayout, QStackedWidget
from GUI.controller.debug import DebugController
from GUI.controller.tpcontroller import TestPlanController
from GUI.controller.statistic_entirety import StatisticEntiretyController
from GUI.controller.overviewcontroller import OverViewController


class ContentController(object):
    def __init__(self):
        super(ContentController, self).__init__()
        self.tp_c = TestPlanController()
        self.statistic_c = StatisticEntiretyController()
        self.debug_c = DebugController()
        self.over_c = OverViewController()

        self.view = ContentView(self.tp_c.view, self.statistic_c.view, self.debug_c.view, self.over_c.view)

    def open_debug(self):
        self.tp_c.set_receiving(False)
        self.debug_c.set_receiving(True)
        self.debug_c.add_subscribers_of_sequencers()
        self.view.main_layout.setCurrentIndex(1)

    def close_debug(self):
        self.tp_c.set_receiving(True)
        self.debug_c.set_receiving(False)
        self.view.main_layout.setCurrentIndex(0)

    def change_page(self, index):
        self.view.change_run_page(index)


class ContentView(QFrame):
    def __init__(self, tp_view, statistic_view, debug_view, over_view):
        super(ContentView, self).__init__()
        self.main_layout = QStackedLayout()
        self.run_widget = QStackedWidget()
        debug_widget = QWidget()
        debug_layout = QHBoxLayout()
        debug_layout.addWidget(debug_view, alignment=Qt.AlignCenter)
        debug_widget.setLayout(debug_layout)


        if constant.OVER_ALL_SHOW:
            self.run_widget.addWidget(over_view)
        if constant.TP_ALL_SHOW:
            all_in_one_widget = QFrame()
            all_in_one_layout = QHBoxLayout()
            all_in_one_layout.addWidget(tp_view, alignment=Qt.AlignLeft)
            all_in_one_layout.addWidget(statistic_view, alignment=Qt.AlignRight)
            all_in_one_layout.setSpacing(0)
            all_in_one_layout.setContentsMargins(0, 0, 0, 0)
            all_in_one_widget.setLayout(all_in_one_layout)
            # all_in_one_widget.setContentsMargins(0, 0, 0, 0)
            all_in_one_widget.setFrameStyle(QFrame.Box)
            all_in_one_widget.setFrameShadow(QFrame.Sunken)
            self.run_widget.addWidget(all_in_one_widget)

        self.main_layout.addWidget(self.run_widget)
        self.main_layout.addWidget(debug_widget)

        self.setLayout(self.main_layout)

    def change_run_page(self, index):
        self.run_widget.setCurrentIndex(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = ContentController()
    controller.view.show()
    sys.exit(app.exec_())
