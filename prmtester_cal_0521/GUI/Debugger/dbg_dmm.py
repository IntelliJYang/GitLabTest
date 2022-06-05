#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2020, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import os
import zmq
import sys
import json
import thread
import traceback
from Configure import zmqports
from GUI.resources.style.ui_style import KColor
from Common.prm_sdb import SequencerDebugger
from threading import Thread
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QListView, QTextEdit, QPushButton, \
    QGridLayout, QLabel, QSpinBox, QSpacerItem, QSizePolicy, QTabWidget, QComboBox, QTextBrowser, QSplitter, \
    QTableWidget, QTableWidgetItem, QMessageBox, QAbstractSpinBox, QLineEdit

# IO_MAP_PATH = '/'.join(os.path.abspath(__file__).split('/')[:-4] + ["PROJECT", PROJECT_NAME, "Map", "io_map.json"])
DMM_TABLE = []
# if os.path.exists(IO_MAP_PATH):
#     with open(IO_MAP_PATH, 'r') as f:
#         try:
#             io_table = json.load(f)
#             DMM_TABLE = io_table.get("HWIO_MeasureTable").keys()
#         except Exception as e:
#             print traceback.format_exc(e)


class DMMDebug(QObject):
    def __init__(self, testenine):
        super(DMMDebug, self).__init__()
        self.matched_table = []
        self.search_count = 0
        self.test_engine = testenine
        self.current_index = 0
        self.view = QFrame()
        self.func_table = QTableWidget()
        self.txt_reve = QTextBrowser()
        self.txt_search = QLineEdit()
        self.txt_search.setFixedWidth(230)
        self.txt_search.setPlaceholderText('DMM netname')
        self.txt_search.textChanged.connect(self.search)
        self.btn_search = QPushButton('search')
        self.btn_search.clicked.connect(self.search_next)
        self.btn_search.setFixedWidth(100)
        self.btn_read_all = QPushButton("Read All")
        self.btn_read_all.clicked.connect(self.read_all_dmm)

        self.setup_ui()
        self.dmm_table = DMM_TABLE
        self.dmm_table.sort()
        self.setup_functions()
        self.func_table.cellDoubleClicked.connect(self.func_clicked)

    def setup_ui(self):
        layout_main = QVBoxLayout()
        layout_search = QHBoxLayout()
        layout_search.addWidget(self.txt_search)
        layout_search.addWidget(self.btn_search)
        layout_search.addWidget(self.btn_read_all)
        layout_search.setContentsMargins(0, 0, 0, 0)
        spacer_item = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout_search.addItem(spacer_item)
        # layout_main.addWidget(self.txt_search)
        # layout_main.addLayout(self.btn_search)
        layout_main.addLayout(layout_search)
        layout_main.addWidget(self.func_table, 8)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(1)

        layout_main.addWidget(self.txt_reve, 2)
        self.view.setLayout(layout_main)
        self.func_table.setColumnCount(2)
        self.func_table.setColumnWidth(0, 200)
        self.func_table.setColumnWidth(1, 110)

    def setup_functions(self):
        self.func_table.setHorizontalHeaderLabels(['NET NAME', 'RESULT'])
        self.func_table.horizontalHeader().setSectionsClickable(False)
        self.func_table.sortItems(0, Qt.AscendingOrder)
        row = 0
        self.func_table.setRowCount(len(self.dmm_table))
        for line in self.dmm_table:
            item = QTableWidgetItem(line)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.func_table.setItem(row, 0, item)
            row += 1

    def func_clicked(self, x, y):
        if y == 0:
            net = None
            net_item = self.func_table.item(x, 0)
            if net_item:
                net = net_item.text()
            if net:
                if self.test_engine:
                    response = getattr(self.test_engine.remote_server(), 'dmm.dmm')(net, unit='mV')
                    if not response:
                        self.update_msg('No response')
                        self.update_rsult(x, 'No response')
                        return
                    if isinstance(response.result, basestring):
                        ret_lst = [c for c in response.result if ord(c) < 128]
                        ret_conv = ''.join(ret_lst)
                    else:
                        ret_conv = str(response.result)
                    self.update_msg(ret_conv)
                    self.update_rsult(x, ret_conv)
                else:
                    self.update_rsult(x, 'test engine is none')
                    self.update_msg('test engine is none')
            else:
                self.update_msg('netname is none')

    def update_msg(self, msg):
        self.txt_reve.append(msg)

    def update_rsult(self, row, val):
        item = QTableWidgetItem(val)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.func_table.setItem(row, 1, item)

    def search(self, name):
        self.search_count = 0
        self.matched_table = []
        for i, val in enumerate(self.dmm_table):
            if name.lower() in val.lower():
                self.matched_table.append([i, val])
        if len(self.matched_table) > 0:
            self.func_table.selectRow(self.matched_table[0][0])

    def search_next(self):
        self.search_count += 1
        if self.search_count >= len(self.matched_table):
            self.search_count = 0
        try:
            index = self.matched_table[self.search_count][0]
        except:
            index = 0
        self.func_table.selectRow(index)

    def read_all_dmm(self):
        if self.test_engine:
            for i in range(0, len(self.dmm_table)):
                net = self.dmm_table[i]
                response = getattr(self.test_engine.remote_server(), 'dmm.dmm')(net, unit='mV')
                if not response:
                    self.update_msg('No response')
                    self.update_rsult(i, 'No response')
                    return
                if isinstance(response.result, basestring):
                    ret_lst = [c for c in response.result if ord(c) < 128]
                    ret_conv = ''.join(ret_lst)
                    self.update_msg(ret_conv)
                else:
                    ret_conv = str(response.result)
                    self.update_rsult(i, ret_conv)
        else:
            self.update_msg("Engine is not ready")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = DMMDebug(None)
    controller.view.show()
    sys.exit(app.exec_())
