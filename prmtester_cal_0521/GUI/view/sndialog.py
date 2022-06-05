#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
from PyQt5.QtWidgets import QFrame, QLineEdit, QApplication, QHBoxLayout, QVBoxLayout, \
    QCheckBox, QLabel, QPushButton, QDialog, QMessageBox, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal, pyqtSlot
from Configure import constant
from GUI.resources.style.ui_style import KFont, KColor
import requests

bda_pattern = re.compile('bt_mac_address=(\w+)')


class BaseSnModule(QFrame):

    def __init__(self, num, font=KFont.FONT_24, lenth=300, parent=None):
        super(BaseSnModule, self).__init__(parent)
        self.lenth = lenth
        self.num = num
        self.font = font
        self.__state = True
        self.init_widget()

    def init_widget(self):
        # create widgets
        _mainlayout = QHBoxLayout()
        self.__cb = QCheckBox(str(self.num))
        self.__cb.clicked.connect(self.check_state)
        self.__cb.setFont(self.font)
        self.__sn = QLineEdit()
        self.__sn.setFont(self.font)

        # self.__sn.setFixedWidth(300)
        self.__cfg = QLineEdit()
        self.__sn.setFixedWidth(self.lenth)
        self.__cfg.setFixedWidth(self.lenth)
        self.__cfg.setFont(self.font)
        self.set_widget_disable(True)
        _mainlayout.addWidget(self.__cb)
        _mainlayout.addWidget(self.__sn)
        if constant.MATRIX_SCANNER:
            _mainlayout.addWidget(self.__cfg)
        _mainlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(_mainlayout)

    def __len__(self):
        return len(self.__sn.text())

    def get_sn(self):
        return self.__sn.text().upper()

    def get_cfg(self):
        return self.__cfg.text().upper()

    def get_slot(self):
        return self.num - 1

    def connect_returnPressed(self, objfunc):
        self.__sn.returnPressed.connect(objfunc)
        if constant.MATRIX_SCANNER:
            self.__cfg.returnPressed.connect(objfunc)

    def disconnect_returnPressed(self, objfunc):
        self.__sn.returnPressed.disconnect(objfunc)
        if constant.MATRIX_SCANNER:
            self.__cfg.returnPressed.disconnect(objfunc)

    def clear(self):
        self.__cfg.clear()
        self.__sn.clear()

    def check_state(self):
        if self.__cb.isChecked():
            self.set_widget_disable(True)
            self.__state = True
        else:
            self.set_widget_disable(False)
            self.__state = False

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, bl):
        assert isinstance(bl, bool)
        self.set_widget_disable(bl)
        self.__state = bl

    def set_widget_disable(self, bl):
        assert isinstance(bl, bool)
        self.__state = bl

        if bl:
            self.__cb.setChecked(True)
            self.__sn.setDisabled(False)
            self.__sn.setStyleSheet(KColor.bg_white)
            if constant.MATRIX_SCANNER:
                self.__cfg.setDisabled(False)
                self.__cfg.setStyleSheet(KColor.bg_white)
            else:
                self.__cfg.setDisabled(True)
                self.__cfg.setStyleSheet(KColor.bg_grey)
        else:
            self.__cb.setChecked(False)
            self.__sn.setDisabled(True)
            self.__sn.setStyleSheet(KColor.bg_grey)
            self.__cfg.setDisabled(True)
            self.__cfg.setStyleSheet(KColor.bg_grey)


class NormalSnModule(QFrame):
    sig = pyqtSignal(list)

    def __init__(self, slot, parent=None):
        super(NormalSnModule, self).__init__(parent)
        self.slots = slot
        self.init()

    def init(self):
        _main_layout = QVBoxLayout()
        h = QHBoxLayout()
        l_sn = QLabel("MLB#")
        l_sn.setFont(KFont.FONT_24_BOLD)
        h.addWidget(l_sn, 1, alignment=Qt.AlignCenter)
        # h.setSpacing(0)
        # h.setContentsMargins()
        if constant.MATRIX_SCANNER:
            l_cfg = QLabel("CFG#")
            l_cfg.setFont(KFont.FONT_24_BOLD)
            h.addWidget(l_cfg, 1, alignment=Qt.AlignCenter)
        _main_layout.addLayout(h)
        self.check_all = QCheckBox("ALL")
        self.check_all.setChecked(True)
        self.check_all.setFont(KFont.FONT_24_BOLD)
        self.check_all.clicked.connect(self.select_all)
        _main_layout.addWidget(self.check_all)
        self.objWidgets = list()
        for slot in xrange(self.slots):
            t = self.get_one_widget(slot + 1)
            self.objWidgets.append(t)
            t.connect_returnPressed(self.returnPressed)
            _main_layout.addWidget(t)

        self.setLayout(_main_layout)

    def get_one_widget(self, num):
        return BaseSnModule(num)

    def returnPressed(self):

        current_widget = QApplication.focusWidget()
        current_sn = current_widget.text()
        if not constant.DEBUG_MODE:
            if len(current_sn) != 17:
                QMessageBox.warning(QMessageBox(), "Warning", "Current SerialNumber is not 17")
                return
        state = self.isRepeat()
        if state:
            if self.isFinished():
                if constant.AUTO_START:
                    self.get_format_sns()
                # self.objWidgets[0].setFocus()
                # print "finished"
                return
            self.focusNextChild()
            current_widget = QApplication.focusWidget()
            # bda_sn = current_widget.text()
            bda = self.query_bda(current_sn)
            if bda:
                current_widget.setText(str(bda))
                self.focusNextChild()
            else:
                QMessageBox.warning(QMessageBox(), "ERROR",
                                    'CAN NOT GET BDA OF: {}'.format(current_sn))
                self.focusPreviousChild()
        else:
            QMessageBox.warning(QMessageBox(), "Warning", "Current SerialNumber is Repeated!!")

    def isRepeat(self):
        if constant.DEBUG_MODE:
            return True
        else:
            sn_list = [sn.get_sn() for sn in self.objWidgets if sn.state and len(sn) > 0]
            # print sn_list,set(sn_list)
            if len(sn_list) != len(set(sn_list)):
                return False
            else:
                return True

    def isFinished(self):
        if not constant.MATRIX_SCANNER:
            return all([True if len(sn) == 17 else False for sn in self.objWidgets if sn.state])
        else:
            for slot in self.objWidgets:
                if slot.state:
                    if len(slot.get_sn()) != 17:
                        return False
                    if len(slot.get_cfg()) == 0:
                        return False
            return True

    def get_format_sns(self):
        all_info = list()
        lt = list()
        for item in self.objWidgets:
            temp = dict()
            temp.setdefault("group", 0)
            temp.setdefault("slot", item.get_slot())
            temp.setdefault("sn", item.get_sn())
            temp.setdefault("cfg", item.get_cfg())
            temp.setdefault("state", item.state)
            lt.append(temp)
        all_info.append(lt)
        self.sig.emit(all_info)
        self.focusNextChild()
        self.clear_all()
        return all_info

    def select_all(self):
        if self.check_all.isChecked():
            # self.check_all.setChecked()
            for slot in self.objWidgets:
                slot.state = True
        else:
            for slot in self.objWidgets:
                slot.state = False

    def clear_all(self):
        for slot in self.objWidgets:
            slot.clear()

    def query_bda(self, mlbsn):
        # 'http://172.26.1.60/BobcatService.svc/request?sn=GRX84640JEHJKM80F&c=QUERY_RECORD&p=bt_mac_address'
        query_cmd = '{}?sn={}&c=QUERY_RECORD&p=bt_mac_address'.format(constant.SFC_URL, mlbsn)
        try:
            response = requests.get(query_cmd, timeout=0.5).content.decode()
            print response
        except:
            return False

        if '0 SFC_OK' in response:
            bda = bda_pattern.findall(response)
            if len(bda) > 0:
                return bda[0]
            else:
                return False


class ManualScanSnModule(QFrame):
    sig = pyqtSignal(list)

    def __init__(self, slots, groups, parent=None):
        super(ManualScanSnModule, self).__init__(parent)
        self.slots = slots
        self.groups = groups
        self.objWidgets = list()
        self.init()

    def init(self):
        _main_layout = QVBoxLayout()
        self.check_all = QCheckBox("ALL")
        self.check_all.setChecked(True)
        self.check_all.setFont(KFont.FONT_24_BOLD)
        self.check_all.clicked.connect(self.select_all)
        _main_layout.addWidget(self.check_all)
        for group in xrange(self.groups):
            h = QHBoxLayout()
            tmp = list()
            for slot in xrange(self.slots):
                t = self.get_one_widget(slot + group * constant.SLOTS + 1)
                t.connect_returnPressed(self.returnPressed)
                # self.uut * group + sn + 1
                h.addWidget(t)
                tmp.append(t)
            self.objWidgets.append(tmp)
            _main_layout.addLayout(h)
        self.setLayout(_main_layout)

    def get_one_widget(self, num):
        return BaseSnModule(num, font=KFont.FONT_16, lenth=200)

    def select_all(self):
        if self.check_all.isChecked():
            # self.check_all.setChecked()
            for groups in self.objWidgets:
                assert isinstance(groups, list)
                for slot in groups:
                    slot.state = True
        else:
            for groups in self.objWidgets:
                assert isinstance(groups, list)
                for slot in groups:
                    slot.state = False

    def clear_all(self):
        for groups in self.objWidgets:
            assert isinstance(groups, list)
            for slot in groups:
                slot.clear()

    def returnPressed(self):
        current_widget = QApplication.focusWidget()
        current_sn = current_widget.text()
        if not constant.DEBUG_MODE:
            if len(current_sn) != 17:
                QMessageBox.warning(QMessageBox(), "Warning", "Current SerialNumber is not 17")
                return
        state = self.isRepeat()
        print state
        if state:
            if self.isFinished():
                if constant.AUTO_START:
                    self.get_format_sns()
                # self.objWidgets[0].setFocus()
                # print "finished"
                return
            self.focusNextChild()
        else:
            QMessageBox.warning(QMessageBox(), "Warning", "Current SerialNumber is Repeated!!")

    def isRepeat(self):
        if constant.DEBUG_MODE:
            return True
        else:
            sn_list = list()
            for groups in self.objWidgets:
                for slot in groups:
                    if slot.state and len(slot) > 0:
                        sn_list.append(slot.get_sn())
            if len(sn_list) != len(set(sn_list)):
                return False
            else:
                return True

    def isFinished(self):
        for groups in self.objWidgets:
            for slot in groups:
                if slot.state and len(slot) != 17:
                    return False
        return True

    def get_format_sns(self):
        all_info = list()
        for index_group, groups in enumerate(self.objWidgets):
            lt = list()
            for index_slot, slot in enumerate(groups):
                temp = dict()
                temp.setdefault("group", index_group)
                temp.setdefault("slot", slot.get_slot())
                temp.setdefault("sn", slot.get_sn())
                temp.setdefault("cfg", slot.get_cfg())
                temp.setdefault("state", slot.state)
                lt.append(temp)
            all_info.append(lt)
        self.sig.emit(all_info)
        # print all_info
        self.focusNextChild()
        self.clear_all()
        return all_info


class PrmScanSn(QDialog):

    def __init__(self, UpdateUI=None, parent=None):
        super(PrmScanSn, self).__init__(parent)
        self.UpdateUI = UpdateUI
        main_layout = QVBoxLayout()
        sp = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        if constant.GROUPS > 1:
            self.module = ManualScanSnModule(constant.SLOTS, constant.GROUPS)
        else:
            self.module = NormalSnModule(constant.SLOTS)
        self.module.sig.connect(self.scan_finished)
        main_layout.addWidget(self.module)
        # self.module.connect_enter_return()

        button_box = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setFixedWidth(150)
        # cancel.setMinimumSize(180, 35)
        cancel.setFont(KFont.FONT_24_BOLD)
        cancel.clicked.connect(self.cancel_button_event)
        cancel.setFocusPolicy(Qt.NoFocus)

        ok = QPushButton("Ok")
        ok.setFixedWidth(150)
        # ok.setMinimumSize(180, 35)
        ok.setFont(KFont.FONT_24_BOLD)
        ok.clicked.connect(self.prmok_button_event)
        ok.setFocusPolicy(Qt.NoFocus)

        button_box.addItem(sp)
        button_box.addWidget(ok)
        button_box.addItem(sp)
        button_box.addWidget(cancel)
        button_box.addItem(sp)

        main_layout.addLayout(button_box)
        self.setLayout(main_layout)
        # self.setFixedSize(self.width(), self.height())
        # on the top of windows
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        # self.setFocusPolicy(Qt.NoFocus)

    def scan_finished(self, lt):
        if constant.AUTO_START:
            print lt
            self.close()
        else:
            print lt

    def cancel_button_event(self):
        self.module.clear_all()
        self.close()

    def prmok_button_event(self):
        # if constant.AUTO_START:
        if self.module.isFinished():
            self.module.get_format_sns()
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sn = PrmScanSn()

    # sn.setStatues("READY")
    # sn.setUUtNumber(6)
    sn.show()
    sys.exit(app.exec_())
