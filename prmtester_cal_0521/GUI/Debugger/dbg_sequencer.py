#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2020, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

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
    QTableWidget, QTableWidgetItem, QMessageBox, QAbstractSpinBox
from Fixture.fixture_client import FixtureClient


class SeqDebug(QObject):
    update_data_signal = pyqtSignal(str)

    def __init__(self, site=0):
        super(SeqDebug, self).__init__()
        self.site = site
        self.current_method = ''
        self._poller = zmq.Poller()
        self._receiving = True
        self._sdb = SequencerDebugger()
        self._sdb.create_server(site)
        self.view = QFrame()
        self.btn_connect = QPushButton("Connect")
        self.btn_step = QPushButton("Step")
        self.lbl_step = QLabel('0')

        self.btn_jump = QPushButton("Jump")
        self.spinbox_jump = QSpinBox()
        self.spinbox_jump.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.btn_skip = QPushButton("Skip")
        self.btn_break = QPushButton("Break")
        self.spinbox_break = QSpinBox()
        self.spinbox_break.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.btn_continue = QPushButton("Continue")
        self.btn_abort = QPushButton('Abort')
        self.btn_clean = QPushButton("Clean")
        self.txt_msg = QTextBrowser()

        self.btn_in = QPushButton("IN")
        self.btn_out = QPushButton("OUT")
        self.btn_up = QPushButton("UP")
        self.btn_down = QPushButton("DOWN")

        self.create_actions()
        self.setup_ui()
        self.subscribe_sequencer()
        self.update_data_signal.connect(self.update_msg)
        self.fixture_client = FixtureClient()

    def create_actions(self):
        self.btn_clean.clicked.connect(self.clean)
        self.btn_step.clicked.connect(self.step_action)
        self.btn_break.clicked.connect(self.break_action)
        self.btn_jump.clicked.connect(self.jump_action)
        self.btn_skip.clicked.connect(self.skip_action)
        self.btn_abort.clicked.connect(self.abort_action)
        self.btn_continue.clicked.connect(self.continue_action)

        self.btn_in.clicked.connect(self.do_in)
        self.btn_out.clicked.connect(self.do_out)
        self.btn_up.clicked.connect(self.do_up)
        self.btn_down.clicked.connect(self.do_down)

    def setup_ui(self):
        self.lbl_step.setStyleSheet(KColor.bg_white)
        self.lbl_step.setFixedHeight(20)
        self.lbl_step.setFixedWidth(50)
        self.spinbox_jump.setMinimum(0)
        self.spinbox_jump.setMaximum(100000)
        # self.spinbox_jump.setFixedWidth(50)
        self.spinbox_break.setMinimum(0)
        self.spinbox_break.setMaximum(100000)
        # self.spinbox_break.setFixedWidth(50)
        layout_main = QVBoxLayout()
        layout_tool = QGridLayout()
        layout_tool.addWidget(self.btn_step, 0, 0, 1, 1)
        layout_tool.addWidget(self.lbl_step, 1, 0, 1, 1)
        layout_tool.addWidget(self.btn_skip, 0, 1, 1, 1)
        layout_tool.addWidget(self.btn_jump, 0, 2, 1, 1)
        layout_tool.addWidget(self.spinbox_jump, 1, 2, 1, 1)
        layout_tool.addWidget(self.btn_continue, 0, 3, 1, 1)
        layout_tool.addWidget(self.btn_break, 0, 4, 1, 1)
        layout_tool.addWidget(self.spinbox_break, 1, 4, 1, 1)
        layout_tool.addWidget(self.btn_abort, 0, 5, 1, 1)
        layout_tool.addWidget(self.btn_clean, 0, 6, 1, 1)
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_tool.addItem(spacer_item, 0, 7, 1, 1)
        layout_tool.setContentsMargins(0, 0, 0, 0)
        layout_tool.setSpacing(2)

        layout_main.addLayout(layout_tool)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.addWidget(self.txt_msg)

        layout_fix = QHBoxLayout()
        layout_fix.addWidget(self.btn_in)
        layout_fix.addWidget(self.btn_out)
        layout_fix.addWidget(self.btn_up)
        layout_fix.addWidget(self.btn_down)

        layout_main.addLayout(layout_fix)
        self.txt_msg.setLineWrapMode(QTextEdit.NoWrap)
        layout_main.setSpacing(1)
        self.view.setLayout(layout_main)
        self.view.setContentsMargins(0, 0, 0, 0)

    def clean(self):
        self.txt_msg.setText('')
        thread.start_new_thread(self._sdb.do_clear, ())

    def step_action(self):
        if self._sdb and self._sdb.sequencer:
            try:
                reply = self._sdb.do_next()
                if hasattr(reply, 'result'):
                    self.lbl_step.setText(str(reply.result))
                else:
                    self.txt_msg.append(str(reply))
            except:
                pass

            thread.start_new_thread(self._sdb.do_step, ())

    def break_action(self):
        if self._sdb:
            self._sdb.do_break(self.spinbox_break.value())
            brakpoints = self._sdb.do_all()
            self.update_msg('Breakpoints: {}'.format(brakpoints))

    def skip_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_skip, (0,))
            current_row = int(self.lbl_step.text())
            self.lbl_step.setText(str(current_row + 1))

    def jump_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_jump, (self.spinbox_jump.value() + 1,))
            current_row = self.spinbox_jump.value()
            self.lbl_step.setText(str(current_row))

    def continue_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_continue, (self.lbl_step,))

    def abort_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_abortcontinue, ())

    def subscribe_sequencer(self):
        ctx = zmq.Context().instance()
        url = 'tcp://127.0.0.1:'
        sub_socket = ctx.socket(zmq.SUB)
        address = '{}{}'.format(url, zmqports.SEQUENCER_PUB + self.site)
        sub_socket.connect(address)
        sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self._poller.register(sub_socket, zmq.POLLIN)
        t = Thread(target=self.receive_sequencer_message, name='testplan_sequencer_{}'.format(self.site))
        t.setDaemon(True)
        t.start()

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
                            try:
                                msg = self.parse_result(data)
                            except:
                                msg = ''
                            self.update_data_signal.emit(msg)
            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()

        for socket in self._get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def parse_result(self, message):
        if message.startswith('running test '):
            msg = message[13:].replace('\'', '\"')
            rowdict = json.loads(msg)
            line = 'running test --> {} | {} | {} | {} | {} | {} | {} | {} | {}\n'.format(
                rowdict.get('GROUP', ''),
                rowdict.get('TID', ''),
                rowdict.get('SUBSUBTESTNAME', ''),
                rowdict.get('LOW', ''),
                rowdict.get('HIGH', ''),
                rowdict.get('UNIT', ''),
                rowdict.get('FUNCTION', ''),
                rowdict.get('PARAM1', ''),
                rowdict.get('PARAM2', ''))
            return line
        elif message.startswith('{"data": {"tid":'):
            return message
        else:
            return ''

    def update_msg(self, msg):
        if msg == '':
            return
        line = msg
        if 'error' in line:
            self.txt_msg.append("<font color=red>%s</font>" % line)
        elif 'Breakpoints' in line:
            self.txt_msg.append("<font color=blue>%s</font>" % line)
        elif line.startswith('running test '):
            self.txt_msg.append("<font color=#ff9900>%s</font>" % line)
        elif msg.startswith('{"data": {"tid":'):
            # self.txt_msg.append("<font color=blue>%s</font>" % line)
            try:
                ret = json.loads(msg)
                result = ret['data'].get('result', False)
                value = ret['data'].get('value', '')
                if 'SKIP' in str(value):
                    self.txt_msg.append("<font color=#C0C0C0>%s</font>" % value)
                else:
                    if result:
                        self.txt_msg.append("<font color=green>%s</font>" % value)
                    else:
                        self.txt_msg.append("<font color=red>%s</font>" % value)
            except:
                pass
        else:
            self.txt_msg.append("<font color=black>%s</font>" % line)

    def do_in(self):
        ret = self.fixture_client.send(b'IN')
        self.update_data_signal.emit(ret)

    def do_out(self):
        ret = self.fixture_client.send(b'OUT')
        self.update_data_signal.emit(ret)

    def do_up(self):
        ret = self.fixture_client.send(b'UP')
        self.update_data_signal.emit(ret)

    def do_down(self):
        ret = self.fixture_client.send(b'DOWN')
        self.update_data_signal.emit(ret)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = SeqDebug(0)
    controller.view.show()
    sys.exit(app.exec_())
