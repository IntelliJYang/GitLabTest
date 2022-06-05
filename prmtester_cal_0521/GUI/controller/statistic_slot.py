#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QFrame
from GUI.view.pluginswiget import YieldAndTimer
from GUI.controller.sn_slot import SnSlotController
from Configure import constant


class SlotStatisticController(object):
    def __init__(self, site):
        self.e_traveler = dict()
        self.slot_sn_c = SnSlotController(site)
        # self.slot_yield = YieldAndTimer(yield_flag=constant.STATISTICBYSLOT)
        self.view = OneSlotStatisticView(self.slot_sn_c.view)

    def slot_sequence_start(self):
        self.slot_sn_c.change_slot_state('testing')
        # self.slot_yield.loading_enable()
        # self.slot_yield.start()

    def slot_sequence_stop(self, result):
        if result:
            state = 'pass'
            # self.slot_yield.pass_result()
        else:
            state = 'fail'
            # self.slot_yield.fail_result()

        self.slot_sn_c.change_slot_state(state)
        # self.slot_yield.loading_disable()
        # self.slot_yield.stop()

    def slot_sequence_control(self, flag, result):
        if flag:
            self.slot_sequence_start()
        else:
            self.slot_sequence_stop(result)


class OneSlotStatisticView(QFrame):
    def __init__(self, slot_sn, parent=None):
        super(OneSlotStatisticView, self).__init__(parent)
        main_layout = QHBoxLayout()
        main_layout.addWidget(slot_sn, 2)
        # main_layout.addWidget(slot_yield, 1)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    con = SlotStatisticController(0)
    con.view.show()
    sys.exit(app.exec_())
