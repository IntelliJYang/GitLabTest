#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
from PyQt5.QtWidgets import QFrame, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import pyqtSignal
from GUI.controller.statistic_group import StatisticGroupController
from GUI.view.pluginswiget import AllYield


class StatisticEntiretyController(object):

    def __init__(self):
        super(StatisticEntiretyController, self).__init__()
        self.group_c = StatisticGroupController()
        self.total_statistic_view = AllYield()
        self.view = StatisticEntiretyView(self.group_c.view, self.total_statistic_view)

    def statistic_sequence_start(self, site):
        self.group_c.statistic_list[site].slot_sequence_start()

    def statistic_sequence_stop(self, site, result):
        self.group_c.statistic_list[site].slot_sequence_stop(result)
        if result:
            self.total_statistic_view.result_pass()
        else:
            self.total_statistic_view.result_fail()

    def statistic_sequence_control(self, site, start, result):
        if start:
            self.statistic_sequence_start(site)
        else:
            self.statistic_sequence_stop(site, result)


class StatisticEntiretyView(QFrame):
    def __init__(self, group_statistic_widget, total_statistic_widget):
        super(StatisticEntiretyView, self).__init__()
        main_layout = QVBoxLayout()

        space = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        group_view_layout = QVBoxLayout()
        group_view_layout.addWidget(group_statistic_widget)
        group_view_layout.addWidget(total_statistic_widget)
        group_view_layout.addItem(space)
        group_view_layout.setContentsMargins(0, 0, 0, 0)
        group_view_layout.setSpacing(1)
        group_view_layout.addItem(space)

        main_layout.addLayout(group_view_layout, 1)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setFixedWidth(220)

        self.setFrameStyle(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = StatisticEntiretyController()
    controller.view.show()
    sys.exit(app.exec_())
