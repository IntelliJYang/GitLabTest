import time
from TI_Define import *
from abc import abstractmethod, ABCMeta
from Configure.constant import TSID
from Common.BBase import GetSN
import pypudding

class RootFunction(object):
    __metaclass__ = ABCMeta
    def __init__(self, driver=None):
        self.driver = driver

    @abstractmethod
    def init(self):
        pass

    def get_method(self, name):
        return self.driver.get(name)

    def get_all_func(self):
        return self.driver.get("all_function")


class CallBack(RootFunction):
    def __init__(self, driver=None):
        super(CallBack, self).__init__(driver)
        self.obj_mix = None

    def init(self):
        self.obj_mix = self.driver.get("mix")

    @handle_response
    def start_test(self, *args, **kwargs):
        from datetime import datetime, timedelta
        ts = datetime.strftime(datetime.now() + timedelta(seconds=-1), '%m-%d-%H-%M-%S')
        self.obj_mix.set_logging_time(ts)
        return ""

    @handle_response
    def end_test(self, *args, **kwargs):
        self.obj_mix.reset_mix()
        ret_str = ""
        ti_dut = self.driver.get("ti_dut")
        if ti_dut.isUseDockChannel:
            if ti_dut.obj_dc_31336:
                ti_dut.obj_dc_31336.dc_close()
            if ti_dut.obj_dc_31337:
                ti_dut.obj_dc_31337.dc_close()
        ti_datalogger = self.driver.get("ti_datalogger")
        ti_datalogger.obj_datalogger.stop()
        ti_digitizer = self.driver.get("ti_digitizer")
        if ti_digitizer.is_running:
            ti_digitizer.obj_digitizer.disable()
        if ti_digitizer and ti_digitizer.log_paths and len(ti_digitizer.log_paths) > 0:
            ret_str = ','.join(ti_digitizer.log_paths)
            ti_digitizer.log_paths = []
        return ret_str

    @handle_response
    def sequencerRigister(self, *args, **kwargs):
        return "--PASS--"


class General(RootFunction):

    def __init__(self, driver=None):
        super(General, self).__init__(driver)
        self.site = 0

    def init(self):
        self.site = self.driver.get("site")

    @handle_response
    def skip(self, *args, **kwargs):
        return "--SKIP--"

    @handle_response
    def vendor_id(self, *args, **kwargs):
        return "0x01:PRM"

    @handle_response
    def station_name(self, *args, **kwargs):
        gh_info = pypudding.IPGHStation()
        product = gh_info[pypudding.IP_PRODUCT]
        station_type = gh_info[pypudding.IP_STATION_TYPE]
        return "{}_{}".format(product, station_type)

    @handle_response
    def fixture_id(self, *args, **kwargs):
        return str(TSID)

    @handle_response
    def slot_id(self, *args, **kwargs):
        return "SLOT{}".format(self.site + 1)

    @handle_response
    def delay(self, *args, **kwargs):
        if len(args) > 0:
            time.sleep(float(args[0]) / 1000)
        return '--PASS--'

    @handle_response
    def calculate(self, *args, **kwargs):
        if len(args) > 0:
            try:
                str = args[0]
                ret_value = eval(str)
                return ret_value
            except Exception as e:
                print(e)

    @handle_response
    def scansn(self, *args, **kwargs):
        return GetSN.get_mlbsn(self.site).strip()
