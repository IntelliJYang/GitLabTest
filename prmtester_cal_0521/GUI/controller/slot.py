#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import time
import traceback
from Configure import constant, events
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QRadioButton, QTextEdit, QApplication, QPlainTextEdit
from Configure.driver_config import FIXTURE_SERIAL_PORT
from GUI.resources.style.ui_style import KColor, KFont


class SlotController(QObject):
    progress_signal = pyqtSignal(float)
    update_state_signal = pyqtSignal(str)
    disable_radio_sn_signal = pyqtSignal(bool)

    def __init__(self, group, site, change_page_signal=None):
        super(SlotController, self).__init__()
        self._site = site
        self._group = group
        self._row_count = 1
        self._current_row = 0
        self._change_page_signal = change_page_signal
        self.view = SlotView(group, site, change_page_signal)
        self.create_action()

    def create_action(self):
        self.progress_signal.connect(self.view.update_progress)
        self.update_state_signal.connect(self.view.update_state)
        self.disable_radio_sn_signal.connect(self.view.radio_sn.setDisabled)

    def parse_sequencer_message(self, message):
        try:
            if message.event == events.SEQUENCE_START:
                self.sequence_start()

            elif message.event == events.SEQUENCE_END:
                self.sequence_end(message)

            elif message.event == events.ITEM_FINISH:
                self.item_finish(message)

            elif message.event == events.ITEM_START:
                self.item_start(message)
        except Exception as e:
            print e, traceback.format_exc()

    def sequence_start(self):
        self.disable_radio_sn_signal.emit(True)
        self._current_row = 0
        self.update_state_signal.emit('running')

    def sequence_end(self, message):
        self.disable_radio_sn_signal.emit(False)
        result = 0
        try:
            result = message.data.get('result', 0)
        except Exception as e:
            print e, traceback.format_exc()
        finally:
            if result > 0:
                self.update_state_signal.emit('pass')
            else:
                self.update_state_signal.emit('fail')

    def item_start(self, message):
        pass

    def item_finish(self, message):
        self._current_row += 1.0
        self.progress_signal.emit(self._current_row / self._row_count * 100)

    def write_e_traveler(self, e_traveler):
        self.view.txt_info.setHtml(FIXTURE_SERIAL_PORT)
        self.view.txt_info.setAlignment(Qt.AlignCenter)
        self.view.txt_info.append(e_traveler.get('sn'))
        self.view.txt_info.append(e_traveler.get('cfg'))

    def set_row_count(self, row_count):
        self._row_count = row_count

    def is_checked(self):
        return self.view.radio_sn.isChecked()

    def reset(self):
        self.view.update_state('idle')
        self.view.lbl_progress.setText('0.00 %')


class SlotView(QFrame):
    def __init__(self, group, site, change_page_signal):
        super(SlotView, self).__init__()
        self._site = site
        self._group = group
        self._change_page_signal = change_page_signal
        self._total = 0
        self._state = "IDLE"

        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        if constant.GROUPS > 1:
            self.lbl_slot_name = QLabel('Slot {}-{}'.format(group, site+1))
        else:
            self.lbl_slot_name = QLabel('Slot {}'.format(site+1))
        self.lbl_slot_name.setFont(KFont.FONT_28)

        self.radio_sn = QRadioButton("WAITING...")
        self.radio_sn.setChecked(True)
        self.radio_sn.setFont(KFont.FONT_28)
        self.radio_sn.clicked.connect(self.state_changed)

        self.txt_info = QTextEdit()
        self.txt_info.setFrameShape(QFrame.NoFrame)
        self.txt_info.setReadOnly(True)
        self.txt_info.setAlignment(Qt.AlignCenter)
        self.txt_info.setDisabled(True)
        self.txt_info.append(FIXTURE_SERIAL_PORT)

        self.lbl_result = QLabel()
        self.lbl_result.setFont(KFont.FONT_36)

        self.lbl_progress = QLabel('0.00 %')
        self.lbl_progress.setFixedWidth(130)
        self.lbl_progress.setAlignment(Qt.AlignRight)
        self.lbl_progress.setFont(KFont.FONT_28)

        main_layout.addWidget(self.lbl_slot_name, stretch=1, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.radio_sn, stretch=1, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.txt_info, stretch=1, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.lbl_progress, stretch=2, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.lbl_result, stretch=3, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)
        self.lbl_result.setText("IDLE")

        self.setMaximumWidth(250)
        # self.setMinimumWidth(200)
        self.setMaximumHeight(300)
        # self.setMinimumHeight(200)

        self.set_style_sheet(KColor.state_idle)
        self.setFrameStyle(QFrame.StyledPanel)

    def mousePressEvent(self, mouse_event):
        if self._state != "DISABLE":
            if self._change_page_signal:
                self._change_page_signal.emit(self._group * constant.SLOTS + self._site)

    def leaveEvent(self, event):
        self.setStyleSheet(KColor.LEFT_COLOR.get(self._state.upper()))

    def enterEvent(self, event):
        self.setStyleSheet(KColor.STATE_COLOR.get(self._state.upper()))

    def state_changed(self):
        if self.radio_sn.isChecked():
            self._state = "IDLE"
            self.lbl_result.setText("IDLE")
        else:
            self._state = "DISABLE"
            self.lbl_result.setText("DISABLE")
            self.lbl_progress.setText('0.00 %')
        self.setStyleSheet(KColor.LEFT_COLOR.get(self._state.upper()))

    def update_progress(self, data):
        self.lbl_progress.setText(format(data, '0.2f') + ' %')

    def update_state(self, state):
        self._state = state
        self.lbl_result.setText(state.upper())
        self.set_style_sheet(KColor.STATE_COLOR.get(self._state.upper()))

    def set_style_sheet(self, style):
        try:
            self.setStyleSheet(style)
        except Exception as e:
            print e, traceback.format_exc()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    con = SlotController(0, 0)
    con.view.show()
    sys.exit(app.exec_())
