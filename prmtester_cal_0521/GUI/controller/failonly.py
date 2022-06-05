#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QSortFilterProxyModel, QRegExp, Qt, QModelIndex
from GUI.view.tableview import KTableView
from GUI.model.failonlymodel import FailOnlyModel


class FailOnlyController(object):
    def __init__(self, testplan_model):
        super(FailOnlyController, self).__init__()
        self.view = FailOnlyView()

        self.filter_model = FailOnlyModel()
        self.filter_model.setDynamicSortFilter(True)
        self.filter_model.setSourceModel(testplan_model)
        self.view.table_view.setModel(self.filter_model)
        self.view.button.clicked.connect(self.filter_happen)

    def filter_happen(self):
        index = self.filter_model.createIndex(0, 0)
        for i in range(600):
            self.filter_model.filterAcceptsRow(i, index)


class FailOnlyView(QWidget):
    def __init__(self):
        super(FailOnlyView, self).__init__()
        self.table_view = KTableView(self)
        layout = QHBoxLayout()
        self.button = QPushButton('test')
        layout.addWidget(self.button)
        layout.addWidget(self.table_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = FailOnlyController()
    controller.view.show()
    sys.exit(app.exec_())
