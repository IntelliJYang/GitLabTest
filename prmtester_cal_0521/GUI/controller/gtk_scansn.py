#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import random
import sys
from PyQt5.QtWidgets import QFrame, QLineEdit, QCheckBox, QLabel, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, \
    QPushButton, QHBoxLayout, QMessageBox
from GUI.resources.style.ui_style import KFont, KColor
from PyQt5.QtCore import Qt, pyqtSignal
from Configure import constant



class SnScanController(object):
    def __init__(self, scan_done_signal):
        super(SnScanController, self).__init__()
        self.view = SnScanView()
        self._auto_get_cfg = True
        self._scan_done_signal = scan_done_signal
        self.create_actions()

    def set_selected_slots(self, e_travelers):
        k = [int(i) for i in e_travelers.keys()]
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                self.view.sn_widgets_list[i][j].select(j in k)

    def create_actions(self):
        self.view.btn_cancel.clicked.connect(self.scan_cancel)
        self.view.btn_ok.clicked.connect(self.scan_confirm)
        self.view.chkbox_auto_get_cfg.clicked.connect(self.set_auto_cfg)
        self.view.check_all.clicked.connect(self.select_all_slots)
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                self.view.sn_widgets_list[i][j].mlb.returnPressed.connect(self.focus_next)
                self.view.sn_widgets_list[i][j].post_get_sn_signal.connect(self.get_sn_from_shufloor)
                if constant.MATRIX_SCANNER:
                    self.view.sn_widgets_list[i][j].cfg.returnPressed.connect(self.focus_next)


    def scan_cancel(self):
        self.view.close()
        self._scan_done_signal.emit([])

    def scan_confirm(self):
        if not self.check_if_repeat():
            if self.check_if_finish():
                self.collect_e_travelers()

    def set_auto_cfg(self, flag):
        self._auto_get_cfg = flag
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                self.view.sn_widgets_list[i][j].auto_cfg(flag)

    def select_all_slots(self, flag):
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                self.view.sn_widgets_list[i][j].select(flag)

    def focus_next(self):
        if not self.check_if_repeat():
            if self.check_if_finish() and constant.AUTO_START:
                self.collect_e_travelers()

    def collect_e_travelers(self):
        e_travelers = []
        for i in range(constant.GROUPS):
            e_travelers.append(dict())
            for j in range(constant.SLOTS):
                if self.view.sn_widgets_list[i][j].check.isChecked():
                    if constant.MATRIX_SCANNER:
                        cur_cfg = self.view.sn_widgets_list[i][j].cfg.text().strip().upper()
                    else:
                        cur_cfg = ''
                    cur_mlb = self.view.sn_widgets_list[i][j].mlb.text().strip().upper()
                    e_travelers[i].setdefault(str(j), {"attributes": {"MLBSN": cur_mlb, "cfg": cur_cfg}})
        if self._scan_done_signal:
            self._scan_done_signal.emit(e_travelers)
        self.view.hide()
        self.clear_all_info()


    def clear_all_info(self):
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                if self.view.sn_widgets_list[i][j].check.isChecked():
                    if constant.MATRIX_SCANNER:
                        self.view.sn_widgets_list[i][j].cfg.setText('')
                    self.view.sn_widgets_list[i][j].mlb.setText('')

    def check_if_repeat(self):
        if not self.check_if_mlb_repeat():
            return self.check_if_cfg_repeat()
        return True

    def check_if_cfg_repeat(self):
        if constant.MATRIX_SCANNER:
            cfg_list = []
            for i in range(constant.GROUPS):
                for j in range(constant.SLOTS):
                    cur_cfg = self.view.sn_widgets_list[i][j].cfg.text().strip()
                    if self.view.sn_widgets_list[i][j].check.isChecked() and cur_cfg != '':
                        if cur_cfg in cfg_list:
                            QMessageBox.warning(QMessageBox(), "Warning", "Repeated CFG: {}".format(cur_cfg))
                            return True
                        else:
                            cfg_list.append(cur_cfg)
        return False

    def check_if_mlb_repeat(self):
        mlb_list = []
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                cur_mlb = self.view.sn_widgets_list[i][j].mlb.text().strip()
                if self.view.sn_widgets_list[i][j].check.isChecked() and cur_mlb != '':
                    if cur_mlb in mlb_list:
                        QMessageBox.warning(QMessageBox(), "Warning", "Repeated MLB: {}".format(cur_mlb))
                        self.view.sn_widgets_list[i][j].mlb.selectAll()
                        self.view.sn_widgets_list[i][j].mlb.setFocus()
                        return True
                    else:
                        mlb_list.append(cur_mlb)
        return False

    def check_if_finish(self):
        for i in range(constant.GROUPS):
            for j in range(constant.SLOTS):
                cur_mlb = self.view.sn_widgets_list[i][j].mlb.text().strip()
                if constant.MATRIX_SCANNER:
                    cur_cfg = self.view.sn_widgets_list[i][j].cfg.text().strip()

                if self.view.sn_widgets_list[i][j].check.isChecked():
                    if constant.MATRIX_SCANNER:
                        if cur_mlb != '' and cur_cfg != '':
                            continue
                        else:
                            return False
                    else:
                        if cur_mlb != '':
                            continue
                        else:
                            return False
                else:
                    continue
        return True

    def get_sn_from_shufloor(self, data):
        print "*"
        print data
        print "*"


class SnScanView(QFrame):
    def __init__(self, parent=None, *name_list):
        if len(name_list) < 1:
            name_list = ["MLB#", "CFG#"]
        super(SnScanView, self).__init__(parent)
        self.sn_widgets_list = []
        self._length = 300
        self._lbl_name = []
        self._name_list = name_list
        self._main_layout = QVBoxLayout()
        self.check_all = QCheckBox("ALL")

        self._sp = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chkbox_auto_get_cfg = QCheckBox("Auto get {} ?".format(name_list[1]))
        self.chkbox_auto_get_cfg.setChecked(True)

        self._name_layout = QHBoxLayout()

        self.layout_name_list()
        self.layout_sn_matrix()

        button_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedWidth(150)
        self.btn_cancel.setFont(KFont.FONT_24_BOLD)
        self.btn_cancel.setFocusPolicy(Qt.NoFocus)
        # self.btn_cancel.clicked.connect(self.close)

        self.btn_ok = QPushButton("Ok")
        self.btn_ok.setFixedWidth(150)
        self.btn_ok.setFont(KFont.FONT_24_BOLD)
        self.btn_ok.setFocusPolicy(Qt.NoFocus)

        button_box.addItem(self._sp)
        button_box.addWidget(self.btn_ok)
        button_box.addItem(self._sp)
        button_box.addWidget(self.btn_cancel)
        button_box.addItem(self._sp)

        self._main_layout.addLayout(button_box)
        self.setLayout(self._main_layout)
        # on the top of windows
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedSize(self.sizeHint())
        self.setContentsMargins(1, 1, 1, 1)

    def layout_name_list(self):

        self.check_all.setChecked(True)
        self.check_all.setFont(KFont.FONT_14)
        self.check_all.setFixedWidth(50)
        self._name_layout.addWidget(self.check_all)
        if constant.GROUPS <= 1:
            lbl_sn = QLabel(self._name_list[0])
            lbl_sn.setFont(KFont.FONT_24_BOLD)
            lbl_sn.setFixedWidth(self._length)
            lbl_sn.setAlignment(Qt.AlignCenter)
            self._name_layout.addWidget(lbl_sn, alignment=Qt.AlignCenter)

            if constant.MATRIX_SCANNER:
                self._main_layout.addWidget(self.chkbox_auto_get_cfg)
                lbl_cfg = QLabel(self._name_list[1])
                lbl_cfg.setFont(KFont.FONT_24_BOLD)
                lbl_cfg.setFixedWidth(self._length)
                lbl_cfg.setAlignment(Qt.AlignCenter)
                self._name_layout.addWidget(lbl_cfg, alignment=Qt.AlignCenter)

        else:
            for i in range(constant.SLOTS):
                lbl_sn = QLabel(self._name_list[0])
                lbl_sn.setFont(KFont.FONT_14_BOLD)
                lbl_sn.setAlignment(Qt.AlignCenter)
                lbl_sn.setFixedWidth(150)
                self._name_layout.addWidget(lbl_sn)

                if constant.MATRIX_SCANNER:
                    self._main_layout.addWidget(self.chkbox_auto_get_cfg)
                    lbl_cfg = QLabel(self._name_list[1])
                    lbl_cfg.setFont(KFont.FONT_14_BOLD)
                    lbl_cfg.setAlignment(Qt.AlignCenter)
                    lbl_cfg.setFixedWidth(150)
                    self._name_layout.addWidget(lbl_cfg)

        self._name_layout.setSpacing(1)
        self._name_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addLayout(self._name_layout)
        self._main_layout.setSpacing(1)

    def layout_sn_matrix(self):
        matrix_layout = QVBoxLayout()
        if constant.GROUPS <= 1:
            self.sn_widgets_list.append(list())
            for i in range(constant.SLOTS):
                sn_widget = SnWidget(300, KFont.FONT_24, str(i + 1))
                self.sn_widgets_list[0].append(sn_widget)
                matrix_layout.addWidget(sn_widget)
        else:
            for i in range(constant.GROUPS):
                line_layout = QHBoxLayout()
                self.sn_widgets_list.append(list())
                for j in range(constant.SLOTS):
                    sn_widget = SnWidget(150, KFont.FONT_14, '{}-{}'.format(i + 1, j + 1))
                    self.sn_widgets_list[i].append(sn_widget)
                    line_layout.addWidget(sn_widget)
                    line_layout.setSpacing(0)
                    line_layout.setContentsMargins(1, 1, 1, 1)
                matrix_layout.addLayout(line_layout)
                matrix_layout.setContentsMargins(0, 0, 0, 0)
                matrix_layout.setSpacing(0)
        matrix_layout.setSpacing(1)
        self._main_layout.addLayout(matrix_layout)
        self.setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, close_event):
        self.hide()


class SnWidget(QFrame):
    post_get_sn_signal = pyqtSignal(str)
    def __init__(self, length, font, index):
        super(SnWidget, self).__init__()

        self._auto_cfg = True
        main_layout = QHBoxLayout()
        self.check = QCheckBox(index)
        self.check.clicked.connect(self.select)

        self.mlb = QLineEdit()
        self.mlb.returnPressed.connect(self.mlb_value_change)
        self.check.setFixedWidth(50)
        self.check.setChecked(True)
        self.mlb.setFont(font)
        self.mlb.setAlignment(Qt.AlignCenter)
        self.mlb.setFixedWidth(length)
        main_layout.addWidget(self.check, alignment=Qt.AlignLeft)
        main_layout.addWidget(self.mlb, alignment=Qt.AlignLeft)

        if constant.MATRIX_SCANNER:
            self.cfg = QLineEdit()
            self.cfg.setFont(font)
            self.cfg.setAlignment(Qt.AlignCenter)
            self.cfg.setFixedWidth(length)
            self.cfg.setDisabled(True)
            self.cfg.setStyleSheet(KColor.bg_litegrey)
            self.cfg.returnPressed.connect(self.cfg_value_change)
            main_layout.addWidget(self.cfg, alignment=Qt.AlignLeft)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)
        # main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.setLayout(main_layout)
        self.setContentsMargins(0, 0, 0, 0)

    def select(self, flag):
        self.mlb.setEnabled(flag)
        self.check.setChecked(flag)
        if flag:
            self.mlb.setStyleSheet(KColor.bg_white)
            if constant.MATRIX_SCANNER:
                self.cfg.setStyleSheet(KColor.bg_white)
        else:
            self.mlb.setStyleSheet(KColor.bg_grey)
            if constant.MATRIX_SCANNER:
                self.cfg.setStyleSheet(KColor.bg_grey)

    def auto_cfg(self, flag):
        self._auto_cfg = flag
        self.cfg.setDisabled(flag)
        if flag:
            self.cfg.setStyleSheet(KColor.bg_litegrey)
        else:
            self.cfg.setStyleSheet(KColor.bg_white)

    def mlb_value_change(self):

        #start
        #add query event to here!!!!
        self.post_get_sn_signal.emit("fucking!!!!")
        #end
        if not constant.DEBUG_MODE:
            if len(self.mlb.text()) != 17:
                QMessageBox.warning(QMessageBox(), "Warning", "Current SerialNumber is not 17")
                self.mlb.selectAll()
                self.mlb.setFocus()
                return False

        self.focusNextChild()
        if self._auto_cfg:
            self.auto_get_cfg()

    def auto_get_cfg(self):
        if constant.MATRIX_SCANNER:
            self.cfg.setText("ADFEEFEAE{}".format(random.randint(100, 999)))


    def cfg_value_change(self):
        print self.cfg.text()

    def closeEvent(self, close):
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = SnScanController(None)
    controller.view.show()
    # w = SnWidget(300, KFont.FONT_24, '1')
    # w.show()
    sys.exit(app.exec_())
