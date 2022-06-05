from ..Function.TI_Common import RootFunction
from ..Device.mix_device.sg.mixdatalogger import datalogger
from TI_Define import *
import time
from ..Utility.utility import Unit
from ..Device.mix_device.cal_table import DATALOGGER_CAL


class TI_Datalogger(RootFunction):
    def __init__(self, rpc_endpoint, stream_endpoint, driver=None, publisher= None):
        super(TI_Datalogger, self).__init__(driver)
        self.obj_mix = None
        self.obj_datalogger = None
        self.rpc_endpoint = rpc_endpoint
        self.stream_endpoint = stream_endpoint
        self.publisher = publisher
        self.power_data = []

    def __del__(self):
        self.obj_datalogger.close()

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_datalogger = datalogger(self.obj_mix.client, self.rpc_endpoint, self.stream_endpoint, self.publisher)
        self.obj_datalogger.open()
        self.obj_wibEEprom = self.obj_mix.objwibEEprom
        self.set_cal_data()

    @handle_response
    def start(self, *args, **kwargs):
        ret = self.obj_datalogger.start()
        if ret:
            return "--PASS--"
        else:
            return "--FAIL--"

    @handle_response
    def stop(self, *args, **kwargs):
        self.obj_datalogger.stop()
        return "--PASS--"

    @handle_response
    def read_dagger_sn(self, *args, **kwargs):
        try:
            ret = self.obj_datalogger.read_serial_number()
            return ret
        except Exception as e:
            self.obj_mix.log_hw("read_dagger_sn", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def get_power_voltage(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        duration_ms = int(args[0])
        sample_rate = int(args[1])
        self.power_data = [0,0]
        try:
            ret = self.obj_datalogger.start_datalogger(sample_rate=sample_rate)
            self.obj_datalogger.set_datalogger_flag(True)
            time.sleep(1)
            ret_v, ret_c = self.obj_datalogger.get_data(duration_ms, sample_rate)
            self.power_data = [ret_v, ret_c] 
            self.obj_datalogger.set_datalogger_flag(False)
            self.obj_datalogger.stop()
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(ret_v, "mV", str(unit))
            return ret
        except Exception as e:
            self.obj_datalogger.set_datalogger_flag(False)
            self.obj_mix.log_hw("get_power_consumption", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def get_power_current(self, *args, **kwargs):
        try:
            ret_c = self.power_data[1]
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(ret_c, "mA", str(unit))
            return ret
        except Exception as e:
            self.obj_mix.log_hw("get_power_current", "[result]={}".format(e))
            return "--FAIL--"

    def get_power_voltage_cal(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        duration_ms = int(args[0])
        sample_rate = int(args[1])
        self.power_data = [0,0]
        try:
            ret = self.obj_datalogger.start_datalogger(sample_rate=sample_rate)
            self.obj_datalogger.set_datalogger_flag(True)
            time.sleep(1)
            ret_v, ret_c = self.obj_datalogger.get_data(duration_ms, sample_rate)
            self.power_data = [ret_v, ret_c] 
            self.obj_datalogger.set_datalogger_flag(False)
            self.obj_datalogger.stop()
            return ret
        except Exception as e:
            self.obj_datalogger.set_datalogger_flag(False)
            self.obj_mix.log_hw("get_power_consumption", "[result]={}".format(e))
            return "--FAIL--"

    def get_power_current_cal(self):
        try:
            ret = self.power_data[1]
            return ret
        except Exception as e:
            self.obj_mix.log_hw("get_power_current", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def get_power_consumption(self, *args, **kwargs):
        try:
            ret = self.power_data[0] * self.power_data[1] / 1000.0
            return ret
        except Exception as e:
            self.obj_mix.log_hw("get_power_consumption", "[result]={}".format(e))
            return "--FAIL--"


    def set_cal_data(self):
        channel_name = ["PPVBUS_SYS", 
                        "PPVBUS_HMD_INPUT_CONN",
                        "CURRENT_PPVBUS_SYS",
                        "CURRENT_PPVBUS_HMD_INPUT_CONN"]
        cal_data = []
        try:
            for i in range(4):
                index = DATALOGGER_CAL.get(channel_name[i])
                if index:
                    self.obj_mix.log_hw("channel", "[result]={}".format(channel_name))
                    cal_info = self.obj_wibEEprom.read_calibration_cell(index)
                    cal_data.append(cal_info)
            self.obj_datalogger.set_cal_data(cal_data)
        except Exception as e:
            self.obj_mix.log_hw("set_cal_data", "[result]={}".format(e))
