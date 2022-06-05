__Author__ = "Minghui.Wang"

import zmq
import os
import time
import serial
import socket
import traceback
import datetime
import telnetlib
from datetime import datetime
from mix.lynx.rpc.rpc_client import RPCClientWrapper
from threading import Thread

from publisher import ZmqPublisher,NoOpPublisher
import serial.tools.list_ports as pts
from mix.lynx.rpc.tinyrpc.protocols.jsonrpc import JSONRPCProtocol,JSONRPCServerError
from mix.lynx.rpc.tinyrpc.transports.zmq import ZmqClientTransport
from abc import abstractmethod, ABCMeta, abstractproperty



def print_with_time(info):
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f --------> {}'.format(info))


class AbstractDriver(object):
    __metaclass__ = ABCMeta

    def __init__(self, publisher=None):
        self.publisher = publisher

    def log(self, msg):
        print_with_time(msg)
        if isinstance(self.publisher, ZmqPublisher):
            self.publisher.publish(msg)

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractproperty
    def isOpen(self):
        pass

    @abstractmethod
    def send(self, cmd, description=''):
        pass

    @abstractmethod
    def receive(self, size=None):
        pass

    @abstractmethod
    def query(self, cmd, tmo, size=None):
        pass

    @abstractmethod
    def read_until(self, tmo=None, terminator=">", size=None):
        pass

    @abstractmethod
    def read_line(self, timeout):
        pass


class KSerial(AbstractDriver):

    def __init__(self, cfg, publisher=None):
        super(KSerial, self).__init__(publisher)
        self.timeout = cfg.get("timeout", 3000)
        self.terminator = cfg.get("terminator", "\n")
        self.port = cfg.get("port", None)
        self.baudrate = cfg.get("baudrate", "115200")
        self.__session = None
        self.flag = False
        # self.open()

    def open(self):
        """
        no need open cause init Serial means open
        didn't set timeout means block
        :return: True
        """
        if not self.__session:
            try:
                self.__session = serial.Serial(self.port, self.baudrate)
            except Exception as e:
                return False
                # raise RuntimeError("Open serial port error: %s", self.port)
            return True

    def close(self):
        """
        close the port
        different version has different is_open
        is_open or isOpen()
        :return:
        """
        if self.isOpen():
            self.__session.flush()
            self.__session.close()
            del self.__session
            self.__session = None
            print("close port OK")

    def isOpen(self):
        """
        whether serial is open
        :return: bool
        """
        if self.__session:
            return self.__session.isOpen()
        else:
            return False

    def send(self, cmd, description=''):
        """
        send cmd by serial port
        :return:
        """
        if self.isOpen():
            # flush buffer
            self.__session.flushInput()
            self.__session.flushOutput()
            try:
                self.__session.write(cmd)
                print " >>>>>>>> SEND TO FIXTURE: {}".format(cmd.strip())
            except Exception as e:
                raise RuntimeError("cmd send error: ", e)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self.__session.name)

    def receive(self, size=None):
        """
        block
        :param size:
        :return:
        """
        line = str()
        lenterm = len(self.terminator)
        if self.isOpen():
            # res = self.read_until(self.timeout, terminator=self.terminator, size=size)
            # self.log(" <<<<<<<< RESPONSE FROM FIXTURE: {}".format(res.strip()))
            while True:
                c = self.__session.read(1)
                if c:
                    line += c
                    if str(line[-lenterm:]) == self.terminator:
                        break
            return line
        else:
            return "ERROR-SERIAL_DISCONNECT"

    def query(self, cmd, tmo, size=None):
        if self.isOpen():
            self.send(cmd)
            return self.read_until(tmo,
                                   self.terminator)  # self.read_line(tmo) if self.__terminator=='\n' else self.receive()
        else:
            return "ERROR-SERIAL_DISCONNECT"

    def read_line(self, timeout):
        """
        timeout is xxx.ms not s
        :param timeout:
        :return:
        """
        if self.isOpen():
            res = self.__session.readline(timeout)
            # self.log(" <<<<<<<< RESPONSE FROM FIXTURE: {}".format(res.strip()))
            return res
        else:
            return "ERROR-SERIAL_DISCONNECT"

    def read_until(self, tmo, terminator=">", size=None):
        """
        this method come from serialutil
        Read until a termination is found , the size
        is exceeded or until timeout occurs.
        no block
        """
        if self.isOpen():
            lenterm = len(terminator)
            print("terminator:" + terminator)
            line = str()

            timeout = self.timeout  # Timeout(self.timeout)
            start = time.time()
            while True:
                c = self.__session.read(1)
                if c:
                    line += c
                    # print("line :" + line)
                    if str(line[-lenterm:]) == terminator:
                        # print("line2 :" + line)
                        break
                    if size is not None and len(line) >= size:
                        # print("line1 :" + line)
                        break
                    if str(terminator) in line:
                        # print("line 3:"+line)
                        break
                if time.time() - start >= timeout:
                    return "ERROR - TIMEOUT"
            #     if timeout.expired():
            #         break
            # if timeout.expired():
            #     return "ERROR - TIMEOUT"
            return line
        else:
            return "ERROR-SERIAL_DISCONNECT"


    def read_all(self):
        if self.isOpen():
            if self.__session.inWaiting():
                return self.__session.readline(1000)
            else:
                return None
        else:
            return None



    @classmethod
    def create(cls, cfg, port):
        assert isinstance(cfg, dict)
        cfg_port = cfg
        cfg_port["port"] = port
        return cls(cfg_port)

    @classmethod
    def get_port_by_location(self, location, retry=3):
        for i in range(retry):
            for ser in pts.comports():
                if ser.location == location:
                    return ser.device
            time.sleep(1)
        return None


class KTcp(AbstractDriver):
    def __init__(self, cfg, publisher=None):
        super(KTcp, self).__init__(publisher)
        self.__timeout = cfg.get("timeout", 0.2)
        self.__net_config = (cfg.get("ip"), cfg.get("port"))
        self.__terminator = cfg.get("terminator", ")\r\n")
        # ensure zynq is connect well
        # os.system("ping {} -c 2 -t 2".format(cfg.get("ip")))
        self.__session = None
        self.__status = False
        self.open()

    def open(self):
        ret = False
        if not self.isOpen():
            try:
                self.__session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__session.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                self.__session.settimeout(self.__timeout)
            except Exception as e:
                ret = False
                raise e
            try:
                if self.__session.connect_ex(self.__net_config) == 0:

                    self.__status = True
                else:
                    self.__status = False
            except Exception as e:
                ret = False
                self.__status = False
        return ret

    def close(self):
        if self.__session and self.isOpen():
            self.__session.shutdown(socket.SHUT_RDWR)
            self.__session.close()
            del self.__session
            self.__status = False
            self.__session = None

    def isOpen(self):
        return self.__status

    def send(self, cmd, description=None):
        """
        all send's command should add description before command
        :param cmd:
        :param description:
        :return:
        """
        if self.isOpen():
            try:
                self.__session.send(cmd)
                if description:
                    self.log(str(datetime.now()) + ' '*3+"{0} Send Command:'{1}' ".format(description, cmd.strip()))
                else:
                    self.log(" >>>>>> [SEND: {}]".format(cmd.strip()))
            except Exception as e:
                raise RuntimeError("cmd send error: ", e)
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self.__session.name)

    def receive(self, size=None):
        if self.isOpen():
            return self.__session.recv(size)
        else:
            return "ERROR-TCP_DISCONNECT"

    def query(self, cmd, tmo=2000, size=None, description=None):
        if self.isOpen():
            self.send(cmd, description)
            # time.sleep(1)
            # return self.read()
            return self.read_until(tmo, terminator=self.__terminator, size=size, description=description)
        else:
            return "ERROR-TCP_DISCONNECT"

    def read_line(self, timeout):
        if self.isOpen():
            return self.read_until(timeout, terminator='\n')
        else:
            return "ERROR-TCP_DISCONNECT"

    def read_until(self, tmo=None, terminator=">", size=None, description=None):
        lenterm = len(terminator)
        timeout = 0
        line = str()
        c = str()
        if self.isOpen():
            while True:
                try:
                    c = self.__session.recv(1)
                except Exception as e:
                    timeout += self.__timeout * 1000
                    if timeout >= tmo:
                        return "ERROR - TIMEOUT"
                if c:
                    line += c
                    if line[-lenterm:] == terminator:
                        break
                    if size is not None and len(line) >= size:
                        break
            self.log(str(datetime.now()) + ' '*3+"Receive:'{0}' \n".format(line.strip()))
            return line
        else:
            return "ERROR-TCP_DISCONNECT"





class kRpc(object):
    '''
    this is the base driver for rpc_client
    user JSONRPCProtocol

    :param1     :port 6100  :int            it's a port for remote
    :param2     :ip_addr    :str            this param is the remote server ip address  default is '127.0.0.1'
    :param3     :publisher  :ZmqPublisher   publish info to which subcriber
    :example:
            client = kRpc(6100,'127.0.0.1',publisher=NoOpPublisher)
            reply = client.call('delay',1000,timeout=1500)
            print reply
            reply = client.call('vendor_id')
            print reply
            reply = client.call('add',10,100)
            print reply
    '''


    def __init__(self, endpoint, publisher=None):
        transport = endpoint
        assert isinstance(transport,dict)
        assert 'requester' in transport
        assert 'receiver' in transport
        self._rpc_proxy = RPCClientWrapper(endpoint, publisher)
        self.publisher = publisher

    def _get_proxy(self, prefix=''):
        return self._rpc_proxy.get_proxy(prefix)

    def call(self, method, *args, **kwargs):
        '''
        this function is the wapper of rpc call
        :param method: string                   this is the function name of remote server
        :param args:   (string,int,float....)   it's the params of remote function
        :param kwargs: (string,int)             timeout or unit in this dict
        :return: result
        '''
        if self.publisher:
            self.publisher.publish(
                str(datetime.now()) + ' ' * 3 + 'method:{} args:{} kwargs:{} \n'.format(method, args, kwargs))
        # response = getattr(self._get_proxy(), method)(*args, **kwargs)
            # response = float(0.001)
        response = getattr(self._rpc_proxy, method)(*args, **kwargs)
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + 'recevice:{}'.format(response))
        if response is None:
            raise JSONRPCServerError('Timed out waiting for response from test engine in test: ' + str(method))
        return response


class kTelnet(object):

    def __init__(self, endpoint, publisher=None):
        assert isinstance(endpoint, dict)
        ip = endpoint.get("ip")
        port = endpoint.get("port")
        self.endStr = endpoint.get("endstr", '\n')
        self.terminator = endpoint.get("terminator", ":-) ")
        try:
            self.telnet = telnetlib.Telnet(ip, port)
        except Exception as e:
            self.telnet = None
        self.publisher = publisher

    def init(self, site=0, drivers=None, te_publisher=None):
        pass

    def log(self, msg):
        print msg
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' '*3+'{}'.format(msg))

    def close(self):
        self.telnet.close()
        return True


    def read_until(self,terminator = None,timeout = 1000):
        result = ''
        tm = timeout / 1000.0
        if self.telnet:
            if not terminator:
                st = self.terminator
            else:
                st = terminator
            result = self.telnet.read_until(st, tm)
            self.log("recevice:{}".format(result))
        return result

    def send(self, cmd):
        if self.telnet:
            if self.endStr not in cmd:
                str_transfer = cmd + self.endStr
            else:
                str_transfer = cmd
            self.telnet.write(str(str_transfer))
            self.log("send:{}".format(cmd))


    def send_read(self,cmd, terminator = None,timeout = 1000):
        tm = timeout/1000

        if self.endStr not in cmd:
            str_transfer = cmd + self.endStr
        else:
            str_transfer = cmd
        self.telnet.write(str(str_transfer))
        self.log("send:{}".format(str_transfer))
        if not terminator:
            st = self.terminator
        else:
            st = terminator
        reslut = self.telnet.read_until(st, tm)
        self.log("recevice:{}".format(reslut))
        return reslut

    def set_terminator(self, terminator):
        self.terminator = str(terminator)
