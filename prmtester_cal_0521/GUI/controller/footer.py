#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"


import sys
from Configure import zmqports
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QFrame
from heartbeat import HeartBeatController


class FooterController(QObject):
    def __init__(self, slots):
        super(FooterController, self).__init__()
        self.view = FooterView()
        self.create_heart_beat_group('sequencer', zmqports.SEQUENCER_PUB, slots)
        self.create_heart_beat_group('Engine', zmqports.TEST_ENGINE_PUB, slots)
        self.create_heart_beat_group('logger', zmqports.LOGGER_PUB, 1)

    def create_heart_beat_group(self, str_name, port, slots):
        label = QLabel(str_name)
        self.view.layout.addWidget(label, alignment=Qt.AlignLeft)
        for slot in range(slots):
            heart_beat = HeartBeatController(slot + 1, port + slot, str_name)
            self.view.layout.addWidget(heart_beat.view, alignment=Qt.AlignLeft)
        self.view.layout.addWidget(QLabel('    '), alignment=Qt.AlignLeft)


class FooterView(QWidget):
    def __init__(self):
        super(FooterView, self).__init__()
        self.setFixedHeight(24)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout = QHBoxLayout()
        self.layout.setSpacing(1)
        self.layout.setAlignment(Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # self.setFixedHeight(24)
        self.setLayout(self.layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    f = FooterController(4)
    f.view.show()
    sys.exit(app.exec_())
