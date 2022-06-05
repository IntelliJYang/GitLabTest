#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import traceback
from Configure import constant
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QHBoxLayout, QWidget, QApplication, QStackedWidget
from GUI.controller.slot import SlotController
from GUI.controller.slottestplan import SlotTpController


class OverViewController(QObject):
    change_page_signal = pyqtSignal(int, name='change_page')

    def __init__(self):
        super(OverViewController, self).__init__()

        self.slot_widget_list = list()
        self.slot_tp_list = list()
        self.create_all_slot_instance()
        self.view = OverView(self.change_page_signal)
        self.layout_over_view_slots()

        self.change_page_signal.connect(self.change_over_view_page)
        self.view.add_slot_tp_widgets(self.slot_tp_list)

        self._current_group_index = 0
        self._current_group_tp = None
        self._current_group_slot = None

    def set_current_group_index(self, index):
        self._current_group_index = index
        self._current_group_tp = self.slot_tp_list[index]
        self._current_group_slot = self.slot_widget_list[index]

    def create_all_slot_instance(self):

        for i in range(constant.GROUPS):
            _slot_widget_group = list()
            _slot_tp_group = list()
            for j in range(constant.SLOTS):
                _slot_widget = SlotController(i, j, self.change_page_signal)
                _slot_widget_group.append(_slot_widget)
                _slot_tp = SlotTpController(i, j, self.change_page_signal)
                _slot_tp_group.append(_slot_tp)

            self.slot_widget_list.append(_slot_widget_group[:])
            self.slot_tp_list.append(_slot_tp_group[:])

    def layout_over_view_slots(self):
        _all_slots_view_list = list()
        for _group in self.slot_widget_list:
            _group_slots_view_list = list()
            for _slot in _group:
                _group_slots_view_list.append(_slot.view)
            _all_slots_view_list.append(_group_slots_view_list)
        self.view.layout_slot_widgets(_all_slots_view_list)

    def change_over_view_page(self, index):
        if index == -1:
            self.view.change_page(0)
        elif index >= 0:
            self.view.change_page(index + 1)

    def parse_sequencer_message(self, site, message):
        try:
            self._current_group_slot[site].parse_sequencer_message(message)
            self._current_group_tp[site].parse_sequencer_message(message)
        except OverflowError:
            print OverflowError, traceback.format_exc()

    def update_e_travelers(self, e_travelers_list):
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                try:
                    e_traveler = e_travelers_list[i][str(j)].get('attributes')
                    self.slot_widget_list[i][j].write_e_traveler(e_traveler)
                except KeyError:
                    continue

    def set_row_count(self, row_count):
        for _group in self.slot_widget_list:
            for _slot in _group:
                _slot.set_row_count(row_count)

    def reset(self):
        for _group in self.slot_widget_list:
            for _slot in _group:
                if _slot.is_checked():
                    _slot.reset()

        for _group in self.slot_tp_list:
            for _slot in _group:
                _slot.reset()

    def get_all_slots_selected_state(self):
        _all_selected_list = list()
        for _group in self.slot_widget_list:
            _group_selected = list()
            for _slot in _group:
                _group_selected.append(_slot.is_checked())
            _all_selected_list.append(_group_selected)
        return _all_selected_list


class OverView(QFrame):
    def __init__(self, signal=None):
        super(OverView, self).__init__()
        main_layout = QVBoxLayout()
        self._signal = signal
        self.slot_widget_list = list()
        self.slot_tp_list = list()
        self.scrollArea = QScrollArea()
        self.scrollArea.setFrameStyle(QFrame.NoFrame)
        self._page = QStackedWidget()
        self._page.addWidget(self.scrollArea)

        main_layout.addWidget(self._page)
        main_layout.setSpacing(1)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_layout)

        self.setFrameStyle(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)

    def layout_slot_widgets(self, all_slots_view_list):
        _all_slots = QWidget()
        _all_slots_layout = QVBoxLayout()
        _all_slots_layout.setSpacing(5)
        if constant.SLOTS<=5:
            for _group_slots_view in all_slots_view_list:
                _group_layout = QHBoxLayout()
                for _slot_view in _group_slots_view:
                    _group_layout.addWidget(_slot_view)
                    _group_layout.setSpacing(1)
                _all_slots_layout.addLayout(_group_layout)
        else:
            for _group_slots_view in all_slots_view_list:
                _group_layout = QHBoxLayout()
                _group_layout1 = QHBoxLayout()
                for _slot_view in _group_slots_view[0:constant.ROWS]:
                    _group_layout.addWidget(_slot_view)
                    _group_layout.setSpacing(1)
                _all_slots_layout.addLayout(_group_layout)
                for _slot_view in _group_slots_view[constant.ROWS::]:
                    _group_layout1.addWidget(_slot_view)
                    _group_layout1.setSpacing(1)
                _all_slots_layout.addLayout(_group_layout1)

        _all_slots.setLayout(_all_slots_layout)
        self.scrollArea.setWidget(_all_slots)

    def add_slot_tp_widgets(self, all_tp_view_list):
        for _group_tp in all_tp_view_list:
            for _slot_tp in _group_tp:
                self._page.addWidget(_slot_tp.view)

    def change_page(self, index):
        self._page.setCurrentIndex(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = OverViewController()
    controller.view.show()
    sys.exit(app.exec_())
