#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2020, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QListView, QTextEdit, QPushButton, \
    QGridLayout, QLabel, QSpinBox, QSpacerItem, QSizePolicy, QTabWidget, QComboBox, QTextBrowser, QSplitter, \
    QTableWidget, QTableWidgetItem, QMessageBox, QAbstractSpinBox, QLineEdit
from GUI.Debugger.dbg_dmm import DMMDebug


class FuncDebugController(QObject):
    def __init__(self, rpc_public_api, testenine):
        super(FuncDebugController, self).__init__()
        self.view = QFrame()
        self.tedispatch = TEDispatchDebug(rpc_public_api, testenine)
        self.dmm_debug = DMMDebug(testenine)
        self.setup_ui()

    def setup_ui(self):
        tab = QTabWidget()
        tab.addTab(self.dmm_debug.view, 'dmm.dmm')
        tab.addTab(self.tedispatch.view, 'AllFuction')
        layout_main = QHBoxLayout()
        layout_main.addWidget(tab)
        layout_main.setContentsMargins(0, 0, 0, 0)
        self.view.setLayout(layout_main)
        self.view.setContentsMargins(0, 0, 0, 0)


class TEDispatchDebug(QObject):
    def __init__(self, rpc_public_api, testenine):
        super(TEDispatchDebug, self).__init__()
        self.rpc_public_api = rpc_public_api
        self.current_index = 0
        self.test_engine = testenine
        self.view = QFrame()
        self.func_table = QTableWidget()
        self.txt_reve = QTextBrowser()
        self.txt_search = QLineEdit()
        self.txt_search.setFixedWidth(230)
        self.txt_search.setPlaceholderText('public api')
        self.txt_search.textChanged.connect(self.search)
        self.btn_search = QPushButton('search')
        self.btn_search.clicked.connect(self.search_next)
        self.btn_search.setFixedWidth(100)
        self.setup_ui()
        self.setup_rpc_public()
        self.func_table.cellDoubleClicked.connect(self.func_clicked)

    def setup_ui(self):
        layout_search = QHBoxLayout()
        layout_search.addWidget(self.txt_search)
        layout_search.addWidget(self.btn_search)
        layout_search.setContentsMargins(0, 0, 0, 0)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_search)
        layout_main.addWidget(self.func_table, 8)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(1)
        layout_main.addWidget(self.txt_reve, 2)
        self.view.setLayout(layout_main)
        self.func_table.setColumnCount(5)
        self.func_table.setColumnWidth(0, 180)
        self.func_table.setColumnWidth(1, 80)
        self.func_table.setColumnWidth(2, 80)
        self.func_table.setColumnWidth(3, 50)
        self.func_table.setColumnWidth(4, 60)

    def setup_rpc_public(self):
        self.func_table.setHorizontalHeaderLabels(['Func', 'Param1', 'Param2', 'UNIT', 'TIMEOUT'])
        self.func_table.horizontalHeader().setSectionsClickable(False)
        self.func_table.sortItems(0, Qt.AscendingOrder)
        row = 0
        self.func_table.setRowCount(len(self.rpc_public_api))
        self.func_table.setColumnWidth(0, 150)
        for line in self.rpc_public_api:
            item = QTableWidgetItem(line)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.func_table.setItem(row, 0, item)
            row += 1

    def func_clicked(self, x, y):
        if y == 0:
            func = None
            p1 = None
            p2 = None
            func_item = self.func_table.item(x, 0)
            if func_item:
                func = func_item.text()
            p1_item = self.func_table.item(x, 1)
            if p1_item:
                p1 = p1_item.text()
            p2_item = self.func_table.item(x, 2)
            if p2_item:
                p2 = p2_item.text()
            unit_item = self.func_table.item(x, 3)
            to_item = self.func_table.item(x, 4)

            if func:
                u = unit_item.text() if unit_item else ''
                to = to_item.text() if to_item else 5000
                response = getattr(self.test_engine.remote_server(), func)(p1, p2, unit=u, timeout=int(to))
                if not response:
                    self.update_msg('No response')
                    return
                if isinstance(response.result, basestring):
                    ret_lst = [c for c in response.result if ord(c) < 128]
                    ret_conv = ''.join(ret_lst)
                else:
                    ret_conv = str(response.result)
                self.update_msg(ret_conv)

    def update_msg(self, msg):
        self.txt_reve.append(msg)

    def search(self, name):
        for i, val in enumerate(self.rpc_public_api):
            if name.lower() in val.lower():
                self.func_table.selectRow(i)
                self.current_index = i
                break

    def search_next(self):
        txt = self.txt_search.text()
        last_nets = self.rpc_public_api[self.current_index:]
        index = self.current_index
        for i, val in enumerate(last_nets):
            index = index + i
            if txt.lower() in val.lower():
                self.func_table.selectRow(self.current_index + i + 1)
                self.current_index = i + self.current_index + 1
                break
        if index >= len(self.rpc_public_api):
            self.current_index = -1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = FuncDebugController(['a'], None)
    controller.view.show()
    sys.exit(app.exec_())
