from datetime import datetime
from pyvisa import ResourceManager


class Visa(object):

    def __init__(self, port_name, publisher = None):
        self.__port_name = port_name
        self.publisher = publisher
        self.__rm = None
        self.__session = None
        self.__isOpen = False

    def open(self):
        # assert self.__port_name in self.list_resources()
        try:
            self.__rm = ResourceManager()
            self.__session = self.__rm.open_resource(self.__port_name)
            self.__session.read_termination = "\r"
            #self.set_termination("\r\n")
            self.__isOpen = True
            print ("open success")
        except Exception as e:
            raise e

    def close(self):
        try:
            if self.__session:
                self.__session.close()
                del self.__session
                del self.__rm
                print ("close success")
            self.__isOpen = False
        except Exception as e:
            raise e

    def log(self, msg):
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + msg)

    @classmethod
    def list_resources(self):
        rm = ResourceManager()
        return rm.list_resources()

    def send(self, cmd):
        if self.__isOpen:
            self.__session.write(cmd)
            self.log("send: {}".format(cmd))
            return True
        else:
            self.log("{} Is Not Open".format(self.__port_name))
            return False

    def read(self):
        if self.__isOpen:
            reply = self.__session.read()
            self.log("recv: {}".format(reply))
            return reply
        else:
            self.log("{} Is Not Open".format(self.__port_name))
            return False


    def query(self, cmd):
        if self.__isOpen:
            self.log("send: {}".format(cmd))
            reply = self.__session.query(cmd)
            self.log("recv: {}".format(reply))
            return reply
        else:
            self.log("{} Is Not Open".format(self.__port_name))
            return False

    def set_termination(self, termination="\r\n"):
        if self.__session:
            self.__session.read_termination = termination
            return True
        else:
            return False



class KeithleyDriver(Visa):

    def __init__(self, port_name, publisher=None):
        super(KeithleyDriver, self).__init__(port_name, publisher)
        self.open()

    def get_local_info(self):
        """
        KEITHLEY INSTRUMENTS,MODEL nnnn,xxxxxxx,yyyyy
        nnnn = the model number
        xxxxxxx = the serial number
        yyyyy = the firmware revision level
        :return:
        """
        try:
            info = dict()
            reply = str(self.query("*IDN?"))
            reply = reply.strip()
            vendor, model, sn, fw_v = reply.split(",")
            info.setdefault("vendor code", vendor)
            info.setdefault("model number", model)
            info.setdefault("serial number", sn)
            info.setdefault("fw version", fw_v)
            return info
        except Exception as e:
            return e

    def reset(self):
        """
        Returns the instrument to default settings
        :return:
        """
        self.send("*RST")
        return True



