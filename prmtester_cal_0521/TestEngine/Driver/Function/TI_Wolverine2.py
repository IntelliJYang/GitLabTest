from ..Function.TI_Common import RootFunction
from ..Utility.utility import Unit
import time
from datetime import datetime
from TI_Define import *
from ..Device.mix_device.cal_table import POWER_RAIL_CAL, ARRAY_RELAY_CAL, RIGEL_CAL
from threading import Thread
import numpy as np

class TI_Wolverine2(RootFunction):
    def __init__(self, driver=None):
        super(TI_Wolverine2, self).__init__(driver)
        self.obj_mix = None
        self.obj_w2 = None
        self.obj_ti_relay = None
        self.rigel_data = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_ti_relay = self.driver.get("ti_relay")
        self.obj_w2 = self.obj_mix.objsgw2
        self.obj_ti_adgrelay = self.driver.get("ti_adgrelay")
        self.obj_wibEEprom = self.obj_mix.objwibEEprom
        self.obj_freq = self.obj_mix.objfreql
        self.rigel_data = []
        self.obj_ti_dut = self.driver.get("ti_dut")

    @handle_response
    def measure_voltage_count(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        ch_type = str(args[0])
        count = int(args[1])
        sample_rate = count
        # sample_rate = 125000

        if ch_type not in ['5V', '5VCH2']:
            return PARA_ERROR
        unit = kwargs.get("unit")
        val = self._measure_voltage(ch_type, unit, 100, sample_rate)
        if val:
            return val
        else:
            return "--FAIL--Measure fail"


    @handle_response
    def measure_voltage(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        ch_type = str(args[0])
        if ch_type not in ['5V', '5VCH2']:
            return PARA_ERROR
        unit = kwargs.get("unit")
        val = self._measure_voltage(ch_type, unit)
        if val:
            return val
        else:
            return "--FAIL--Measure fail"

    def _measure_voltage(self, ch_type, unit, count=10, sample_rate=1000):
        try:
            ret = self.obj_w2.set_measure_path(ch_type)
            time.sleep(0.005)
            self.obj_mix.log_hw("measure_voltage", "[rail]={}-{} [ch]={}".format(self.obj_ti_relay.net, self.obj_ti_relay.sub_net, ch_type))
            if ret.upper() == 'DONE':
                val = self.obj_w2.read_measure_value(sample_rate, count)
                # all channel has 5.99/4.99 div for N301 MLB FCT

                if "_I_P" in self.obj_ti_relay.sub_net:
                    real_val = (5.99 / 4.99) * Unit.convert_unit(val, "mA", str(unit))
                else:
                    real_val = (5.99 / 4.99) * Unit.convert_unit(val, "mV", str(unit))
                # all POWER_RAIL_PATH group with '_DIV' signals has 4x div for N301 MLB FCT
                if self.obj_ti_relay.net == "POWER_RAIL_PATH":
                    if self.obj_ti_relay.sub_net.endswith('_DIV'):
                        real_val = real_val * 4
                        real_val = real_val * 1.009  # after div, has 1.009 gain
                    elif self.obj_ti_relay.sub_net == "PP8V0_IPD_DRV":
                        real_val = real_val * 2

                if self.obj_ti_relay.sub_net == "GPIO_ARRAY_Y_7_TO_DMM":
                    if self.obj_ti_adgrelay.net == "GPIO_ARRAY_TO_DMM_TABLE":
                        index = ARRAY_RELAY_CAL.get(self.obj_ti_adgrelay.sub_net)
                    else:
                        index = ARRAY_RELAY_CAL.get(self.obj_ti_adgrelay.net)
                else:
                    index = POWER_RAIL_CAL.get(self.obj_ti_relay.sub_net)

                real_val = self.obj_wibEEprom.do_system_cal(index, real_val)

                self.obj_mix.log_hw("measure_voltage", "[result]={} {}".format(real_val, unit))
                return real_val
            else:
                return None
        except Exception as e:
            self.obj_mix.log_hw("[measure_voltage]", "[result]={}".format(e))
            return None

    @handle_response
    def wait_voltage_drop(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        net = "POWER_RAIL_PATH"
        ch_type = "5V"
        sub_net = str(args[0])
        threshold = float(args[1])
        tmp_result = self.obj_ti_relay._relay_switch(net, sub_net)
        if tmp_result == "--PASS--":
            unit = kwargs.get("unit")
            timeout = kwargs.get("timeout")
            date_start = datetime.now()
            while (datetime.now() - date_start).total_seconds() < (timeout/1000.0 - 5.0):
                val = self._measure_voltage(ch_type, unit, count=2)
                print "wait_voltage: {}".format(val)
                if val <= threshold:
                    return "last_voltage={}".format(val)
                time.sleep(0.01)
            return "--FAIL--Timeout and last_voltage={}".format(val)
        else:
            return tmp_result

    @handle_response
    def wait_voltage_up(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        net = "POWER_RAIL_PATH"
        ch_type = "5V"
        date_start = datetime.now()
        sub_net = str(args[0])
        threshold = float(args[1])
        tmp_result = self.obj_ti_relay._relay_switch(net, sub_net)
        if tmp_result == "--PASS--":
            unit = kwargs.get("unit")
            timeout = kwargs.get("timeout")
            # date_start = datetime.now()
            while (datetime.now() - date_start).total_seconds() < 1.5:
                val = self._measure_voltage(ch_type, unit)
                print "wait_voltage: {}".format(val)
                if val >= threshold:
                    return "last_voltage={}".format(val)
                time.sleep(0.1)
            return "--FAIL--Timeout and last_voltage={}".format(val)
        else:
            return tmp_result


    @handle_response
    def read_dmm_sn(self, *args, **kwargs):
        try:
            ret = self.obj_w2.read_serial_number()
            return ret
        except Exception as e:
            self.obj_mix.log_hw("read_dmm_sn", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def clear_toffmin_data(self, *args, **kwargs):
        '''
        Args:
            *args:
            **kwargs:

        Returns:
        '''
        self.obj_mix.log_hw("[clear_toffmin_clksafety]", "[result]={}".format("True"))
        self.rigel_data = []
        return "--PASS--"

    @handle_response
    def get_toffmin_clksafety(self, *args, **kwargs):
        '''
        Args:
            *args:
            **kwargs:

        Returns:
        '''
        value = 0
        if len(self.rigel_data) > 0:
            value = np.min(self.rigel_data)
        self.obj_mix.log_hw("[get_toffmin_clksafety]", "[result]={}".format(self.rigel_data))
        self.rigel_data = []
        return value

    @handle_response
    def get_duty_sample(self, *args, **kwargs):
        '''
        Args:
            *args:
            **kwargs:

        Returns:
        '''
        if len(args) != 1:
            return MISSING_ENOUGH_PARA

        mode = str(args[0])
        unit = kwargs.get("unit")

        duration = 200
        try:
            result = self.w2_multi_sample_no_calulate(duration)
            # max_data = np.max(result)
            # min_data = np.min(result)
            # threshold = (max_data + min_data)/2
            # self.obj_mix.log_hw("[get_duty_sample]", "[result]=max:{} min:{} threshold:{}".format(max_data, min_data, threshold))
            threshold = 100
            t_on, t_off = self.calculate_duty_on_off(result, threshold)

            self.obj_mix.log_hw("[get_duty_sample]", "[result]=on:{} off:{}".format(t_on, t_off))

            value = 0
            if len(t_on)>0 and len(t_off)>0:
                if mode == "TON":
                    value = np.max(t_on) / 125.0
                elif mode == "TOFF":
                    value = np.min(t_off) / 125.0
            self.rigel_data.append(value)
        except Exception as e:
            self.obj_mix.log_hw("[get_duty_sample]", "[result]={}".format(e))
            return "--FAIL--"
        return value


    @handle_response
    def get_ton_max_sample(self, *args, **kwargs):
        '''
        Args:
            *args:
            **kwargs:

        Returns:
        '''
        if len(args) != 2:
            return MISSING_ENOUGH_PARA

        rigel_channel = str(args[0])
        rigel_mode = str(args[1])
        unit = kwargs.get("unit")

        duration = 100
        freq = 33.333
        duty = 19.9998
        channel = "2"
        try:
            result = self.w2_multi_sample_no_calulate(duration, freq, duty, rigel_channel)
            # max_data = np.max(result)
            # min_data = np.min(result)
            # threshold = (max_data + min_data)/2
            # self.obj_mix.log_hw("[get_ton_max_sample]", "[result]=max:{} min:{} threshold:{}".format(max_data, min_data, threshold))
            threshold = 100
            t_on, t_off = self.calculate_duty_on_off(result, threshold)

            self.obj_mix.log_hw("[get_ton_max_sample]", "[result]=on:{} off:{}".format(t_on, t_off))
            value = 0
            if len(t_on)>0 and len(t_off)>0:
                if rigel_mode == "TON":
                    value = np.max(t_on) / 125.0
                elif rigel_mode == "TOFF":
                    value = np.min(t_off) / 125.0

        except Exception as e:
            self.obj_mix.log_hw("[get_ton_max_sample]", "[result]={}".format(e))
            return "--FAIL--"
        return value

    @handle_response
    def w2_multi_sample(self, *args, **kwargs):
        '''
        Args:
            *args:
            **kwargs:

        Returns:
        '''
        if len(args) != 1:
            return MISSING_ENOUGH_PARA

        rigel_channel = str(args[0])
        unit = kwargs.get("unit")

        duration = 200
        result = self.w2_multi_sample_no_calulate(duration)

        threshold = 10
        currents = [i for i in result if i > threshold]
        # self.obj_mix.log_hw("[w2_multi_sample]", "[result]={}".format(currents))
        value = 0
        if currents:
            # value = np.max(currents)
            value = np.average(currents)
        # real_val = Unit.convert_unit(value, "mA", str(unit))
        real_val = value

        index = RIGEL_CAL.get(rigel_channel + "_I_MAX_MAP")
        # real_val = self.obj_wibEEprom.do_system_cal(index, real_val)
        # self.obj_mix.log_hw("w2_multi_sample", "[result]={} {}".format(real_val, unit))
        return real_val

    @handle_response
    def w2_multi_verify(self, *args, **kwargs):
        '''
        Args:
            *args:
            **kwargs:

        Returns:
        '''
        if len(args) != 2:
            return MISSING_ENOUGH_PARA

        rigel_channel = str(args[0])
        index = args[1]
        unit = kwargs.get("unit")

        duration = 200
        result = self.w2_multi_sample_no_calulate(duration)

        threshold = 10
        currents = [i for i in result if i > threshold]
        # self.obj_mix.log_hw("[w2_multi_sample]", "[result]={}".format(currents))
        value = 0
        if currents:
            # value = np.max(currents)
            value = np.average(currents)
        # real_val = Unit.convert_unit(value, "mA", str(unit))
        real_val = value

        # index = RIGEL_CAL.get(rigel_channel + "_I_MAX_MAP")
        real_val = self.obj_wibEEprom.do_system_cal(index, real_val)
        # self.obj_mix.log_hw("w2_multi_sample", "[result]={} {}".format(real_val, unit))
        return real_val

    def w2_multi_sample_no_calulate(self, duration, freq=None, duty=None, rigel_channel=None):
        '''
        :param args:
        :param kwargs:
        :return:
        '''
        # time.sleep(0.5)
        try:
            scope = "5V"
            sample_rate = 125000

            if "@" in scope:
                scope_only = 'a'
            print "datalogger open:", scope
            self.obj_w2.datalogger_open(scope, sample_rate)
            time.sleep(0.001)

            if freq:
                time.sleep(0.05)
                self.obj_mix.log_hw("pwm_out", "[result]={} {} {}".format(freq, duty, rigel_channel))
                if rigel_channel == "PDRV":
                    self.obj_freq.pwm_out_2(freq, duty, "square")
                else:
                    self.obj_freq.pwm_out_3(freq, duty, "square")

            raw_data = self.obj_w2.datalogger_read(duration)
            self.obj_w2.datalogger_close()
            result = self.obj_w2.parse_data(raw_data)
            result = result[10:]
            # self.obj_mix.log_hw("[measure_w2_multi_result]", "[result]={}".format(result))

            if False:
                pass
            else:
                # w2_cal_index = 8
                dmm_div = (4.99 / 5.99)
                gain_val = 50 
                res_val = 0.1
                gain = dmm_div * gain_val 
                currents = [float(i) / gain / res_val for i in result]

            # self.obj_mix.log_hw("[measure_w2_multi_sample]", "[result]={}: {}".format(scope, currents))

            return currents
        except Exception as e:
            self.obj_mix.log_hw("[measure_w2_multi_sample]", "[result]={}".format(e))
            return None

    def calculate_duty_on_off(self, data, thres):
        # thres = 100
        idx = 0
        indexes_hi = []
        indexes_lo = []
        start_hi = False
        start_lo = False
        ton = []
        toff = []
        for i in data:
            if i > thres:
                if not start_hi:
                    indexes_hi.append(idx)
                start_hi = True

                if start_lo:
                    indexes_lo.append(idx)
                    toff.append(indexes_lo[-1]-indexes_lo[-2])
                start_lo = False
            else:
                if start_hi:
                    indexes_hi.append(idx)
                    ton.append(indexes_hi[-1]-indexes_hi[-2])
                # indexes_lo.append(idx)
                start_hi = False

                if not start_lo:
                    indexes_lo.append(idx)
                start_lo = True
            idx = idx + 1

        if data[0] > thres:
            if len(ton) > 1:
                ton = ton[1:]
        else:
            if len(toff) > 1:
                toff = toff[1:]
                
        if len(indexes_lo) > 0 and len(toff) == 0:
            ton.append(0)
            toff.append(len(data) - indexes_lo[-1])
        if len(indexes_hi) > 0 and len(ton) == 0:
            toff.append(0)
            ton.append(len(data) - indexes_hi[-1])
        return ton, toff

    