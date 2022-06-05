import serial
from datetime import datetime
import time


class SerialPort(object):
    def __init__(self, PortName, BaudRate=115200, TimeOut=5, publisher=None):
        self.publisher = publisher
        self.portname = PortName
        self.baudrate = BaudRate
        self.timeout = TimeOut
        self.port = None
        time.sleep(0.1)
        self.open()

    def init(self, site=0, drivers=None, te_publisher=None):
        pass

    def open(self):
        """
        no need open cause init Serial means open
        didn't set timeout means block
        :return: True
        """
        self.close()
        try:
            self.port = serial.Serial(self.portname, self.baudrate)
            if self.publisher:
                self.publisher.publish(str(datetime.now()) + ' ' * 3 + "Open Serial Port SUCCESS [{}]".format(self.portname))
        except Exception as e:
            if self.publisher:
                self.publisher.publish(str(datetime.now()) + ' ' * 3 + "Open Serial Port FAIL [{}]".format(self.portname))
            return False
            # raise RuntimeError("Open serial port error: %s", self.port)
        return True

    def log(self, td, msg):
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + "{0}: {1}\n".format(td,msg))

    def close(self):
        if self.port:
            if self.port.isOpen():
                self.port.flush()
                self.port.close()
                del self.port
                self.port = None
                if self.publisher:
                    self.publisher.publish(str(datetime.now()) + ' ' * 3 + "Close Serial Port SUCCESS [{}]".format(self.portname))
        return True

    def send(self, cmd):
        if self.port.isOpen():
            self.port.flushInput()
            self.port.flushOutput()
            # print datetime.datetime.now().strftime("\n%Y-%m-%d %H:%M:%S.%f"), '    ', cmd,
            # self.log('send_command',cmd)
            # print str(datetime.now()) + ' ' * 3 + "send_command: {}\n".format(cmd)
            if self.publisher:
                self.publisher.publish(str(datetime.now()) + ' ' * 3 + "send_command: {}\n".format(cmd))
            return self.port.write(cmd + '\n')
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self.port.name)

    def sendcmd_bybyte(self, cmd, interval=0.030):
        if self.port.isOpen():
            self.port.flushInput()
            self.port.flushOutput()
            # self.log('send_command',cmd)
            if self.publisher:
                self.publisher.publish(str(datetime.now()) + ' ' * 3 + "send_command: {}\n".format(cmd))
            # print datetime.datetime.now().strftime("\n%Y-%m-%d %H:%M:%S.%f"), '    ', cmd,
            for sc in cmd:
                self.port.write(sc)
                time.sleep(interval)
            self.port.write("\n")
        else:
            raise RuntimeError("Cmd send error, port not open: %s", self.port.name)

    def readResponse(self, terminator=']', nextline_check=True):
        return self.read_until(terminator, self.timeout, nextline_check)
        # self.log('recv_command',res)

        # print datetime.datetime.now().strftime("\n%Y-%m-%d %H:%M:%S.%f"), '    ', res,
        # if terminator in res:
        #     return res
        # else:
        #     raise RuntimeError("Error: timeout %s", res)

    def send_read(self, cmd, terminator=']', timeout=3000,nextline_check=False):
        self.read_existing()
        self.send(cmd)
        # return self.read_existing()
        return self.read_until(terminator, timeout, nextline_check)

    def read_until(self, terminator, timeout, nextline_check=False):
        """\
        Read until a termination sequence is found ('\n' by default), the size
        is exceeded or until timeout occurs.
        """
        timeout_happen = False
        line = ""
        time_out = timeout/1000.0
        begin = time.time()
        try:
            while True:
                c = self.port.read(self.port.inWaiting())
                if c:
                    line += c
                    # print "serial port: {};terminator: {}".format(line,terminator)
                    if line.rfind(terminator) > 0:
                        if nextline_check:
                            # ensure after terminator: > is located at end of response, ]
                            # if line.split('\n')[-3].split(terminator)[-1] == '\r':
                            break
                        else:
                            break

                    # time.sleep(0.05)
                if time.time() - begin > time_out:
                # if self.publisher:
                #     self.publisher.publish(str(datetime.now()) + ' ' * 3 + "time_out: {}s\n".format(time.time() - begin))
                    timeout_happen = True
                    break
        except Exception as e:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + "Exception_fail_recv_result: {}\n".format(e))
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + "fail_recv_result: {}\n".format(line))
            return '--FAIL--'
        # print "Port: {};received: {}".format(self.portname, line)
        # if timeout_happen:
        #     raise RuntimeError("Error: timeout %s", line)
        if self.publisher:
            if timeout_happen:
                # self.publisher.publish(str(datetime.now()) + ' ' * 3 + "Timeout happened\n")
                self.publisher.publish(str(datetime.now()) + ' ' * 3 + "TIMEOUT recv_result: {}\n".format(line))
            else:
                self.publisher.publish(str(datetime.now()) + ' ' * 3 + "recv_result: {}\n".format(line))
        return line if not timeout_happen else None

    def read_existing(self):
        res = ""
        start_time = time.time()
        while self.port.inWaiting() > 0:
            if time.time() - start_time > 3:
                break
            serialstring = self.port.read(self.port.inWaiting())
            res = res + serialstring
            time.sleep(0.5)
            # self.port.reset_input_buffer()
            # self.port.reset_output_buffer()
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + "read_existing: {}\n".format(res))
        return res

    def setTimeout(self, timeOut=6):
        self.port.timeout = timeOut


if __name__ == "__main__":
    start_time = time.time()
    s = SerialPort("/dev/cu.usbserial-PRMDUT01")
    print s.open()
    print s.send('[SV]')
    print s.read_until('>', 6000)
    print time.time()-start_time

