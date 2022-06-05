#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import re
import zmq
import time
import traceback
from Configure import constant, zmqports, levels, events
from multiprocessing import Process, Manager
from GUI.protocal.sequencerprotocal import SequencerProtocol
from PyQt5.QtCore import QThread, pyqtSignal



class SequencerSubscriberProcess(Process):
    SITE_PATTERN = re.compile(r'Sequencer_(\d+)')

    def __init__(self, queue):
        super(SequencerSubscriberProcess, self).__init__()
        self._receiving = True
        self._queue = queue
        self._level = levels.REPORTER
        self._poller = zmq.Poller()

    def register_subscribers_of_sequencers(self):

        ctx = zmq.Context.instance()
        url = 'tcp://127.0.0.1:'
        for i in range(constant.SLOTS):
            sub_socket = ctx.socket(zmq.SUB)
            address = '{}{}'.format(url, zmqports.SEQUENCER_PUB + i)
            sub_socket.connect(address)
            sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
            self._poller.register(sub_socket, zmq.POLLIN)

    def receive_sequencer(self, i):
        ctx = zmq.Context.instance()
        url = 'tcp://127.0.0.1:'
        sub_socket = ctx.socket(zmq.SUB)
        address = '{}{}'.format(url, zmqports.SEQUENCER_PUB + i)
        sub_socket.connect(address)
        sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        while self._receiving:
            try:
                topic, ts, level, origin, data = sub_socket.recv_multipart(zmq.NOBLOCK)
                if int(level) == self.level:
                    site = int(re.match(self.SITE_PATTERN, origin).group(1))
                    message = SequencerProtocol.parse_report(data)
                    self._queue.put((site, message.copy()))
                else:
                    time.sleep(0.001)
            except zmq.ZMQError:
                time.sleep(0.1)

    def unregister_subscribers_of_sequencers(self):
        for socket in self.__get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def run(self):
        ctx = zmq.Context()

        for i in range(constant.SLOTS):
            url = 'tcp://127.0.0.1:'
            sub_socket = ctx.socket(zmq.SUB)
            address = '{}{}'.format(url, zmqports.SEQUENCER_PUB + i)
            sub_socket.connect(address)
            sub_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
            self._poller.register(sub_socket, zmq.POLLIN)
        _poller_socks = self.__get_sockets()
        site_pattern = re.compile(r'Sequencer_(\d+)')
        while self._receiving:
            try:
                socks = dict(self._poller.poll(1000))
                for fd, event in socks.items():
                    if fd in _poller_socks and event == zmq.POLLIN:
                        topic, ts, level, origin, data = fd.recv_multipart(zmq.NOBLOCK)
                        if int(level) == self._level:
                            site = int(re.match(site_pattern, origin).group(1))
                            message = SequencerProtocol.parse_report(data)
                            self._queue.put((site, message))

            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()
        self.unregister_subscribers_of_sequencers()

    def __get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets


from loadingframe import MyQSplashScreen
from PyQt5.QtGui import QPixmap

class TestEngineSubscriberProcess(QThread):

    data_signal = pyqtSignal(str, name='data_signal')


    def __init__(self):
        super(TestEngineSubscriberProcess, self).__init__()
        self._receiving = True
        self._level = levels.REPORTER
        self._poller = zmq.Poller()
        ctx = zmq.Context()
        url = 'tcp://127.0.0.1:'
        for i in range(constant.SLOTS):
            sub_socket = ctx.socket(zmq.SUB)
            address = '{}{}'.format(url, zmqports.TEST_ENGINE_PUB + i)
            print address
            sub_socket.connect(address)
            sub_socket.setsockopt(zmq.SUBSCRIBE, "")
            self._poller.register(sub_socket, zmq.POLLIN)

    def run(self):
        # _poller_socks = self.__get_sockets()
        # site_pattern = re.compile(r'TestEngine_(\d+)')
        while self._receiving:
            try:
                socks = dict(self._poller.poll(1000))
                for fd, event in socks.items():
                    if event == zmq.POLLIN:
                        topic, ts, level, origin, data = fd.recv_multipart(zmq.NOBLOCK)
                        if "FCT_HEARTBEAT" not in data:
                            self.data_signal.emit(data)
            except zmq.ZMQError as e:
                print e.message, traceback.format_exc()
        self.unregister_subscribers()

    def __get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def unregister_subscribers(self):
        for socket in self.__get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def stop(self):
        try:
            self._receiving = False
        except Exception as e:
            raise e
        self.wait()
        del self





#
# import sys
# from PyQt5.QtWidgets import QApplication
#
#
# if __name__ == '__main__':
#
#
#     app = QApplication(sys.argv)
#
#     p = TestEngineSubscriberProcess()
#     p.start()
#
#     sys.exit(app.exec_())


