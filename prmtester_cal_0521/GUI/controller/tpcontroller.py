#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import Queue

import re
import sys
import csv
import zmq
import time
import traceback
import multiprocessing
from Configure import constant
from Configure import levels
from Configure import events

from threading import Thread,Lock
from subscriber import SequencerSubscriberProcess
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QSplitter, QFrame, QLabel, QVBoxLayout,QTabWidget
from GUI.view.tableview import KTableView
from GUI.model.tablemodel import KTotalTableModel
from GUI.model.failonlymodel import FailOnlyModel

SITE_PATTERN = re.compile(r'Sequencer_(\d+)')


class TestPlanController(QObject):
    tp_all_selected_row_signal = pyqtSignal(int, name='test_plan_all')
    tp_all_selected_row_signal1 = pyqtSignal(int, name='test_plan_all1')
    tp_fail_selected_row_signal = pyqtSignal(int, name='test_plan_fail_only')

    def __init__(self):
        super(TestPlanController, self).__init__()

        self.current_step_identify = []
        self.static_identify = []

        self.slot_under_test = 1
        self._current_slots_row = []
        self._current_row = {}
        self._failed_row = {}
        self._queue_list = []
        self._lock = Lock()
        # self._queue = Queue.Queue()
        self._sequence_start_time = 0
        self._receiving = True
        self._poller = zmq.Poller()
        # 2d array, each line store one slot result values
        self._column_values = []

        # an array to store the if get the sequence done message
        self._sequence_end_flag = []
        # total rows count
        self._tp_row_count = 0
        self._count_timer = QTimer()
        self._count_timer.timeout.connect(self._flash_gui)
        self._count_timer.start(1000)

        self.view = TestPlanView()
        self.tp_all_model = KTotalTableModel(self.tp_all_selected_row_signal)
        self.view.tp_all_view.setModel(self.tp_all_model)
        self.tp_all_model.tp_failed_row_signal.connect(self._add_fail_row_to_list)

        self.tp_fail_model = FailOnlyModel(self.tp_fail_selected_row_signal)
        self.view.tp_fail_view.setModel(self.tp_fail_model)

        self.tp_all_model2 = KTotalTableModel(self.tp_all_selected_row_signal1)
        self.view.tp_all_view2.setModel(self.tp_all_model2)


        # when data change, update table view
        self.tp_all_selected_row_signal.connect(self.view.tp_all_view.selectRow)
        self.tp_fail_selected_row_signal.connect(self.view.tp_fail_view.selectRow)

        self.level = levels.REPORTER

        for i in range(constant.SLOTS):
            self.current_step_identify.append('')
            self._sequence_end_flag.append(False)
            self._column_values.append(list())
            self._current_slots_row.append(dict())

        # self._queue = multiprocessing.Queue()

    def add_subscribers(self):
        _subscriber = SequencerSubscriberProcess(self._queue)
        _subscriber.daemon = True
        _subscriber.start()

        t = Thread(target=self.queue_get, name='tp_queue_get')
        t.setDaemon(True)
        t.start()

    def _flash_gui(self):
        # self.view
        # self.view.tp_all_view2.reset()
        self.view.tp_all_view2.update()

        a = []
        if self._lock.acquire():
            for row in self._queue_list:
                result = self.tp_all_model.get_one_row(row, self.slot_under_test)
                if result:
                    # print "result: ", row, a
                    r = self.tp_all_model.get_one_row_result(row)
                    self.tp_fail_model.insert_fail_row(result, r)
                    a.append(row)
                    # self._queue_list.remove(row)
        for i in a:
            self._queue_list.remove(i)
        self._lock.release()


    def _add_fail_row_to_list(self, row_count):
        if not self._failed_row.get(row_count):
            self._failed_row[row_count] = row_count
            if self._lock.acquire():
                self._queue_list.append(row_count)
                self._lock.release()
            # self._queue.put(row_count)


    def queue_get(self):
        while self._receiving:
            try:
                if self._queue.empty():
                    time.sleep(0.1)
                    continue
                else:
                    site, message = self._queue.get()
                    self.parse_sequencer_message(site, message)
            finally:
                pass

    def load_test_plan(self, tp_path):
        f = open(tp_path, 'rU')
        reader = csv.DictReader(f)
        # GROUP,TID,UNIT,LOW,HIGH
        tp = [[] for i in range(5)]
        self.static_identify = []
        
        for row in reader:
            if row['GROUP'].startswith('#'):
                continue
            tp[0].append(row['GROUP'])
            tp[1].append(row['TID'])
            tp[2].append(row['LOW'])
            tp[3].append(row['HIGH'])
            tp[4].append(row['UNIT'])
            identify = re.sub('\W', '_', '{}_{}'.format(row['GROUP'], row['TID']))
            self.static_identify.append(identify)
        self._tp_row_count = len(tp[0])
        self.tp_all_model.insertColumns(0, 5, None, col_type='test_plan', data=tp, rows=self._tp_row_count)
        self.tp_all_model2.insertColumns(0, 5, None, col_type='test_plan', data=tp, rows=self._tp_row_count)

        self.tp_fail_model.clean_column(0)
        self.view.tp_all_view.set_columns_width()
        self.view.tp_all_view2.set_columns_width()
        self.view.tp_fail_view.set_columns_width([40, 80, 250, 50, 50, 50])

    def set_receiving(self, flag):
        self._receiving = flag

    def parse_sequencer_message(self, site, message):
        try:
            if message.event == events.SEQUENCE_START:
                self.sequence_start(site)

            elif message.event == events.SEQUENCE_END:
                self.sequence_end(site)

            elif message.event == events.ITEM_START:
                data = message.data
                self.current_step_identify[site] = re.sub('\W', '_',
                                                    '{}_{}'.format(data.get('group', ''), data.get('tid', '')))

                self.item_start(site, message)


            elif message.event == events.ITEM_FINISH:
                self.item_finish(site, message)

        except TypeError:
            print traceback.format_exc()

    def sequence_start(self, site):
        s = []
        with open('/vault/sn.txt', 'r') as f:
            a =  f.read().split("\n")
            for i in a:
                if len(i)> 0:
                    s.append(i)
        self.slot_under_test = len(s)
        self._sequence_end_flag[site] = False
        self._column_values[site] = []
        self.tp_all_model.clean_column(site)
        self.tp_fail_model.clean_column(site)
        self.tp_all_model2.clean_column(site)
        self._failed_row.clear()
        self._queue_list = []
        self._sequence_start_time = time.time()

    def sequence_end(self, site):
        self.slot_under_test = self.slot_under_test - 1
        self._sequence_end_flag[site] = True

    def item_start(self, site, message):
        self._current_slots_row[site].update(message.data)
        # self._current_row.update(message.data)

    def item_finish(self, site, message):
        self._current_row.clear()
        self._current_slots_row[site].update(message.data)
        value = message.data['value']
        result = message.data['result']
        self._current_row.update(self._current_slots_row[site].copy())

        if value == "":
            value = '--FAIL--'
        if result == -1:
            result = False

        self._column_values[site].append(value)
        self.update_result(site, value, result)

    def update_result(self, site, value, result):
        # row = len(self._column_values[site]) - 1
        row = self.static_identify.index(self.current_step_identify[site])
        # print site, row, value
        value_index = self.tp_all_model.createIndex(row, site, value)
        self.tp_all_model.setData(value_index, value, role=Qt.EditRole)
        self.tp_all_model2.setData(value_index, value, role=Qt.EditRole)

        result_index = self.tp_all_model.createIndex(row, site, result)
        self.tp_all_model.setData(result_index, result, role=Qt.TextColorRole)
        self.tp_all_model2.setData(result_index, result, role=Qt.TextColorRole)
        # if not result:
        #     self.tp_fail_model.insert_fail_result(row, site, value, result, self._current_row.copy())

    def get_row_count(self):
        return self._tp_row_count

    def reset_result_column(self):
        for i in range(constant.SLOTS):
            self.tp_all_model.clean_column(i)
            self.tp_all_model2.clean_column(i)
        self.tp_fail_model.clean_column(0)
        self._failed_row.clear()


class TestPlanView(QFrame):
    def __init__(self):
        super(TestPlanView, self).__init__()
        self.tp_all_view = KTableView(self)
        self.tp_fail_view = KTableView(self)
        self.tp_all_view2 = KTableView(self)
        self.tp_splitter = QTabWidget()





        self.setFrameStyle(QFrame.NoFrame)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        _frame_tp_all = QFrame()
        _frame_tp_fail = QFrame()
        _frame_tp_all2 = QFrame()

        _tp_fail_layout = QVBoxLayout()
        _tp_fail_layout.setSpacing(0)
        _tp_fail_layout.setContentsMargins(1, 1, 1, 1)
        _tp_all_layout = QVBoxLayout()
        _tp_all_layout.setSpacing(1)
        _tp_all_layout.setContentsMargins(1, 1, 1, 1)

        _tp_all_layout1 = QVBoxLayout()
        _tp_all_layout1.setSpacing(1)
        _tp_all_layout1.setContentsMargins(1, 1, 1, 1)

        # _lbl_fail = QLabel("FAIL RECORDS")
        # _lbl_all = QLabel("ALL RECORDS")

        # _tp_fail_layout.addWidget(_lbl_fail)
        _tp_fail_layout.addWidget(self.tp_fail_view)
        _frame_tp_fail.setLayout(_tp_fail_layout)
        # _tp_all_layout.addWidget(_lbl_all)
        _tp_all_layout.addWidget(self.tp_all_view)
        _frame_tp_all.setLayout(_tp_all_layout)

        _tp_all_layout1.addWidget(self.tp_all_view2)
        _frame_tp_all2.setLayout(_tp_all_layout1)



        main_layout.addWidget(self.tp_splitter)
        self.setLayout(main_layout)
        self.setFrameStyle(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.tp_splitter.addTab(_frame_tp_all, "ALL_RECORDS")
        self.tp_splitter.addTab(_frame_tp_all2, "STATIC_RECORDS")
        self.tp_splitter.addTab(_frame_tp_fail, "FAIL_RECORDS")

        # self.tp_splitter.setOrientation(Qt.Vertical)
        # self.tp_splitter.addWidget(_frame_tp_fail)
        # self.tp_splitter.addWidget(_frame_tp_all)
        # self.tp_splitter.setStretchFactor(0, 1)
        # self.tp_splitter.setStretchFactor(1, 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = TestPlanController()
    controller.view.setGeometry(100, 100, 850, 600)
    controller.view.tp_all_view.set_columns_width()
    controller.view.tp_fail_view.set_columns_width()
    controller.view.show()
    sys.exit(app.exec_())
