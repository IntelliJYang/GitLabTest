# -*- coding: utf-8 -*-
from PyQt5.QtGui import QFont

FONT_STYLE = "PingFang HK"


class KFont(QFont):
    FONT_10 = QFont(FONT_STYLE, 10)
    FONT_10_BOLD = QFont(FONT_STYLE, 10, QFont.Bold)
    FONT_14 = QFont(FONT_STYLE, 14)
    FONT_14_BOLD = QFont(FONT_STYLE, 14, QFont.Bold)
    FONT_16 = QFont(FONT_STYLE, 16)
    FONT_16_BOLD = QFont(FONT_STYLE, 16, QFont.Bold)

    FONT_18 = QFont(FONT_STYLE, 18)
    FONT_18_BOLD = QFont(FONT_STYLE, 18, QFont.Bold)

    FONT_24 = QFont(FONT_STYLE, 24)
    FONT_24_BOLD = QFont(FONT_STYLE, 24, QFont.Bold)

    FONT_28 = QFont(FONT_STYLE, 28)
    FONT_28_BOLD = QFont(FONT_STYLE, 28, QFont.Bold)

    FONT_36 = QFont(FONT_STYLE, 36)
    FONT_36_BOLD = QFont(FONT_STYLE, 36, QFont.Bold)

    FONT_40 = QFont(FONT_STYLE, 40)
    FONT_40_BOLD = QFont(FONT_STYLE, 40, QFont.Bold)

    @staticmethod
    def get_font(tp, size, is_bold=False):
        assert isinstance(tp, basestring)
        assert isinstance(size, int)
        if is_bold:
            ft = QFont(tp, size, QFont.Bold)
        else:
            ft = QFont(tp, size)
        return ft


class KColor(object):
    white = "color: rgb(255,255,255);"
    red = "color: rgb(220, 20, 30);"
    green = "color: rgb(0, 220, 127);"
    blue = "color: rgb(70, 70, 255);"
    black = "color: rgb(0, 0, 0);"
    grey = "color: rgb(90, 90, 90);"
    yellow = "color: rgb(255, 200, 0);"
    c_window = "color: rgb(236, 236, 236);"
    purple = "color: rgb(255, 0, 255);"

    bg_white = "background-color: rgb(255, 255, 255);"
    bg_red = "background-color: rgb(220, 20, 30);"
    bg_grey = "background-color: rgb(150, 150, 150);"
    bg_litegrey = "background-color: rgb(240, 240, 240);"
    bg_green = "background-color: rgb(0, 220, 127);"
    bg_blue = "background-color: rgb(70, 70, 255);"
    bg_orange = "background-color: rgb(255, 165, 0);"
    # bg_grey = "background-color: rgb(0, 0, 0);"
    bg_yellow = "background-color: rgb(255, 255, 0);"
    bg_window = "background-color: rgb(236, 236, 236);"
    bg_purple = "background-color: rgb(255, 0, 255);"

    state_running = "background-color: rgb(255, 255, 0);color: rgb(0, 0, 0);"
    state_fail = "background-color: rgb(220, 20, 30);color: rgb(255, 255, 255);"
    state_pass = "background-color: rgb(0, 220, 127);color: rgb(255, 255, 255);"
    state_disable = "background-color: rgb(150, 150, 150);color: rgb(255, 255, 255);"
    state_idle = "background-color: rgb(250, 250, 250);color: rgb(0, 0, 0);"

    leave_running = "background-color: rgb(255, 255, 100);color: rgb(0, 0, 0);"
    leave_fail = "background-color: rgb(250, 20, 30);color: rgb(255, 255, 255);"
    leave_pass = "background-color: rgb(0, 220, 154);color: rgb(255, 255, 255);"
    leave_disable = "background-color: rgb(160, 160, 160);color: rgb(255, 255, 255);"
    leave_idle = "background-color: rgb(255, 255, 255);color: rgb(0, 0, 0);"

    STATE_COLOR = {
        "RUNNING": "background-color: rgb(255, 255, 0);color: rgb(0, 0, 0);",
        "FAIL": "background-color: rgb(220, 20, 30);color: rgb(255, 255, 255);",
        "PASS": "background-color: rgb(0, 220, 127);color: rgb(255, 255, 255);",
        "DISABLE": "background-color: rgb(150, 150, 150);color: rgb(255, 255, 255);",
        "IDLE": "background-color: rgb(250, 250, 250);color: rgb(0, 0, 0);"
    }

    LEFT_COLOR = {
        "RUNNING": "background-color: rgb(255, 255, 100);color: rgb(0, 0, 0);",
        "FAIL": "background-color: rgb(250, 20, 30);color: rgb(255, 255, 255);",
        "PASS": "background-color: rgb(0, 220, 154);color: rgb(255, 255, 255);",
        "DISABLE": "background-color: rgb(160, 160, 160);color: rgb(255, 255, 255);",
        "IDLE": "background-color: rgb(255, 255, 255);color: rgb(0, 0, 0);"
    }

    @classmethod
    def get_color(cls, r, g, b):
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            return "color: rgb({},{},{});".format(r, g, b)

    @classmethod
    def get_background_color(cls, r, g, b):
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            return "background-color: rgb({},{},{});".format(r, g, b)


PRM_STATE = ("RUNNING", "FAIL", "PASS", "DISABLE", "IDLE")
