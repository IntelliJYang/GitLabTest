#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from GUI.controller.header import HeaderController
from GUI.controller.footer import FooterController
from GUI.controller.content import ContentController
from Configure import constant


class ContainerController(object):
    def __init__(self):
        super(ContainerController, self).__init__()
        self.header_c = None
        self.footer_c = None
        self.content_c = None
        self.view = ContainerView()
        self._create_all_controllers()
        self._layout_all_view()

    def _create_all_controllers(self):
        self.header_c = HeaderController()
        self.footer_c = FooterController(constant.SLOTS)
        self.content_c = ContentController()

    def _layout_all_view(self):
        self.view.create_layout(self.header_c.view, self.content_c.view, self.footer_c.view)


class ContainerView(QWidget):
    def __init__(self):
        super(ContainerView, self).__init__(flags=Qt.WindowTitleHint)

    def create_layout(self, header_view, content_view, footer_viwe):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(header_view)
        main_layout.addWidget(content_view)
        main_layout.addWidget(footer_viwe)
        self.setLayout(main_layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = ContainerController()
    controller.view.show()
    sys.exit(app.exec_())
