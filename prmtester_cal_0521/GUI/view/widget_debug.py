#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import thread
from PyQt5.QtWidgets import QFrame, QGridLayout, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QLabel, QApplication
from PyQt5.QtCore import Qt, QObject
from Common.prm_sdb import SequencerDebugger
from GUI.resources.style.ui_style import KColor


class DebugWidgetController(QObject):
    def __init__(self, site, signal):
        super(DebugWidgetController, self).__init__()
        self.view = DebugWidgetView(site)
        self._site = site
        self._sdb = SequencerDebugger()
        self._sdb.create_server(self._site)
        self._signal = signal
        self.create_actions()

    def create_actions(self):
        self.view.btn_clean.clicked.connect(self.clean_action)
        self.view.btn_step.clicked.connect(self.step_action)
        self.view.btn_break.clicked.connect(self.break_action)
        self.view.btn_jump.clicked.connect(self.jump_action)
        self.view.btn_skip.clicked.connect(self.skip_action)

    def clean_action(self):
        if self._signal:
            self._signal.emit('clean', self._site, 0)

    def step_action(self):
        if self._sdb and self._sdb.sequencer:
            thread.start_new_thread(self._sdb.do_step, (0,))
            current_row = int(self.view.lbl_step.text())
            self.view.lbl_step.setText(str(current_row + 1))
            if self._signal:
                self._signal.emit('row', self._site, current_row)

    def break_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_break, (self.view.spinbox_break.value(),))
            current_row = self.view.spinbox_break.value()
            self.view.lbl_step.setText(str(current_row + 1))
            if self._signal:
                self._signal.emit('row', self._site, current_row)

    def skip_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_skip, (0,))
            current_row = int(self.view.lbl_step.text())
            self.view.lbl_step.setText(str(current_row + 1))
            if self._signal:
                self._signal.emit('row', self._site, current_row)

    def jump_action(self):
        if self._sdb:
            thread.start_new_thread(self._sdb.do_jump, (self.view.spinbox_jump.value(),))
            current_row = self.view.spinbox_jump.value()
            self.view.lbl_step.setText(str(current_row + 1))
            if self._signal:
                self._signal.emit('row', self._site, current_row)


class DebugWidgetView(QFrame):

    def __init__(self, site, parent=None):
        super(DebugWidgetView, self).__init__(parent)
        main_layout = QGridLayout()
        self.lbl_site = QLabel('SLOT' + str(site))
        self.lbl_site.setAlignment(Qt.AlignCenter)
        self.btn_connect = QPushButton("Connect")

        self.btn_step = QPushButton("Step")
        self.lbl_step = QLabel('0')
        self.lbl_step.setFixedWidth(70)

        self.btn_jump = QPushButton("Jump")
        self.spinbox_jump = QSpinBox()
        self.spinbox_jump.setMinimum(0)
        self.spinbox_jump.setMaximum(100000)
        self.spinbox_jump.setFixedWidth(70)

        self.btn_skip = QPushButton("Skip")
        self.btn_break = QPushButton("Break")
        self.spinbox_break = QSpinBox()
        self.spinbox_break.setMinimum(0)
        self.spinbox_break.setMaximum(100000)
        self.spinbox_break.setFixedWidth(70)
        self.btn_continue = QPushButton("Continue")

        self.btn_clean = QPushButton("Clean")
        main_layout.addWidget(self.lbl_site, 0, 0, 1, 2)

        main_layout.addWidget(self.btn_step, 1, 0, 1, 1)
        main_layout.addWidget(self.lbl_step, 1, 1, 1, 1)

        main_layout.addWidget(self.btn_skip, 2, 0, 1, 2)

        main_layout.addWidget(self.btn_jump, 3, 0, 1, 1)
        main_layout.addWidget(self.spinbox_jump, 3, 1, 1, 1)

        main_layout.addWidget(self.btn_continue, 4, 0, 1, 2)
        main_layout.addWidget(self.btn_break, 5, 0, 1, 1)
        main_layout.addWidget(self.spinbox_break, 5, 1, 1, 1)

        main_layout.addWidget(self.btn_clean, 6, 0, 1, 2)
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addItem(spacer_item)
        main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(main_layout)
        self.setStyleSheet(KColor.bg_orange)
        self.setFixedSize(160, 200)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = DebugWidgetController(0, None)
    controller.view.show()
    sys.exit(app.exec_())
