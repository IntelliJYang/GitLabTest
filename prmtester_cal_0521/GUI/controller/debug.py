#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import csv
import zmq
import time
import re
import traceback
from Configure import zmqports
from threading import Thread
from Configure import levels
from Configure import events
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from GUI.view.widget_debug import DebugWidgetController
from Configure import constant
from GUI.resources.style.ui_style import KColor
from GUI.view.tableview import KTableView
from GUI.model.tablemodel import KTotalTableModel
from GUI.protocal.sequencerprotocal import SequencerProtocol


class DebugController(QObject):
    selected_row_signal = pyqtSignal(int, name='debug_row_select')
    interact_signal = pyqtSignal(str, int, int)

    def __init__(self):
        super(DebugController, self).__init__()
        self.view = DebugView(self.interact_signal)
        self._poller = zmq.Poller()
        self.tp_model = KTotalTableModel(self.selected_row_signal)
        self.view.table_view.setModel(self.tp_model)
        self._tp_row_count = 0
        self._receiving = True
        self.level = levels.REPORTER
        self._current_row = [0 for i in range(constant.SLOTS)]
        self.create_actions()

    def create_actions(self):
        self.interact_signal.connect(self.set_current_row)
        self.selected_row_signal.connect(self.view.table_view.selectRow)

    def load_test_plan(self, tp_path):
        f = open(tp_path, 'rU')
        reader = csv.DictReader(f)
        # GROUP,TID,UNIT,LOW,HIGH
        tp = [[] for i in range(5)]
        for row in reader:
            if row['GROUP'].startswith('#'):
                continue
            tp[0].append(row['GROUP'])
            tp[1].append(row['TID'])
            tp[2].append(row['LOW'])
            tp[3].append(row['HIGH'])
            tp[4].append(row['UNIT'])
        self._tp_row_count = len(tp[0])
        self.tp_model.insertColumns(0, 5, None, col_type='test_plan', data=tp, rows=self._tp_row_count)
        self.view.table_view.set_columns_width()

    def add_subscribers_of_sequencers(self):
        ctx = zmq.Context()
        url = 'tcp://127.0.0.1:'
        for i in range(constant.SLOTS):
            sub_socket = ctx.socket(zmq.SUB)
            address = '{}{}'.format(url, zmqports.SEQUENCER_PUB + i)
            sub_socket.connect(address)
            sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
            self._poller.register(sub_socket, zmq.POLLIN)
        t = Thread(target=self.receive_sequencers_message, name='testplan_sequencer')
        t.setDaemon(True)
        t.start()

    def _get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def receive_sequencers_message(self):
        site_pattern = re.compile(r'Sequencer_(\d+)')
        while self._receiving:
            try:
                socks = dict(self._poller.poll(1000))
                for socket in self._get_sockets():
                    if socket in socks and socks[socket] == zmq.POLLIN:
                        topic, ts, level, origin, data = socket.recv_multipart(zmq.NOBLOCK)
                        if int(level) == self.level:
                            site = int(re.match(site_pattern, origin).group(1))
                            self.receive_sequencer_message(site, data)

            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()

        for socket in self._get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def receive_sequencer_message(self, site, message):
        try:
            message = SequencerProtocol.parse_report(message)
            if message.event == events.SEQUENCE_START:
                pass

            elif message.event == events.SEQUENCE_END:
                print 'site: {} spend: {}'.format(site, time.time() - self._sequence_start_time)

            elif message.event == events.ITEM_FINISH:
                value = message.data['value']
                result = message.data['result']
                self.update_result(site, value, result)

        except Exception as e:
            print e, traceback.format_exc()

    def update_result(self, site, value, result):
        # default result is True , only update list if detect false

        row = self._current_row[site]
        value_index = self.tp_model.createIndex(row, site, value)
        self.tp_model.setData(value_index, value, role=Qt.EditRole)

        result_index = self.tp_model.createIndex(row, site, result)
        self.tp_model.setData(result_index, result, role=Qt.TextColorRole)

    def set_receiving(self, flag):
        self._receiving = flag

    def set_current_row(self, act, site, row):
        if act == 'row':
            self._current_row[site] = row
        elif act == 'clean':
            self.tp_model.clean_column(site)


class DebugView(QFrame):
    def __init__(self, interact_signal):
        super(DebugView, self).__init__()
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.debug_tool_c = []
        self.table_view = KTableView()
        main_layout = QVBoxLayout()
        debug_tool_layout = QHBoxLayout()
        debug_tool_layout.addItem(spacer_item)
        for i in range(1):
            tool = DebugWidgetController(i, interact_signal)
            self.debug_tool_c.append(tool)
            debug_tool_layout.addWidget(tool.view)

        main_layout.addLayout(debug_tool_layout)
        tp_layout = QHBoxLayout()
        tp_layout.addWidget(self.table_view)
        main_layout.addLayout(tp_layout)
        main_layout.addItem(spacer_item)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_layout)
        self.setStyleSheet(KColor.bg_white)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = DebugController()
    controller.view.show()
    sys.exit(app.exec_())
