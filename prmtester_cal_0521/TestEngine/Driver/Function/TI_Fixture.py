import time
from Common.prmdriver import KSerial
from Configure.driver_config import FIXTURE_SERIAL_PORT
from ..Function.TI_Common import RootFunction
from TI_Define import *

class TI_Fixture(RootFunction):
    def __init__(self, driver=None):
        super(TI_Fixture, self).__init__(driver)
        self.obj_mix = None
        self.obj_fix = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_fix = KSerial({"port": FIXTURE_SERIAL_PORT})

    def _query(self, command, timeout=1000):
        try:
            self.obj_fix.open()
            self.obj_fix.send(command + "\r\n")
            time.sleep(0.1)
            resp = self.obj_fix.read_line(timeout)
            self.obj_fix.close()
            return resp
        except Exception as e:
            print e

    @handle_response
    def reset_fixture(self, *args, **kwargs):
        res = self._query("S:RESET")
        if "OK" in res:
            return "--PASS--"
        else:
            return "--FAIL--"
