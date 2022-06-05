import telnetlib
from datetime import datetime
import time
import re

class DockChannel(object):
    def __init__(self, publisher=None):
        self.publisher = publisher
        self.telnet = None
        self.endofstr = "\r"
        self.terminator = "] :-)"

    def init(self):
        pass

    def log(self, title, data):
        if self.publisher:
            self.publisher.publish('[' + str(datetime.now()) + ']-[{}]:{}\r\n'.format(title, data))

    def dc_open(self, ip, port):
        try:
            self.telnet = telnetlib.Telnet(ip, port)
            self.log("OPEN", "open dock channel {}:{}".format(ip, port))
        except Exception as e:
            self.log("OPEN", "open dock channel failed:{}".format(e.message))
            self.telnet = None

    def dc_close(self):
        self.log("CLOSE", "close dock channel {}:{}".format(self.telnet.host, self.telnet.port))
        self.telnet.close()
        return True

    def dc_set_endofstr(self, endofstr):
        self.log("SET", "set end_of_string = {}".format(endofstr))
        self.endofstr = endofstr

    def dc_send(self, cmd):
        if self.telnet:
            if self.endofstr not in cmd:
                str_transfer = cmd + self.endofstr
            else:
                str_transfer = cmd
            self.telnet.write(str(str_transfer))
            # if 'csoc --on' in cmd:
            #     print '1' * 50
            #     self.telnet.write(str('csoc --on\r').encode('utf-8'))
            # else:
            #     self.telnet.write(str(str_transfer))


    def dc_read(self):
        ret = ''
        if self.telnet:
            ret = self.telnet.read_until(self.terminator, 0.01)
        return ret

    def dc_query(self, cmd, terminator="^-^:)", timeout=5.0):
        ret = None
        if self.telnet:
            self.dc_send(cmd)
            ret = self.telnet.read_until(terminator, timeout)
        return ret


if __name__ == "__main__":
    dc = DockChannel()
    dc.dc_open('169.254.1.34', 31337)
    dc.dc_send('csoc --on\n')
    time.sleep(1)
    print dc.dc_read()


