#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import time
import traceback
from PyQt5.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QApplication, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from GUI.resources.style.ui_style import KFont, KColor

STATUS = ("WAITING", "DISABLE", "PASS", "FAIL", "TESTING", "UUT")


class SnSlotController(QObject):
    change_slot_state_signal = pyqtSignal(str)
    lbl_sn_signal = pyqtSignal(str)

    def __init__(self, slot):
        super(SnSlotController, self).__init__()
        self._slot = slot
        self.view = SingleSlotView(slot)
        self.create_actions()
        self.create_action()
        self.change_slot_state_signal.emit('normal')

    def create_action(self):
        self.change_slot_state_signal.connect(self.change_slot_state)
        self.lbl_sn_signal.connect(self.view.lbl_sn.setText)
        self.view.chkbox_enable.clicked.connect(self.check_slot)

    def get_e_traveler(self):
        e_traveler = {}
        sn = None
        if self.view.chkbox_enable.isChecked():
            sn = self.view.lbl_sn.text()
        e_traveler.setdefault(str(self._slot), {"attributes": {"MLBSN": sn}})
        return e_traveler

    def check_slot(self):
        if self.view.chkbox_enable.isChecked():
            return True
        else:
            return False


        # # print self.view.chkbox_enable.text()
        # if self.view.chkbox_enable.text():
        #     return False
        # else:
        #     return True

    def set_e_traveler(self, sn, enable):
        if enable:
            self.change_slot_state_signal.emit('normal')
            self.lbl_sn_signal.emit(sn.upper())
        else:
            self.change_slot_state_signal.emit('disable')

    def set_sn(self, sn):
        self.lbl_sn_signal.emit(sn.upper())

    def create_actions(self):
        self.view.chkbox_enable.stateChanged.connect(self.enable_action)

    def change_slot_state(self, result):
        self.result = result
        if result == 'normal':
            self.view.setStyleSheet(KColor.bg_orange)
            self.view.lbl_sn.setText(STATUS[0])
            self.view.lbl_result.setText(str(self._slot))
            self.view.chkbox_enable.setChecked(True)
        elif result == 'fail':
            self.view.setStyleSheet(KColor.bg_red)
        elif result == 'disable':
            self.view.setStyleSheet(KColor.bg_grey)
            self.view.lbl_sn.setText(STATUS[1])
            # self.view.lbl_sn.setText("")
            self.view.lbl_result.setText(str(self._slot))
            self.view.chkbox_enable.setChecked(False)
        elif result == 'pass':
            self.view.setStyleSheet(KColor.bg_green)
        elif result == 'testing':
            self.view.setStyleSheet(KColor.bg_blue)
        else:
            print "state: {} error".format(result), traceback.format_exc()

    def enable_action(self, flag):
        if flag:
            self.change_slot_state_signal.emit('normal')
        else:
            self.change_slot_state_signal.emit('disable')


class SingleSlotView(QFrame):
    def __init__(self, index):
        super(SingleSlotView, self).__init__()
        self.lbl_sn = QLabel()
        self.lbl_index = QLabel(str(index + 1))
        self.lbl_result = QLabel()
        self.chkbox_enable = QCheckBox()
        self._font = KFont.FONT_14
        self.layout_widget()

    def layout_widget(self):
        self.setFrameShape(self.Box)
        self.setFrameShadow(self.Raised)
        self.lbl_sn.setAlignment(Qt.AlignCenter)
        self.lbl_sn.setFont(self._font)
        self.lbl_sn.setStyleSheet(KColor.white)

        self.lbl_result.setFont(self._font)
        self.lbl_result.setAlignment(Qt.AlignHCenter)
        self.lbl_result.setStyleSheet(KColor.white)
        self.lbl_index.setFixedSize(14, 14)
        self.lbl_index.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.lbl_index.setFont(self._font)

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        mid_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        left_layout.addWidget(self.chkbox_enable)
        left_layout.setSpacing(5)
        left_layout.addWidget(self.lbl_index)
        left_layout.setContentsMargins(0, 0, 0, 0)

        mid_layout.addWidget(self.lbl_sn)
        mid_layout.setSpacing(0)
        mid_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(self.chkbox_enable)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(mid_layout, 12)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = SingleSlotView(0)
    controller.view.show()
    sys.exit(app.exec_())
