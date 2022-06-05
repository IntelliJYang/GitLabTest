__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import serial
import socket
import time
import datetime
import select
import threading
import traceback
from abc import abstractmethod, ABCMeta, abstractproperty
from threading import Thread


def print_with_time(info):
    print datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f --------> {}'.format(info))


class KAbstractDriver(object):
    __metaclass__ = ABCMeta

    def __init__(self, publisher=None):
        self.publisher = publisher

    def log(self, msg):
        print_with_time(msg)
        if self.publisher:
            self.publisher.publish(msg)

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractproperty
    def is_open(self):
        pass

    @abstractmethod
    def send(self, cmd, description=''):
        pass

    @abstractmethod
    def send_by_byte(self, cmd, interval=0.005, description=''):
        pass

    @abstractmethod
    def set_timeout(self, timeout=3):
        """
        set communication timeout
        :param timeout: ms
        :return:
        """
        pass

    @abstractmethod
    def read(self, size=0, timeout=None):
        pass


class KSerialPortBgRead(KAbstractDriver):
    def __init__(self, port_name, baud_rate=921600, timeout=6, end_str='\n', recv_signal=None):
        super(KSerialPortBgRead, self).__init__()
        self._port_name = port_name
        self._baud_rate = baud_rate
        self._timeout = timeout
        self._end_str = end_str
        self._b_read_in_background = False
        self._detect_str = ''
        self._port = None
        self._str_buffer = ''
        self._lock = threading.Lock()
        self._recv_signal = recv_signal

    def connect(self):
        if not self.is_open():
            # if not serial not open, then reopen.
            try:
                self._port = serial.Serial(self._port_name, baudrate=self._baud_rate, timeout=self._timeout)
                self._b_read_in_background = True
            except Exception:
                self._b_read_in_background = False
                raise Warning("Open serial port error: %s", self._port_name)
            if self._b_read_in_background:
                t = Thread(target=self._read_data_in_background, name=self._port_name)
                t.setDaemon(True)
                t.start()
                return True
            return False
        return True

    def close(self):
        if self._port.isOpen():
            self._port.flush()
            self._port.close()
            self._b_read_in_background = False

    def send(self, cmd, description=''):
        if self._port.isOpen():
            self._port.flushInput()
            self._port.flushOutput()
            self._port.write(cmd + self._end_str)
            self.log(description + '[Send:]' + cmd + self._end_str)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self._port.name)

    def send_by_byte(self, cmd, interval=0.005, description=''):
        if self._port.isOpen():
            self._port.flushInput()
            self._port.flushOutput()
            self.log(cmd)
            for sc in cmd:
                self._port.write(sc)
                time.sleep(interval)
            self._port.write(self._end_str)
            self.log(description + '[Send:]' + cmd + self._end_str)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self._port.name)

    def set_timeout(self, timeout=3):
        self._timeout = timeout
        self._port.timeout = self._timeout

    def is_open(self):
        try:
            return self._port.isOpen()
        except Exception:
            return False

    def read(self, size=0, timeout=None):
        # if timeout is none, make self._timeout as timeout
        if timeout is None:
            timeout = self._timeout
        begin_time = time.time()
        if size != 0:
            while True:
                if len(self._str_buffer) >= size:
                    self._lock.acquire(True)
                    result = self._str_buffer[:size]
                    self._str_buffer = self._str_buffer[size:]
                    self._lock.release()
                    return result
                if time.time() - begin_time > timeout:
                    timeout_happen = True
                    break
                time.sleep(0.005)
            if timeout_happen:
                return 'Timeout'
        return ''

    def read_string(self):
        """
        read all buffer data, and then empty buffer
        :return:
        """
        return_str = ''
        if self._lock.acquire(True):
            return_str = self._str_buffer
            self._str_buffer = ''
            self._lock.release()
        return return_str

    def wait_detect(self, timeout=6):
        """
        wait detect string until timout
        :param timeout:
        :return:
        """
        detect = False
        timeout_happen = False
        begin = time.time()
        if self.is_open():
            # detect string until found or timeout
            while True:
                if self._lock.acquire(True):
                    detect = self._detect_str in self._str_buffer
                self._lock.release()
                if detect:
                    break
                if time.time() - begin > timeout:
                    timeout_happen = True
                    break
                else:
                    time.sleep(0.05)
            if timeout_happen:
                return False, 'timeout'
            else:
                return detect, self._detect_str

    def set_detect_string(self, string):
        """
        set detect string
        :param string:
        :return:
        """
        self._detect_str = string

    def _read_existing(self):
        res = self._port.read(self._port.inWaiting())
        if res != "":
            self.log('[Receive:]' + res)
        return res

    def _read_data_in_background(self):
        """
        read data in a single thread
        :return:
        """
        while self._b_read_in_background:
            ret, _, _ = select.select([self._port], [], [], 0)
            if ret:
                self._analysis_data(self._read_existing())
            time.sleep(0.001)

    def _analysis_data(self, data):
        """
        analysis the input data
        :param data:
        :return:
        """
        if self._recv_signal:
            self._recv_signal.emit(data)
            # self._recv_signal.emit(self._end_str)

        if self._lock.acquire(True):
            self._str_buffer += data
        self._lock.release()


class KTcpSocketBgRead(KAbstractDriver):
    def __init__(self, ip, port, end_str='\r\n', timeout=0.5, publisher=None, recv_signal=None):
        super(KTcpSocketBgRead, self).__init__(publisher)
        self._ip = ip
        self._port = port
        self._end_str = end_str
        self._timeout = timeout
        self._session = None
        self._status = False
        self._b_read_in_background = False
        self._lock = threading.Lock()
        self._str_buffer = ''
        self._recv_signal = recv_signal

    def connect(self):
        if not self.is_open():
            try:
                self._session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._session.settimeout(self._timeout)
                if self._session.connect_ex((self._ip, self._port)) == 0:
                    self._b_read_in_background = True
                    self._status = True
                else:
                    self._status = False
            except Exception:
                self._status = False
                raise RuntimeWarning("Can not connect to %s:%s" % (self._ip, self._port))
            if self._status:
                # new thread for reading data
                read_thread = threading.Thread(target=self._read_data_in_background,
                                               name='{}:{}'.format(self._ip, self._port))
                read_thread.setDaemon(True)
                read_thread.start()
                return True
            else:
                return False
        return True

    def close(self):
        if self.is_open():
            self._session.shutdown(socket.SHUT_RDWR)
            self._b_read_in_background = False
            self._session.close()
            self._session = None
            self._status = False
            return True
        return True

    def set_timeout(self, timeout=3):
        self._timeout = timeout

    def send(self, cmd, description='SEND'):
        """
        send cmd in one
        :param cmd:
        :param description:
        :return:
        """
        msg = ''
        if self.is_open():
            try:
                self.log(" >>>>>> [ {} --> '{}' ]".format(description, cmd))
                self._session.send(cmd + self._end_str)
            except Exception:
                self._status = False
                msg = ("CMD Send Error, %s:%s" % (self._ip, self._port))
                raise RuntimeWarning(msg)
        else:
            msg = ("%s:%d did not connected" % (self._ip, self._port))

        return self._status, msg

    def send_by_byte(self, cmd, interval=0.005, description='SEND'):
        """
        send cmd one by one byte
        :param cmd:
        :param interval:
        :param description:
        :return:
        """
        msg = ''
        if self.is_open():
            try:
                for i in cmd:
                    self._session.send(i)
                    time.sleep(interval)
                self._session.send(self._end_str)
                self.log(" >>>>>> [ {} --> '{}' ]".format(description, cmd))
            except Exception:
                self._status = False
                msg = ("CMD Send Error, %s:%s" % (self._ip, self._port))
                raise RuntimeWarning(msg)
        else:
            self._status = False
            msg = ("%s:%s did not connected", self._ip, self._port)
        return self._status, msg

    def is_open(self):
        return self._status

    def read(self, size=0, timeout=None):
        """
        read
        :param timeout
        :param size:
        :return:
        """
        if timeout is None:
            timeout = self._timeout
        begin_time = time.time()
        if size != 0:
            while True:
                if len(self._str_buffer) >= size:
                    self._lock.acquire(True)
                    result = self._str_buffer[:size]
                    self._str_buffer = self._str_buffer[size:]
                    self._lock.release()
                    return result
                if time.time() - begin_time > timeout:
                    timeout_happen = True
                    break
                time.sleep(0.005)
            if timeout_happen:
                raise RuntimeWarning('Timeout')
        return ''

    def read_string(self):
        self._lock.acquire(True)
        res = self._str_buffer
        self._str_buffer = ''
        self._lock.release()
        return res

    def wait_detect(self, detect_str, timeout=6):
        """
        wait detect string until timout
        :param detect_str
        :param timeout:
        :return:
        """
        detect = False
        timeout_happen = False
        begin = time.time()
        if self.is_open():
            # detect string until found or timeout
            while True:
                if self._lock.acquire(True):
                    detect = detect_str in self._str_buffer
                self._lock.release()
                if detect:
                    break
                if time.time() - begin > timeout:
                    timeout_happen = True
                    break
                else:
                    time.sleep(0.05)
            if timeout_happen:
                return False, 'timeout'
            else:
                return detect, detect_str

    def _read_data_in_background(self):
        while self._b_read_in_background:
            ret, _, _ = select.select([self._session], [], [], 0)
            if ret:
                try:
                    res = self._session.recv(1024)
                    self._analysis_data(res)
                except Exception:
                    self._status = False
                    raise RuntimeWarning(Exception)

            time.sleep(0.001)

    def _analysis_data(self, data):
        if self._recv_signal:
            self._recv_signal.emit(data)

        if self._lock.acquire(True):
            self._str_buffer += data
        self._lock.release()


class KTcpSocket(KAbstractDriver):
    def __init__(self, ip, port, end_str='\r\n', timeout=0.5, publisher=None):
        super(KTcpSocket, self).__init__(publisher)
        self._ip = ip
        self._port = port
        self._end_str = end_str
        self._timeout = timeout
        self._session = None
        self._status = False
        self._b_read_in_background = False
        self._lock = threading.Lock()
        self._str_buffer = ''
        self.connect()

    def connect(self):
        if not self.is_open():
            try:
                self._session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._session.settimeout(self._timeout)
                if self._session.connect_ex((self._ip, self._port)) == 0:
                    self._status = True
                else:
                    self._status = False
            except Exception:
                self._status = False
                raise RuntimeError("Can not connect to %s:%s" % (self._ip, self._port))
        return self._status

    def close(self):
        if self.is_open():
            self._session.shutdown(socket.SHUT_RDWR)
            self._session.close()
            self._session = None
            self._status = False
        return True

    def send(self, cmd, description='SEND'):
        """
        send cmd in one
        :param cmd:
        :param description:
        :return:
        """
        if self.is_open():
            try:
                self.log(" >>>>>> [ {} --> '{}' ]".format(description, cmd))
                self._session.send(cmd + self._end_str)
            except Exception:
                raise RuntimeError("CMD Send Error, %s:%s" % (self._ip, self._port))
        else:
            raise RuntimeError("%s:%s did not connected" % (self._ip, self._port))

    def send_by_byte(self, cmd, interval=0.005, description='SEND'):
        """
        send cmd one by one byte
        :param cmd:
        :param interval:
        :param description:
        :return:
        """
        if self.is_open():
            try:
                for i in cmd:
                    self._session.send(i)
                    time.sleep(interval)
                self._session.send(self._end_str)
                self.log(" >>>>>> [ {} --> '{}' ]".format(description, cmd))
            except Exception:
                raise RuntimeError("CMD Send Error, %s:%s", self._ip, self._port)
        else:
            raise RuntimeError("%s:%s did not connected", self._ip, self._port)

    def read(self, size=0, timeout=None):
        if self.is_open():
            ret = self._session.recv(size)
            b_ret = True
        else:
            b_ret = False
            ret = "ERROR-TCP_DISCONNECT"

        return b_ret, ret

    def set_timeout(self, timeout=3):
        self._timeout = timeout
        self._session.settimeout(timeout)

    def is_open(self):
        return self._status

    def read_line(self, timeout):
        if self.is_open():
            return self.read_until('\n', timeout=timeout)
        else:
            return "ERROR-TCP_DISCONNECT"

    def read_until(self, terminator='\r\n', next_line_check=False, next_line_flag='', timeout=None):
        if timeout is None:
            timeout = self._timeout
        timeout_happen = False
        line = ""
        # collect start time
        begin = time.time()
        if self.is_open():
            while True:
                c = self._session.recv(1)
                if c:
                    line += c
                    if line.rfind(terminator) > 0:
                        if next_line_check:
                            if line.split('\n')[-1].split() == next_line_flag:
                                break
                        else:
                            break
                    time.sleep(0.001)
                if time.time() - begin > timeout:
                    timeout_happen = True
                    break
            if timeout_happen:
                raise RuntimeError("Error: timeout %s", line)
            return line
        else:
            raise RuntimeError("%s:%s did not connected", self._ip, self._port)


class KSerialPort(KAbstractDriver):

    def __init__(self, port_name, baud_rate=115200, timeout=6, end_str='\n', publisher=None):
        super(KSerialPort, self).__init__(publisher)
        self._timeout = timeout
        self._end_str = end_str
        self._port_name = port_name
        self._baud_rate = baud_rate
        self._port = None
        self.flag = False

    def connect(self):
        """
        no need open cause init Serial means open
        didn't set timeout means block
        :return: True
        """
        b_ret = True
        if not self._port:
            try:
                b_ret = True
                self._port = serial.Serial(self._port_name, self._baud_rate)
            except Exception as e:
                b_ret = False
                print e, traceback.format_exc()
            finally:
                return b_ret
        return b_ret

    def close(self):
        if self.is_open():
            self._port.flush()
            self._port.close()
            self._port = None

        return True

    def is_open(self):
        """
        whether serial is open
        :return: bool
        """
        if self._port is None:
            return False
        b_ret = True
        try:
            b_ret = self._port.isOpen()
        except Exception as e:
            b_ret = False
            print "can not found device: {}!!!".format(self._port_name), e, traceback.format_exc()
        finally:
            return b_ret

    def send(self, cmd, description='SEND'):
        """
        send cmd by serial port
        :return:
        """
        b_ret = True
        if self.is_open():
            # flush buffer
            self._port.flushInput()
            self._port.flushOutput()
            try:
                self._port.write(cmd)
            except Exception as e:
                b_ret = False
                print e, traceback.format_exc()
        else:
            b_ret = False
            print "Cmd send error, port not open: %s" % self._port.name, traceback.format_exc()

        return b_ret

    def send_by_byte(self, cmd, interval=0.005, description=''):
        b_ret = True
        if self._port.isOpen():
            self._port.flushInput()
            self._port.flushOutput()
            self.log(cmd)
            for sc in cmd:
                self._port.write(sc)
                time.sleep(interval)
            self._port.write(self._end_str)
            self.log(description + '[Send:]' + cmd + self._end_str)
        else:
            b_ret = False
            print ("Cmd send error, port not open: %s", self._port.name), traceback.format_exc()
        return b_ret

    def read(self, size=0, timeout=None):
        b_ret = True
        line = ''
        if self.is_open():
            try:
                for i in range(size):
                    c = self._port.read(1)
                    if c:
                        line += c
            except Exception as e:
                b_ret = False
                print e, traceback.format_exc()
        else:
            b_ret = False
            line = "ERROR-SERIAL_DISCONNECT"

        return b_ret, line

    def set_timeout(self, timeout=3):
        self._timeout = timeout
        self._port.settimeout(timeout)

    def read_line(self):
        b_ret = True
        if self.is_open():
            try:
                ret = self._port.readline()
            except Exception as e:
                b_ret = False
                ret = e
                print e, traceback.format_exc()
        else:
            b_ret = False
            return "ERROR-SERIAL_DISCONNECT"
        return b_ret, ret

    def read_until(self, terminator, next_line_check=False, next_line_flag='', timeout=None):
        b_ret = True
        if timeout is None:
            timeout = self._timeout
        timeout_happen = False
        line = ""
        # collect start time
        begin = time.time()
        if self.is_open():
            while True:
                c = self._port.read(1)
                if c:
                    line += c
                    if line.rfind(terminator) > 0:
                        if next_line_check:
                            if line.split('\n')[-1].split() == next_line_flag:
                                break
                        else:
                            break
                    time.sleep(0.001)
                if time.time() - begin > timeout:
                    timeout_happen = True
                    break
            if timeout_happen:
                b_ret = False
                line = 'TIMEOUT'
        else:
            b_ret = False
            line = 'DISCONNECTED'
        return b_ret, line

    def read_all(self):
        b_ret = True
        if self.is_open():
            try:
                ret = self._port.read(self._port.inWaiting())
            except Exception as e:
                b_ret = False
                ret = e
        else:
            b_ret = False
            ret = 'disconnected'
        return b_ret, ret
