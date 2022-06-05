from ..Function.TI_Common import RootFunction
import time
from TI_Define import *
from mix.lynx.rpc.profile_client import RPCClientWrapper
from ..Mapping.io_table import IOTable


class TI_PSU(RootFunction):
    def __init__(self, driver=None):
        super(TI_PSU, self).__init__(driver)
        self.obj_mix = None
        self.obj_pgpsu = None
        self.client = None
        self.io_table = IOTable()

    def init(self):
        self.site = self.driver.get('site')
        self.obj_mix = self.get_method("mix")
        self.obj_pgpsu = self.obj_mix.objsgpsu

    @handle_response
    def psu_power_on(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        voltage = float(args[0])
        current_limit = float(args[1])
        # time.sleep(2*self.site)
        ret = self.obj_pgpsu.power_output(voltage)
        ret = self.obj_pgpsu.current_limit(current_limit)
        ret = self.obj_pgpsu.power_control('on')
        time.sleep(0.02)
        if ret.upper() == 'DONE':
            return "--PASS--"
        else:
            return "--FAIL--"

    @handle_response
    def psu_power_off(self, *args, **kwargs):
        ret = self.obj_pgpsu.power_output(1)
        ret = self.obj_pgpsu.current_limit(10)
        ret = self.obj_pgpsu.power_control('off')
        time.sleep(0.02)
        if ret.upper() == 'DONE':
            return "--PASS--"
        else:
            return "--FAIL--"

    @handle_response
    def cal_psu_power_on(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        slots_map = {"1": "33", "2": "32", "3": "35", "4": "34"}
        slot_id = str(self.site + 1)
        lookup_psu_ip = slots_map.get(slot_id)
        endpoint = {'requester': 'tcp://169.254.1.{}:7801'.format(lookup_psu_ip), 'receiver': 'tcp://169.254.1.{}:17801'.format(lookup_psu_ip)}
        self.obj_mix.log_hw("endpoint", "[endpoint]={}".format(endpoint))
        self.client = RPCClientWrapper(endpoint)
        io_dict = self.io_table.get_by_netname("POWER_SUPPLY_PATH", "PSU_TO_PPVBUS_HMD_INPUT", "HWIO_RELAY_TABLE")
        result = self.client.relay.set_io_switch(io_dict.get("IO"))
        self.obj_mix.log_hw("set_io_switch", "[set_io_switch]={}".format(result))
        
        voltage = float(args[0])
        current_limit = float(args[1])
        ret = self.client.psu_board.power_output(voltage)
        ret = self.client.psu_board.set_current_limit(current_limit)
        ret = self.client.psu_board.power_control('on')
        time.sleep(0.02)
        if ret.upper() == 'DONE':
            self.obj_mix.log_hw("cal_psu_power_on", "[ret]={}".format(ret))
            return "--PASS--"
        else:
            return "--FAIL--"

    @handle_response
    def cal_psu_power_off(self, *args, **kwargs):
        ret = self.client.psu_board.power_output(1)
        ret = self.client.psu_board.set_current_limit(10)
        ret = self.client.psu_board.power_control('off')
        time.sleep(0.02)
        if ret.upper() == 'DONE':
            self.obj_mix.log_hw("cal_psu_power_off", "[ret]={}".format(ret))
            return "--PASS--"
        else:
            return "--FAIL--"


    @handle_response
    def psu_power_slower_on(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        all_str = str(args[0])
        temp_str = all_str.split("_")
        start_voltage = float(temp_str[0])
        stop_voltage = float(temp_str[1])
        current_limit = float(args[1])
        # time.sleep(2*self.site)
        ret = self.obj_pgpsu.current_limit(current_limit)
        ret = self.obj_pgpsu.power_output(start_voltage)
        for i in range(4):
            time.sleep(0.001)
            start_voltage = start_voltage + 3000
            if start_voltage > stop_voltage:
                ret = self.obj_pgpsu.power_output(stop_voltage)
                break
            ret = self.obj_pgpsu.power_output(start_voltage)
        
        if ret.upper() == 'DONE':
            return "--PASS--"
        else:
            return "--FAIL--"
