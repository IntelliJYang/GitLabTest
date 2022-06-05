# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, qApp
from Configure.constant import SLOTS
import time


class MyQSplashScreen(QtWidgets.QSplashScreen):

    def __init__(self, *args):
        super(MyQSplashScreen, self).__init__(*args)
        self.txt_buffer = list()
        self.flag = True



    def mousePressEvent(self, QMouseEvent):
        pass

    def append(self, data):
        print "addend: {}".format(len(self.txt_buffer))
        self.clearMessage()
        self.txt_buffer.append(str(data))
        new_string = "".join(self.txt_buffer)
        if "ERROR" in new_string.upper():
            self.showMessage(new_string, QtCore.Qt.AlignBottom, QtCore.Qt.red)
            if "ERROR" in str(data.upper()):
                QMessageBox.warning(QMessageBox(), "ERROR", data)
            self.flag = False
        else:
            self.showMessage(new_string, QtCore.Qt.AlignBottom, QtCore.Qt.blue)



    def clear(self):
        if len(self.txt_buffer) == 0:
            self.flag = False
        self.txt_buffer = list()
        self.clearMessage()
        return self.flag


# class MyWindow(QtWidgets.QPushButton):
#
#     def __init__(self):
#         QtWidgets.QPushButton.__init__(self)
#         self.setText("关闭窗口")
#         self.clicked.connect(QtWidgets.qApp.quit)
#
#     def load_data(self, sp):
#         for i in range(1, 11):              #模拟主程序加载过程
#             time.sleep(2)
#             # 加载数据
#             sp.append("加载... {0}%".format(i * 10))
#             # sp.showMessage("加载... {0}%".format(i * 10), QtCore.Qt.AlignHCenter |QtCore.Qt.AlignBottom, QtCore.Qt.black)
#             QtWidgets.qApp.processEvents()  # 允许主进程处理事件
#
#
#
#
#
# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     splash = MyQSplashScreen(QtGui.QPixmap("/Users/prmeasure/Desktop/intelligent.png"))
#     splash.showMessage("加载... 0%", QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom, QtCore.Qt.black)
#
#     splash.show()                           # 显示启动界面
#     QtWidgets.qApp.processEvents()          # 处理主进程事件
#     window = MyWindow()
#     window.setWindowTitle("QSplashScreen类使用")
#     window.resize(300, 30)
#     window.load_data(splash)                # 加载数据
#     window.show()
#     splash.finish(window)                   # 隐藏启动界面