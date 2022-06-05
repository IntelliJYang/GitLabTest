#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import traceback
import time
from PyQt5.QtWidgets import QFrame, QPushButton, QApplication, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from GUI.view.pluginswiget import BusyWidget, MyLineText, MyLabel
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject


class LoopController(object):

    def __init__(self, loop_signal):
        super(LoopController, self).__init__()
        self.view = LoopView(loop_signal=loop_signal)
        # self._timer = QTimer()
        self._create_action()
        self._loop_signal = loop_signal
        self._current_loop_time = 0
        self.looping = False

    def _create_action(self):
        self.view.loop_in.clicked.connect(self._loop_in)
        self.view.loop_out.clicked.connect(self._loop_out)
        self.view.timer_signal.connect(self.view.gif_busy.control_action)

    def _loop_in(self):
        self.looping = True
        self.view.timer_signal.emit(True)
        if self._loop_signal:
            self._loop_signal.emit('start')
        self.view.loop_in.setDisabled(True)
        self.view.loop_out.setDisabled(False)
        self._current_loop_time = 1
        self.view.current_loop.value = "1"

    def _loop_out(self):
        self.view.timer_signal.emit(False)
        if self._loop_signal:
            self._loop_signal.emit('abort')
        self.looping = False
        self.view.loop_in.setDisabled(False)
        self.view.loop_out.setDisabled(True)

    def set_loop_out(self):
        self._loop_out()

    def next_round(self):
        time.sleep(1)
        if self.looping:
            cycle_time = int(self.view.loop_count.getValue())
            if self._current_loop_time < cycle_time:
                wait_second = float(self.view.time_interval.getValue())
                time.sleep(wait_second / 1000.0)
                self._loop_signal.emit('start')
                self._current_loop_time += 1
                self.view.current_loop.value = str(self._current_loop_time)

            else:
                self._loop_signal.emit('abort')
                self.view.timer_signal.emit(False)
                self.view.loop_in.setDisabled(False)
                self.view.loop_out.setDisabled(True)
                self.looping = False
        else:
            self._loop_signal.emit('abort')


class LoopView(QFrame):
    timer_signal = pyqtSignal(bool)

    def __init__(self, parent=None, loop_signal=None):
        super(LoopView, self).__init__(flags=Qt.WindowStaysOnTopHint)
        self._signal = loop_signal
        self.prm_parent = parent
        self.loop_in = QPushButton("Loop In")
        self.loop_out = QPushButton("Loop Out")
        self.resize(250, 180)
        mainlayout = QVBoxLayout()
        self.loop_count = MyLineText(position='LEFT')
        self.loop_count.setName("Loop Count:")
        self.loop_count.setValue("10")
        h_time_layout = QHBoxLayout()
        h_time_layout.addWidget(self.loop_in, 1)
        h_time_layout.addWidget(self.loop_out, 1)
        h_time_layout.setContentsMargins(20, 0, 20, 0)
        h_time_layout.setSpacing(0)
        self.time_interval = MyLineText(position='LEFT')
        self.time_interval.setName("Time Interval(ms):")
        self.time_interval.setValue("5000")
        self.current_loop = MyLabel(position='LEFT')
        self.current_loop.name = "Current Loop:"
        self.current_loop.value = "0"

        waitlayout = QHBoxLayout()
        self.gif_busy = BusyWidget()
        waitlayout.setSpacing(0)
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        waitlayout.addItem(spacer_item)
        waitlayout.addWidget(self.gif_busy)
        waitlayout.addItem(spacer_item)

        waitlayout.setContentsMargins(0, 0, 0, 0)
        mainlayout.addWidget(self.loop_count, 1)
        mainlayout.addWidget(self.time_interval, 1)
        mainlayout.addWidget(self.current_loop, 1)
        mainlayout.addLayout(waitlayout)
        mainlayout.addLayout(h_time_layout, 1)
        mainlayout.setContentsMargins(10, 10, 10, 0)
        mainlayout.setSpacing(3)

        self.loop_out.setDisabled(True)
        self.setWindowTitle("LoopTest")
        self.setLayout(mainlayout)
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def closeEvent(self, event):
        try:
            if self._signal:
                self._signal.emit('hide')
                self.hide()
        except Exception as e:
            print e, traceback.format_exc()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = LoopController(None)
    controller.view.show()
    sys.exit(app.exec_())
