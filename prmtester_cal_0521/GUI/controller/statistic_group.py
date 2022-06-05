#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import traceback
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QApplication
from Configure import constant
from GUI.controller.statistic_slot import SlotStatisticController
from GUI.resources.style.ui_style import KColor


class StatisticGroupController(object):
    def __init__(self):
        self.statistic_list = []
        super(StatisticGroupController, self).__init__()
        for i in range(0, constant.SLOTS):
            self.statistic_list.append(SlotStatisticController(i))
        self.view = StatisticGroupView([statistic.view for statistic in self.statistic_list])

    def get_enable_slots_e_travelers(self):
        e_travelers = {}
        enable = False
        try:
            for slot in self.statistic_list:
                e_traveler = slot.slot_sn_c.get_e_traveler()
                for v in e_traveler.values():
                    enable = v.get('attributes').get('MLBSN')
                if enable:
                    e_travelers.update(e_traveler)
        except Exception, e:
            print e, traceback.format_exc()
        return e_travelers

    def set_slots_info(self, e_travelers):
        for i in range(constant.SLOTS):
            e_traveler = e_travelers.get(str(i), None)
            if e_traveler:
                self.statistic_list[i].slot_sn_c.set_e_traveler(e_traveler.get('attributes').get('MLBSN'), True)
            else:
                self.statistic_list[i].slot_sn_c.set_e_traveler('', False)
        with open('/vault/sn.txt', 'w') as f:
            for key in e_travelers.keys():
                f.writelines(str("mlbsn{}".format(key)) + ':' + e_travelers.get(key).get('attributes').get('MLBSN') + '\n')

    def get_slots_info(self):
        result = []
        for i in range(constant.SLOTS):
            r = self.statistic_list[i].slot_sn_c.check_slot()
            result.append(r)
        return result


    def set_slot_sn(self, site, sn):
        self.statistic_list[site].slot_sn_c.set_sn(sn)

    def enable_selected(self, flag):
        for i in range(constant.SLOTS):
            self.statistic_list[i].slot_sn_c.view.chkbox_enable.setEnabled(flag)


class StatisticGroupView(QFrame):
    def __init__(self, slot_statistic_list):
        super(StatisticGroupView, self).__init__()
        main_layout = QVBoxLayout()
        for slot in slot_statistic_list:
            main_layout.addWidget(slot)
        main_layout.setSpacing(1)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setStyleSheet(KColor.bg_grey)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = StatisticGroupController()
    controller.view.show()
    sys.exit(app.exec_())
