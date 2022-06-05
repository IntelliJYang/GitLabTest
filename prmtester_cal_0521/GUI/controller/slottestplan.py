#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import re
import sys
import zmq
import time
import traceback
from Configure import events, zmqports, levels, constant
from threading import Thread
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QSplitter, QFrame, QVBoxLayout, QHBoxLayout, QToolButton, QLabel, QApplication
from GUI.view.tableview import KTableView
from GUI.model.slotmodel import SlotTpTableModel
from GUI.view.pluginswiget import Counter
from GUI.resources.style.ui_style import KFont
from GUI.protocal.sequencerprotocal import SequencerProtocol


class SlotTpController(QObject):
    slot_tp_all_selected_row_signal = pyqtSignal(int, name='slot_tp_all_selected_row_signal')
    slot_fail_tp_selected_row_signal = pyqtSignal(int, name='slot_fail_tp_selected_row_signal')
    timer_signal = pyqtSignal(bool)

    def __init__(self, group, site, change_page_signal=None):
        super(SlotTpController, self).__init__()
        self._receving = True
        self._level = levels.REPORTER
        self._group = group
        self._site = site
        self._change_page_signal = change_page_signal
        self.view = SlotTpView(group, site)
        self._current_row = {}
        self.tp_fail_model = SlotTpTableModel(self.slot_fail_tp_selected_row_signal)
        self.tp_all_model = SlotTpTableModel(self.slot_tp_all_selected_row_signal)

        self.view.slot_tp_all_view.setModel(self.tp_all_model)
        self.slot_tp_all_selected_row_signal.connect(self.view.slot_tp_all_view.selectRow)

        self.view.slot_tp_fail_view.setModel(self.tp_fail_model)
        self.slot_fail_tp_selected_row_signal.connect(self.view.slot_tp_fail_view.selectRow)
        self.view.btn_back.clicked.connect(self.change_page)
        self.timer_signal.connect(self.slot_tp_timer)

        # self.add_subscribers()

    def change_page(self):
        if self._change_page_signal:
            self._change_page_signal.emit(-1)

    def add_subscribers(self):
        ctx = zmq.Context()
        url = 'tcp://127.0.0.1:'
        sub_socket = ctx.socket(zmq.SUB)
        address = '{}{}'.format(url, zmqports.SEQUENCER_PUB + self._site)
        sub_socket.connect(address)
        sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        t = Thread(target=self.receive_message, args=(sub_socket,))
        t.setDaemon(True)
        t.start()

    def receive_message(self, socket):
        while self._receving:
            try:
                topic, ts, level, origin, data = socket.recv_multipart(zmq.NOBLOCK)
                if int(level) == self._level:
                    message = SequencerProtocol.parse_report(data)
                    self.parse_sequencer_message(message)
                else:
                    time.sleep(0.001)
            except zmq.ZMQError:
                time.sleep(0.1)
                continue

    def parse_sequencer_message(self, message):
        try:
            if message.event == events.SEQUENCE_START:
                self.timer_signal.emit(True)
                self.sequence_start()

            elif message.event == events.SEQUENCE_END:
                self.timer_signal.emit(False)
                self.sequence_end()

            elif message.event == events.ITEM_FINISH:
                self.item_finish(message)

            elif message.event == events.ITEM_START:
                self.item_start(message)

        except TypeError:
            print traceback.format_exc()

    def slot_tp_timer(self, flag):
        if flag:
            self.view.lbl_test_time.start_the_timer()
        else:
            self.view.lbl_test_time.stop_the_timer()

    def sequence_start(self):
        self._current_row.clear()

    def sequence_end(self):
        pass

    def item_start(self, message):
        self._current_row.update(message.data)

    def item_finish(self, message):
        self._current_row.update(message.data)
        self.tp_all_model.insertRows(data=self._current_row)
        if int(self._current_row['result']) != 1:
            self.tp_fail_model.insertRows(data=self._current_row)

    def reset(self):
        self.tp_fail_model.clear()
        self.tp_all_model.clear()
        self.view.tp_splitter.setStretchFactor(0, 1)
        self.view.tp_splitter.setStretchFactor(1, 2)
        self.view.lbl_test_time.setText('0 s')


class SlotTpView(QFrame):
    def __init__(self, group, site):
        super(SlotTpView, self).__init__()

        self._group = group
        self._site = site
        main_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(1, 1, 1, 1)
        header_layout.setSpacing(5)

        self.btn_back = QToolButton()
        self.btn_back.setText('<')
        self.btn_back.setFont(KFont.FONT_24)
        if constant.GROUPS > 1:
            self.lbl_unit = QLabel('Unit {}-{}'.format(group, site+1))
        else:
            self.lbl_unit = QLabel('Unit {}'.format(site+1))
        self.lbl_unit.setFont(KFont.FONT_24)

        self.lbl_test_time = Counter()
        self.lbl_test_time.setFont(KFont.FONT_24)

        header_layout.addWidget(self.btn_back)
        header_layout.addWidget(self.lbl_unit)
        header_layout.addWidget(self.lbl_test_time, alignment=Qt.AlignRight)
        main_layout.addLayout(header_layout)

        self.tp_splitter = QSplitter()
        self.tp_splitter.setContentsMargins(1, 1, 1, 1)
        self.slot_tp_all_view = KTableView(self)
        self.slot_tp_fail_view = KTableView(self)

        self.layout_tp_view()

        main_layout.addWidget(self.tp_splitter)
        main_layout.setContentsMargins(10, 10, 0, 0)
        main_layout.setSpacing(5)
        self.setLayout(main_layout)

    def layout_tp_view(self):
        _frame_tp_all = QFrame()
        _frame_tp_fail = QFrame()

        _tp_fail_layout = QVBoxLayout()
        _tp_fail_layout.setSpacing(0)
        _tp_fail_layout.setContentsMargins(1, 1, 1, 1)
        _tp_all_layout = QVBoxLayout()
        _tp_all_layout.setSpacing(1)
        _tp_all_layout.setContentsMargins(1, 1, 1, 1)
        _lbl_fail = QLabel("FAIL RECORDS")
        _lbl_all = QLabel("ALL RECORDS")

        _tp_fail_layout.addWidget(_lbl_fail)
        _tp_fail_layout.addWidget(self.slot_tp_fail_view)
        _frame_tp_fail.setLayout(_tp_fail_layout)

        _tp_all_layout.addWidget(_lbl_all)
        _tp_all_layout.addWidget(self.slot_tp_all_view)
        _frame_tp_all.setLayout(_tp_all_layout)

        self.tp_splitter.setOrientation(Qt.Vertical)
        self.tp_splitter.addWidget(_frame_tp_fail)
        self.tp_splitter.addWidget(_frame_tp_all)
        self.tp_splitter.setStretchFactor(0, 1)
        self.tp_splitter.setStretchFactor(1, 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = SlotTpController(0, 0)
    controller.view.show()
    sys.exit(app.exec_())
