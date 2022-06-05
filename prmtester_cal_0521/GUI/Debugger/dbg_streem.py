#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2020, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import zmq
import sys
import traceback
from Configure import zmqports
from threading import Thread
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QListView, QTextEdit, QPushButton, \
    QGridLayout, QLabel, QSpinBox, QSpacerItem, QSizePolicy, QTabWidget, QComboBox, QTextBrowser, QSplitter
from Fixture.fixture_client import FixtureClient
from Fixture.fixture_server import FixtureServer


class DBGFIXTURE(QObject):
    update_data_signal = pyqtSignal(str)

    def __init__(self, name=''):
        super(DBGFIXTURE, self).__init__()
        self.pub_port = zmqports.FIXTURE_CTRL_PUB
        self.item_buff = []
        self.view = QFrame()
        self._poller = zmq.Poller()
        self.name = name
        self._receiving = True
        self.subscriber()
        self.update_data_signal.connect(self.update_msg)
        self.fixture_client = FixtureClient()
        self.setup_ui()
        self.launch_stream_server()

    def setup_ui(self):
        self.cmbox_send = QComboBox()
        btn_in = QPushButton('IN')
        btn_in.clicked.connect(self.do_in)
        btn_out = QPushButton('OUT')
        btn_out.clicked.connect(self.do_out)
        btn_up = QPushButton('UP')
        btn_up.clicked.connect(self.do_up)
        btn_down = QPushButton('DOWN')
        btn_down.clicked.connect(self.do_down)
        btn_send = QPushButton('SEND')
        btn_send.clicked.connect(self.send_cmd)
        btn_clear = QPushButton('CLEAR')
        btn_clear.clicked.connect(self.clear_recv)
        self.txt_recv = QTextBrowser()
        self.txt_recv.setLineWrapMode(QTextEdit.NoWrap)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.txt_recv)
        layout_send = QHBoxLayout()
        self.cmbox_send.setEditable(True)
        self.cmbox_send.setFixedWidth(200)
        layout_send.addWidget(self.cmbox_send)
        layout_send.addWidget(btn_send)
        layout_send.addWidget(btn_clear)
        layout_send.addWidget(btn_in)
        layout_send.addWidget(btn_out)
        layout_send.addWidget(btn_up)
        layout_send.addWidget(btn_down)
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
                self.cmbox_send.addItem(cmd)

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
        while self._receiving:
            try:
                socks = dict(self._poller.poll(5000))
                for socket in self._get_sockets():
                    if socket in socks and socks[socket] == zmq.POLLIN:
                        topic, ts, level, origin, data = socket.recv_multipart(zmq.NOBLOCK)
                        if data != 'FCT_HEARTBEAT':
                            self.update_data_signal.emit(data)
            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()

        for socket in self._get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def send_cmd(self):
        cmd = self.cmbox_send.currentText()
        self.cmbox_send.setCurrentText('')
        if cmd not in self.item_buff:
            self.item_buff.append(cmd)
            self.cmbox_send.addItem(cmd)
        self.fixture_client.send(cmd.encode())

    def do_in(self):
        self.fixture_client.send(b'IN')

    def do_out(self):
        self.fixture_client.send(b'OUT')

    def do_up(self):
        self.fixture_client.send(b'UP')

    def do_down(self):
        self.fixture_client.send(b'DOWN')

    def update_msg(self, msg):
        if msg:
            if not msg.startswith("INTERVAL CHECK STATUS"):
                self.txt_recv.append(msg)

    def launch_stream_server(self):
        pass
        # try:
        #     ss = FixtureServer()
        #     ss.start()
        # except:
        #     pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = DBGFIXTURE()
    controller.view.show()
    sys.exit(app.exec_())
