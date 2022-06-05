#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2020, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import os
import zmq
import sys
import traceback
from Configure import zmqports, constant
from threading import Thread
from Common.rpc_client import RPCClientWrapper
from Common.tinyrpc.protocols.jsonrpc import JSONRPCSuccessResponse
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QListView, QTextEdit, QPushButton, \
    QGridLayout, QLabel, QSpinBox, QSpacerItem, QSizePolicy, QTabWidget, QComboBox, QTextBrowser, QSplitter, \
    QTableWidget, QTableWidgetItem, QMessageBox
from GUI.Debugger.dbg_streem import DBGFIXTURE
# from ansi2html import Ansi2HTMLConverter
from GUI.Debugger.dbg_sequencer import SeqDebug
from GUI.Debugger.dbg_function import FuncDebugController


class DebugContainer(QFrame):
    def __init__(self, parent=None):
        super(DebugContainer, self).__init__(parent)
        self.tab = QTabWidget()
        self.setup_ui()

    def setup_ui(self):
        for i in range(constant.SLOTS):
            sub_view = SlotContainer(i)
            self.tab.addTab(sub_view, 'Slot{}'.format(i + 1))
        layout = QHBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tab)
        self.setLayout(layout)
        self.setMinimumWidth(1000)

        # self.setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to close?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class SlotContainer(QFrame):
    def __init__(self, site=0):

        super(SlotContainer, self).__init__()
        test_engine = RPCClientWrapper(
            'tcp://localhost:' + str(zmqports.TEST_ENGINE_PORT + site),
            None
        )
        response = test_engine.remote_server().collect_debug_ref(timeout=1000)
        print '*' * 100
        print response
        functions = []
        if response:
            if isinstance(response, JSONRPCSuccessResponse):
                info = response.result
                functions = info.get('functions')
                functions.sort()
            else:
                print response.error
                pass

        self.work_debug = WorkDebug(test_engine, site)
        self.seq_debug = SeqDebug(site)
        self.func_debug = FuncDebugController(functions, test_engine)
        self.setup_ui()

    def setup_ui(self):
        layout_container = QHBoxLayout()
        layout_container.setContentsMargins(5, 5, 5, 5)
        splitter_main = QSplitter(Qt.Vertical)
        splitter_H = QSplitter(Qt.Horizontal)

        splitter_main.addWidget(self.work_debug.view)
        splitter_main.addWidget(self.seq_debug.view)

        splitter_H.addWidget(splitter_main)
        splitter_H.addWidget(self.func_debug.view)

        splitter_H.setStretchFactor(0, 3)
        splitter_H.setStretchFactor(1, 5)
        layout_container.addWidget(splitter_H)
        self.setLayout(layout_container)
        self.setContentsMargins(0, 0, 0, 0)


class WorkDebug(QObject):
    def __init__(self, engine, site):
        super(WorkDebug, self).__init__()
        self.site = site
        dc_port_PORT = zmqports.UART2_PUB + site
        dc_config_PORT = zmqports.UART3_PUB + site
        dut_PORT = zmqports.UART_PUB + site
        self.dc_port = RW(dc_port_PORT, '31337', engine)
        self.dc_config = RW(dc_config_PORT, '31336', engine)
        self.dc_config.init_cmd_box(
            ['', 'restart_dc_manager-pl', 'enable_dc', 'enable_advdm', 'disable_dc', 'disable_advdm'])
        self.dut = RW(dut_PORT, 'dut', engine)
        self.fixture = DBGFIXTURE()
        self.view = QFrame()
        self.setup_ui()

    def setup_ui(self):
        tab = QTabWidget()
        tab.addTab(self.dc_config.view, 'DC_CONFIG_{}'.format(self.site + 1))
        tab.addTab(self.dc_port.view, 'DC_PORT_{}'.format(self.site + 1))
        tab.addTab(self.dut.view, 'DUT_{}'.format(self.site + 1))
        tab.addTab(self.fixture.view, 'FIXTURE_{}'.format(self.site + 1))
        layout_main = QHBoxLayout()
        layout_main.addWidget(tab)
        layout_main.setContentsMargins(0, 0, 0, 0)
        self.view.setLayout(layout_main)
        self.view.setContentsMargins(0, 0, 0, 0)


class RW(QObject):
    update_data_signal = pyqtSignal(str)

    # cvrt = Ansi2HTMLConverter()

    def __init__(self, pub_port, name='', testengine=None, remote=True):
        super(RW, self).__init__()
        self.test_engine = testengine
        self.remote = remote
        self.item_buff = []
        self.view = QFrame()
        self.txt_recv = QTextBrowser()
        self.cmbox_send = QComboBox()
        self.btn_send = QPushButton('SEND')
        self.btn_clear = QPushButton('CLEAR')
        self._poller = zmq.Poller()
        self.pub_port = pub_port
        self.name = name
        self._receiving = True
        self.subscriber()
        self.create_action()
        self.setup_ui()
        self._init_flag = True

    def create_action(self):
        self.cmbox_send.currentIndexChanged.connect(self.send_cmd)
        self.btn_send.clicked.connect(self.send_cmd)
        self.btn_clear.clicked.connect(self.clear_recv)
        self.update_data_signal.connect(self.update_msg)

    def setup_ui(self):
        self.txt_recv.setLineWrapMode(QTextEdit.NoWrap)
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.txt_recv)
        layout_send = QHBoxLayout()
        self.cmbox_send.setEditable(True)
        self.cmbox_send.setFixedWidth(400)
        layout_send.addWidget(self.cmbox_send)
        layout_send.addWidget(self.btn_send)
        layout_send.addWidget(self.btn_clear)
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_send.addItem(spacer_item)
        layout_send.setSpacing(5)
        layout_send.setContentsMargins(0, 0, 0, 0)
        layout_main.addLayout(layout_send)
        layout_main.setContentsMargins(0, 0, 0, 3)
        layout_main.setSpacing(1)
        self.view.setLayout(layout_main)

    def init_cmd_box(self, cmd_list):
        for cmd in cmd_list:
            if cmd not in self.item_buff:
                self.item_buff.append(cmd)
        self.cmbox_send.addItems(self.item_buff)

    def subscriber(self):
        ctx = zmq.Context().instance()
        url = 'tcp://127.0.0.1:'
        sub_socket = ctx.socket(zmq.SUB)
        address = '{}{}'.format(url, self.pub_port)
        sub_socket.connect(address)
        sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self._poller.register(sub_socket, zmq.POLLIN)
        t = Thread(target=self.receive_sequencer_message)
        t.setDaemon(True)
        t.start()

    def clear_recv(self):
        self.txt_recv.setText('')

    def _get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def receive_sequencer_message(self):
        data_buf = ''
        while self._receiving:
            try:
                socks = dict(self._poller.poll(5000))
                for socket in self._get_sockets():
                    if socket in socks and socks[socket] == zmq.POLLIN:
                        topic, ts, level, origin, data = socket.recv_multipart(zmq.NOBLOCK)
                        if data != 'FCT_HEARTBEAT':
                            data_buf += data
                            l = data_buf.rfind('\n')
                            if l != -1:
                                current_data = data_buf[:l + 1]
                                data_buf = data_buf[l + 1:]
                                self.update_data_signal.emit(current_data.strip())
            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()

        for socket in self._get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def send_cmd(self, f):
        if self._init_flag:
            self._init_flag = False
            return
        cmd = self.cmbox_send.currentText()
        self.cmbox_send.setCurrentText('')
        if cmd not in self.item_buff:
            self.item_buff.append(cmd)
            self.cmbox_send.addItem(cmd)
        if self.test_engine:
            cmd = cmd.encode('utf-8')
            self.update_msg('send: {}'.format(cmd))
            if self.remote:
                response = getattr(self.test_engine.remote_server(), '{}.send'.format(self.name))(cmd)
                if response is None:
                    self.update_msg('Timed out waiting for response from test engine')
                    return
                if hasattr(response, 'error'):
                    self.update_msg(
                        'Test Engine error: ' + str(response._jsonrpc_error_code) + ':' + response.error)
                    return
                if not hasattr(response, 'result'):
                    self.update_msg('Received invalid response : ' + str(response))
                    return
            else:
                self.test_engine.send(cmd)

    def update_msg(self, msg):
        if msg:
            # data = self.cvrt.convert(msg)
            self.txt_recv.append(msg)


class FuncDebug(QObject):
    def __init__(self, functions, testenine):
        super(FuncDebug, self).__init__()
        self.functions = functions
        self.test_engine = testenine
        self.view = QFrame()
        self.func_table = QTableWidget()
        self.txt_reve = QTextBrowser()
        self.setup_ui()
        self.setup_functions()
        self.func_table.cellDoubleClicked.connect(self.func_clicked)

    def setup_ui(self):
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.func_table, 7)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.addWidget(self.txt_reve, 3)
        self.view.setLayout(layout_main)
        self.func_table.setColumnCount(5)
        self.func_table.setColumnWidth(0, 180)
        self.func_table.setColumnWidth(1, 80)
        self.func_table.setColumnWidth(2, 80)
        self.func_table.setColumnWidth(3, 50)
        self.func_table.setColumnWidth(4, 60)

    def setup_functions(self):
        self.func_table.setHorizontalHeaderLabels(['Func', 'Param1', 'Param2', 'UNIT', 'TIMEOUT'])
        self.func_table.horizontalHeader().setSectionsClickable(False)
        self.func_table.sortItems(0, Qt.AscendingOrder)
        row = 0
        self.func_table.setRowCount(len(self.functions))
        self.func_table.setColumnWidth(0, 150)
        for line in self.functions:
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
                response = getattr(self.test_engine.remote_server(), func)(p1, p2, unit=u, timeout=to)
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = DebugContainer()
    controller.show()
    sys.exit(app.exec_())
