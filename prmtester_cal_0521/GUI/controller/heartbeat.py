#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import sys
import zmq
import traceback
from Configure.zmqports import PUB_CHANNEL
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject, QTimer, QRect, Qt
from PyQt5.QtWidgets import QLabel, QApplication
from threading import Thread
from GUI.resources import resources


class HeartBeatController(object):
    @staticmethod
    def create_background_color(colorstr='green'):
        background = ':/images/circle_%s_24px.png' % colorstr
        return background

    def __init__(self, index, int_port, str_name=None):
        """
        :param index: the number show in
        :param int_port:
        """
        self.str_name = str_name
        self.index = index
        super(HeartBeatController, self).__init__()
        self._beating = True
        self._hb_count = 0
        self._hb_happened = False
        # init three state image
        self._green_image = self.create_background_color('green')
        self._red_image = self.create_background_color('red')
        self._grey_image = self.create_background_color('grey')
        self._current_image = self._green_image

        self.view = WidgetHeartBeat(index)
        self._port = int_port
        self._subscriber = None
        self._poller = zmq.Poller()
        self.create_heart_beat_subscriber()

        # crate a timer to blink every 1 second
        self._timer = QTimer()
        self._timer.timeout.connect(self.change_image)
        self._timer.start(1000)

        # single daemon thread to receive heart beat message
        t = Thread(target=self.run_heart_beat_thread)
        t.setDaemon(True)
        t.start()

    def create_heart_beat_subscriber(self):
        """
        create a zmq.sub socket to subscribe PUB_CHANNEL
        use poll to get pollin message
        :return:
        """
        url = 'tcp://127.0.0.1'
        ctx = zmq.Context()
        self._subscriber = ctx.socket(zmq.SUB)
        self._subscriber.setsockopt(zmq.SUBSCRIBE, PUB_CHANNEL)
        self._subscriber.connect('%s:%d' % (url, self._port))
        self._poller.register(self._subscriber, zmq.POLLIN)

    def change_image(self):
        """
        change image
        :return:
        """
        if self._hb_count % 2 == 1:
            self._current_image = self._grey_image
        else:
            if not self._hb_happened or self._hb_count >= 10:
                if self.str_name == "Engine":
                    with open("/tmp/HeartBeat_Slot{}.txt".format(self.index),"w") as f:
                        f.writelines("0")
                self._current_image = self._red_image
            else:
                if self.str_name == "Engine":
                    with open("/tmp/HeartBeat_Slot{}.txt".format(self.index),"w") as f:
                        f.writelines("1")
                self._current_image = self._green_image

        self._hb_count += 1
        self.view.setStyleSheet('background-image:url(%s)' % self._current_image)

    def run_heart_beat_thread(self):
        """
        subscribe heart beat message
        :return:
        """
        while self._beating:
            try:
                socks = dict(self._poller.poll(5000))
                if socks.get(self._subscriber) == zmq.POLLIN:
                    topic, ts, level, origin, msg = self._subscriber.recv_multipart(zmq.NOBLOCK)
                    if msg == 'FCT_HEARTBEAT':
                        self._online()
            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()

    def _offline(self):
        self._current_image = self._red_image
        self._hb_happened = False

    def _online(self):
        """
        if receive heart beat message, make all state to on line
        :return:
        """
        self._current_image = self._green_image
        self._hb_happened = True
        self._hb_count = 0


class WidgetHeartBeat(QLabel):
    def __init__(self, index):
        super(WidgetHeartBeat, self).__init__()
        self.setFixedHeight(24)
        self.setFixedWidth(24)
        self.setText(str(index))
        self.setAlignment(Qt.AlignCenter)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hb = HeartBeatController(1, 6150)
    hb.view.show()
    sys.exit(app.exec_())
