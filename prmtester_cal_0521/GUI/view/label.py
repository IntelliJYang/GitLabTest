#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QWidget, QLabel, QBoxLayout, QApplication, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from GUI.resources.style.ui_style import KFont


class PrmLabel(QWidget):
    def __init__(self, parent=None, position="TOP"):
        super(PrmLabel, self).__init__(parent)
        self._name = QLabel()
        self._value = QLabel()
        self._name.setBuddy(self._value)
        self._layout = QBoxLayout(QBoxLayout.LeftToRight if position == "LEFT" else QBoxLayout.TopToBottom)
        # layout.setStretch(1,2)
        # layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        space_item1 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.addItem(space_item1)
        self._layout.addWidget(self._name, 1, Qt.AlignLeft)
        self._layout.addWidget(self._value, 1, Qt.AlignCenter)
        self.setLayout(self._layout)

    @property
    def name(self):
        return self._name.text()

    @name.setter
    def name(self, name):
        height = self._name.fontMetrics().height()
        self._name.setFixedHeight(height)
        self._name.setText(str(name))

    @property
    def value(self):
        return self._value.text()

    @value.setter
    def value(self, value):
        height = self._value.fontMetrics().height()
        self._value.setFixedHeight(height)
        self._value.setText(str(value))

    def set_font(self, name_font=KFont.FONT_14, value_font=KFont.FONT_14):
        assert isinstance(name_font, QFont)
        assert isinstance(value_font, QFont)
        # self._name.setFixedSize()
        self._name.setFont(name_font)
        self._value.setFont(value_font)

    def set_style_sheet(self, name_stytle_sheet, value_stytle_sheet):
        self._name.setStyleSheet(name_stytle_sheet)
        self._value.setStyleSheet(value_stytle_sheet)

    def set_name_style(self, *args):
        st = "".join(args)
        self._name.setStyleSheet(st)

    def set_value_style(self, *args):
        st = "".join(args)
        self._value.setStyleSheet(st)

    def set_space(self, value):
        assert isinstance(value, int)
        self._layout.setSpacing(value)

    def set_contents_margins(self, *args):
        self.setContentsMargins(*args)

    def same_size(self, width, length):
        self._name.setFixedSize(int(width), int(length))
        self._value.setFixedSize(int(width / 2), int(length))
        self._name.setAlignment(Qt.AlignCenter)
        self._value.setAlignment(Qt.AlignCenter)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    a = PrmLabel()
    a.name = "asdasdasd"
    a.value = "asdasdasd"
    a.show()

    sys.exit(app.exec_())
