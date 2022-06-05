import sys
import time
import traceback
from PyQt5.QtGui import QMovie, QFontMetrics, QFont
from PyQt5.QtCore import Qt, QFile, QTimer, pyqtSignal
from PyQt5.QtWidgets import QLabel, QApplication, QWidget, QBoxLayout, QVBoxLayout, QGroupBox
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QFrame, QLineEdit, QSpacerItem, QSizePolicy
from GUI.resources.style.ui_style import KFont, KColor
from GUI.resources import resources


class BusyWidget(QLabel):
    def __init__(self, parent=None):
        super(BusyWidget, self).__init__(parent)
        self.gif_busy_gif = QMovie(":/images/busy.gif")
        self.setMovie(self.gif_busy_gif)
        self.start_busy()
        self.stop_busy()
        self.resize(20, 20)

    def start_busy(self):
        self.gif_busy_gif.start()

    def stop_busy(self):
        self.gif_busy_gif.stop()

    def control_action(self, start):
        if start:
            self.start_busy()
        else:
            self.stop_busy()


class StatisticLabel(QWidget):
    value_change_signal = pyqtSignal(str)
    name_change_signal = pyqtSignal(str)
    value_style_signal = pyqtSignal(str)
    name_style_signal = pyqtSignal(str)

    def __init__(self, parent=None, position="RIGHT", font=KFont.FONT_14):
        super(StatisticLabel, self).__init__(parent)
        self.name = QLabel()
        self.name.setFont(font)
        self.value = QLabel()
        self.value.setFont(font)
        fm = QFontMetrics(font)
        wd = fm.width("100%")
        self.value.setMinimumWidth(wd)
        self.value.setAlignment(Qt.AlignCenter)
        self.name.setBuddy(self.value)
        layout = QBoxLayout(QBoxLayout.LeftToRight if position == "LEFT" else QBoxLayout.TopToBottom)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.name, 1)
        layout.addWidget(self.value, 1)
        self.setLayout(layout)
        self.create_signal_action()

    def create_signal_action(self):
        self.value_change_signal.connect(self.value.setText)
        self.name_change_signal.connect(self.name.setText)
        self.value_style_signal.connect(self.setStyleSheet)
        self.name_style_signal.connect(self.setStyleSheet)

    def set_name(self, name):
        self.name_change_signal.emit(str(name))

    def set_value(self, value):
        self.value_change_signal.emit(str(value))

    def get_value(self):
        return self.value.text()

    def get_name(self):
        return self.name.text()

    def set_font_color(self, color):
        try:
            self.name_style_signal.emit(color)
            self.value_style_signal.emit(color)
        except Exception as e:
            print e, traceback.format_exc()


class Yield(QWidget):

    def __init__(self, parent=None):
        super(Yield, self).__init__(parent)
        self.main_layout = QVBoxLayout()
        self.lbl_pass = StatisticLabel(position="LEFT")
        self.lbl_fail = StatisticLabel(position="LEFT")
        self.lbl_rate = StatisticLabel(position="LEFT")

        self.lbl_pass.set_name("P:")
        self.lbl_pass.set_font_color(KColor.green)
        self.lbl_fail.set_name("F:")
        self.lbl_fail.set_font_color(KColor.red)
        self.lbl_rate.set_name("R:")
        self.lbl_rate.set_font_color(KColor.blue)
        self.clear_all()
        self.main_layout.addWidget(self.lbl_pass)
        self.main_layout.addWidget(self.lbl_fail)
        self.main_layout.addWidget(self.lbl_rate)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def create_signal_action(self):
        self.lbl_pass_signal.connect(self.lbl_pass.set_value())

    def clear_all(self):
        self.lbl_pass.set_value(0)
        self.lbl_fail.set_value(0)
        self.lbl_rate.set_value("0%")

    def set_pass_value(self, value):
        self.lbl_pass.set_value(value)

    def get_pass_value(self):
        return self.lbl_pass.get_value()

    def set_fail_value(self, value):
        self.lbl_fail.set_value(value)

    def get_fail_value(self):
        return self.lbl_fail.get_value()

    def result_pass(self):
        current = int(self.get_pass_value())
        current += 1
        self.set_pass_value(current)
        self.cal_rate()

    def result_fail(self):
        current = int(self.get_fail_value())
        current += 1
        self.set_fail_value(current)
        self.cal_rate()

    def cal_rate(self):
        p = float(self.get_pass_value())
        f = float(self.get_fail_value())
        total = p + f
        if total == 0:
            self.lbl_rate.set_value("0%")
        else:
            result = round(p / total * 100, 1)
            self.lbl_rate.set_font_color(KColor.blue)
            if result > 80:
                self.lbl_rate.set_font_color(KColor.blue)
            else:
                self.lbl_rate.set_font_color(KColor.red)
            self.lbl_rate.set_value("{}%".format(result))


class AllYield(QGroupBox):
    lbl_fail_count_signal = pyqtSignal(str)
    lbl_pass_count_signal = pyqtSignal(str)
    lbl_fail_rate_signal = pyqtSignal(str)
    lbl_pass_rate_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(AllYield, self).__init__(parent)

        main_layout = QHBoxLayout()
        h1 = QVBoxLayout()
        btn_reset = ResetButton()
        btn_reset.clicked.connect(self.clean)
        lbl_pass = QLabel("PASS:")
        lbl_fail = QLabel("FAIL:")
        h1.addWidget(btn_reset, 1)
        h1.addWidget(lbl_pass)
        h1.addWidget(lbl_fail)
        h1.setContentsMargins(0, 0, 0, 0)
        h1.setSpacing(0)

        h2 = QVBoxLayout()
        lbl_fail_1 = QLabel("Tested:")
        self.lbl_pass_count = QLabel("0")
        self.lbl_fail_count = QLabel("0")
        h2.addWidget(lbl_fail_1)
        h2.addWidget(self.lbl_pass_count)
        h2.addWidget(self.lbl_fail_count)
        h2.setContentsMargins(0, 0, 0, 0)
        h2.setSpacing(0)

        h3 = QVBoxLayout()
        lbl_rate = QLabel("Rate:")
        self.lbl_pass_rate = QLabel("0%")
        self.lbl_pass_rate.setStyleSheet(KColor.green)
        self.lbl_fail_rate = QLabel("0%")
        self.lbl_fail_rate.setStyleSheet(KColor.red)
        h3.addWidget(lbl_rate)
        h3.addWidget(self.lbl_pass_rate)
        h3.addWidget(self.lbl_fail_rate)
        h3.setSpacing(0)
        h3.setContentsMargins(0, 0, 0, 0)

        main_layout.addLayout(h1)
        main_layout.addLayout(h2)
        main_layout.addLayout(h3)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setFixedHeight(60)
        self.setFixedWidth(200)
        self.create_signal_action()

    def create_signal_action(self):
        self.lbl_fail_count_signal.connect(self.lbl_fail_count.setText)
        self.lbl_pass_count_signal.connect(self.lbl_pass_count.setText)
        self.lbl_fail_rate_signal.connect(self.lbl_fail_rate.setText)
        self.lbl_pass_rate_signal.connect(self.lbl_pass_rate.setText)

    def clean(self):
        self.lbl_fail_count_signal.emit('0')
        self.lbl_pass_count_signal.emit('0')
        self.lbl_fail_rate_signal.emit('0%')
        self.lbl_pass_rate_signal.emit('0%')

    def set_pass_value(self, value):
        self.lbl_pass_count_signal.emit(str(value))

    def get_pass_value(self):
        return self.lbl_pass_count.text()

    def set_fail_value(self, value):
        self.lbl_fail_count_signal.emit(str(value))

    def get_fail_value(self):
        return self.lbl_fail_count.text()

    def result_pass(self):
        current = int(self.get_pass_value())
        current += 1
        self.set_pass_value(current)
        self.cal_pass_rate()
        self.cal_rate()

    def result_fail(self):
        current = int(self.get_fail_value())
        current += 1
        self.set_fail_value(current)
        self.cal_pass_rate()
        self.cal_rate()

    def cal_rate(self):
        f = float(self.get_fail_value())
        total = f + float(self.get_pass_value())
        fr = round(f / total * 100, 1)
        self.lbl_fail_rate_signal.emit("{}%".format(fr))

    def cal_pass_rate(self):
        f = float(self.get_pass_value())
        total = f + float(self.get_fail_value())
        fr = round(f / total * 100, 1)
        self.lbl_pass_rate_signal.emit("{}%".format(fr))


class ResetButton(QPushButton):

    def __init__(self, parent=None):
        super(ResetButton, self).__init__(parent)
        self.setFixedSize(20, 20)
        self.load_style_sheet("resetbutton")

    def load_style_sheet(self, sheet_name):

        qss_file = QFile(":/qss/%s.qss" % sheet_name.lower())
        qss_file.open(QFile.ReadOnly)
        style_sheet = qss_file.readAll()
        if sys.version_info < (3, 0):
            # Python v2.
            style_sheet = unicode(style_sheet, encoding='utf8')
        else:
            # Python v3.
            style_sheet = str(style_sheet)
        self.setStyleSheet(style_sheet)


class Counter(QLabel):
    timer_signal = pyqtSignal(bool)

    def __init__(self, parent=None, font=KFont.FONT_16_BOLD):
        super(Counter, self).__init__(parent)
        self._start_time = 0
        self.setMinimumWidth(60)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFont(font)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._counting)

        self.setText("{} s".format(0))
        self.setStyleSheet(KColor.blue)
        self.timer_signal.connect(self.operate_timer)

    def _counting(self):
        t = time.time() - self._start_time
        self.setText("{} s".format(round(t, 1)))

    def operate_timer(self, flag):
        if flag:
            self._start_time = time.time()
            self._timer.start(100)
        else:
            self._timer.stop()
            self._start_time = 0

    def start_the_timer(self):
        self.timer_signal.emit(True)
        # self._start_time = time.time()
        # self._timer.start(100)

    def stop_the_timer(self):
        self.timer_signal.emit(False)
        # self._timer.stop()
        # self._start_time = 0


class YieldAndTimer(QFrame):
    def __init__(self, parent=None, yield_flag=True):
        super(YieldAndTimer, self).__init__(parent)
        main_layout = QHBoxLayout()
        self.gif_busy = BusyWidget()
        self.yield_flag = yield_flag
        # self.gif_busy.start()
        self._timer = Counter(font=KFont.FONT_16_BOLD)
        if yield_flag:
            self._btn_reset = ResetButton()
            self.yd = Yield()
            self._btn_reset.clicked.connect(self.clear)
            h1 = QHBoxLayout()
            h1.addWidget(self.gif_busy)
            h1.addWidget(self._btn_reset)
            h1.setSpacing(0)
            h1.setContentsMargins(0, 0, 0, 0)
            v = QVBoxLayout()
            v.addWidget(self._timer)
            v.addLayout(h1)
            v.setSpacing(0)
            v.setContentsMargins(0, 0, 0, 0)
            main_layout.addLayout(v)
            main_layout.addWidget(self.yd)
        else:
            main_layout.addWidget(self.gif_busy, 1)
            main_layout.addWidget(self._timer, 4)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setStyleSheet(KColor.bg_white)

    def clear(self):
        self.yd.clear_all()

    def pass_result(self):
        if self.yield_flag:
            self.yd.result_pass()

    def fail_result(self):
        if self.yield_flag:
            self.yd.result_fail()

    def loading_enable(self):
        self.gif_busy.start_busy()

    def loading_disable(self):
        self.gif_busy.stop_busy()

    def start(self):
        self._timer.start_the_timer()

    def stop(self):
        self._timer.stop_the_timer()

    def get_pass(self):
        if self.yield_flag:
            return int(self.yd.get_pass_value())
        else:
            return 0

    def get_fail(self):
        if self.yield_flag:
            return int(self.yd.get_fail_value())
        else:
            return 0

    def get_total(self):
        return self.get_fail() + self.get_pass()


class MyLineText(QWidget):
    def __init__(self, parent=None, position="RIGHT"):
        super(MyLineText, self).__init__(parent)
        self._name = QLabel()
        self._value = QLineEdit()
        self._name.setBuddy(self._value)
        layout = QBoxLayout(QBoxLayout.LeftToRight if position == "LEFT" else QBoxLayout.TopToBottom)
        # layout.setStretch(1,2)
        # layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._name, 1, Qt.AlignRight)
        layout.addWidget(self._value, 1, Qt.AlignLeft)
        self.setLayout(layout)

    def setName(self, name):
        self._name.setText(str(name))

    def getName(self):
        return self._name.text()

    def setValue(self, value):
        self._value.setText(str(value))

    def getValue(self):
        return self._value.text()

    def setMyFont(self, font=QFont("Timers", 14)):
        assert isinstance(font, QFont)
        self._name.setFont(font)
        self._value.setFont(font)


class MyLabel(QWidget):
    def __init__(self, parent=None, position="TOP"):
        super(MyLabel, self).__init__(parent)
        self._name = QLabel()
        self._value = QLabel()
        self._name.setBuddy(self._value)
        self._layout = QBoxLayout(QBoxLayout.LeftToRight if position == "LEFT" else QBoxLayout.TopToBottom)
        # layout.setStretch(1,2)
        # layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        spaceItem1 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.addItem(spaceItem1)
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

    def set_myfont(self, name_font=KFont.FONT_14, value_font=KFont.FONT_14):
        assert isinstance(name_font, QFont)
        assert isinstance(value_font, QFont)
        # self._name.setFixedSize()
        self._name.setFont(name_font)
        self._value.setFont(value_font)

    def set_stytle_sheet(self, name_stytle_sheet, value_stytle_sheet):
        self._name.setStyleSheet(name_stytle_sheet)
        self._value.setStyleSheet(value_stytle_sheet)

    def set_name_stytle(self, *args):
        st = "".join(args)
        self._name.setStyleSheet(st)

    def set_value_stytle(self, *args):
        st = "".join(args)
        self._value.setStyleSheet(st)

    def set_space(self, value):
        assert isinstance(value, int)
        self._layout.setSpacing(value)

    def set_contents_margins(self, *args):
        self.setContentsMargins(*args)

    def same_size(self, width, lenth):
        self._name.setFixedSize(int(width), int(lenth))
        self._value.setFixedSize(int(width / 2), int(lenth))
        self._name.setAlignment(Qt.AlignCenter)
        self._value.setAlignment(Qt.AlignCenter)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wi = AllYield()
    wi.show()
    sys.exit(app.exec_())
