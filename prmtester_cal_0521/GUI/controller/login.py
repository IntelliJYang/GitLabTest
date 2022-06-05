#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import base64
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QDialog, QMessageBox
from PyQt5.QtCore import Qt, QObject


class LoginController(QObject):
    def __init__(self):
        super(LoginController, self).__init__()

    @staticmethod
    def get_password():
        login_dialog = QDialog()

        main_layout = QVBoxLayout()
        lbl_pwd = QLabel('password:')
        line_pwd = QLineEdit()
        line_pwd.setEchoMode(QLineEdit.Password)
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(lbl_pwd)
        pwd_layout.addWidget(line_pwd)
        btn_layout = QHBoxLayout()

        btn_cancel = QPushButton('Cancel')
        btn_ok = QPushButton('OK')
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        main_layout.addLayout(pwd_layout)
        main_layout.addLayout(btn_layout)
        main_layout.setContentsMargins(5, 1, 5, 5)
        main_layout.setSpacing(5)
        login_dialog.setLayout(main_layout)
        login_dialog.setFixedSize(250, 100)
        login_dialog.setModal(True)
        login_dialog.setLayout(main_layout)
        btn_ok.clicked.connect(login_dialog.accept)
        btn_ok.setDefault(True)
        btn_cancel.clicked.connect(login_dialog.reject)

        if login_dialog.exec_() == QDialog.Accepted:
            if 'Z2RhZG1pbg==\n' == base64.encodestring(line_pwd.text()):
                return True
            else:
                QMessageBox.critical(QMessageBox(), "WRONG PASSWORD",
                                     "WRONG PASSWORD!!!\n",
                                     buttons=QMessageBox.Yes)
                return False



