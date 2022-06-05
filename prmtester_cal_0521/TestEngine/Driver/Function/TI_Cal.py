
from ..Function.TI_Common import RootFunction
from ..Mapping.io_table import IOTable
from TI_Define import *

import time
import numpy as np
from time import time, sleep
from oqc_instr import Inst_2400, Inst_33522A, Inst_Telnet, Inst_34461A, Inst_63600
from ..Device.mix_device.cal_table import POWER_RAIL_CAL, ARRAY_RELAY_CAL

from TI_DUT import *
from threading import Thread

# from ..Function.TI_Wolverine2 import measure_voltage

CAL_STEP = 5
LOOP_TIMES = 3
VERIFY_TIMES = 1
IS_WRITE_EEPROM = True

TOTAL_TEST_COUNT = 0
FAIL_TEST_COUNT = 0
TOLERANCE = True
cal_info_to_eeprom = list()
TOTAL_CAL = 0
CURRENT_CAL_INDEX = 0


csv_dir = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), 'cal_data.csv')

print os.path.abspath(csv_dir)
csv_f = open(csv_dir, 'a+')
csv_f.write('SET_raw, 34461A_raw, Fixture_raw, CAL, 34461A - CAL\r')
VERIFY = True
# VERIFY = False

def write_csv(data):
    # print data
    print '$' * 100
    print data
    csv_f.write(data + '\n')
    csv_f.flush()


class DMM:
    def __init__(self, clinet):
        self.client = clinet

    def measure(self, channel="voltage", mes_range=1.0, loop_times=1, nplc=10):
        assert channel in ('voltage', 'current')
        if channel == "voltage":
            # return self.client.read_voltage("DC", 10)
            return self.client.read_voltage_times("DC", mes_range, loop_times, nplc)
        else:
            # return self.client.read_current(curr_range)
            return self.client.read_current_times(mes_range, loop_times, nplc)

    def measure_current(self, mes_range, loop_times, nplc):
        '''
         only used for current measurement
        '''
        return self.client.read_current_multi_times(mes_range, loop_times, nplc)

    def measure_vol(self, channel, mes_range, loop_times, nplc):
        '''
        only for voltage measurement
        '''
        assert channel == "voltage"
        return self.client.read_voltage_multi_times("DC", mes_range, loop_times, nplc)

    def reset(self):
        self.client.reset()
        sleep(0.5)

    def write(self, current):
        return self.client.write(current)

    def loadon(self):
        return self.client.loadon()

    def loadoff(self):
        return self.client.loadoff()


class TI_Cal(RootFunction):

    def __init__(self, driver=None):
        super(TI_Cal, self).__init__(driver)
        self.obj2400 = None
        self.obj33522 = None
        self.objOQCBoard = None
        self.obj34461 = None
        self.obj63600 = None
        self.ti_digitizer = None

        self.io_table = IOTable()
        self.obj_mix = None
        self.obj_relay = None
        self.net = None
        self.sub_net = None

        self.gain = 0
        self.offset = 0
        self.datalogger_init = True
        self.cal_result = True
        # self.thread_flag = False
        # self.base_cal_gain = None
        # self.base_cal_offset = None
        self.x1_list = None
        self.y1_list = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_ti_relay = self.driver.get("ti_relay")
        self.obj_w2 = self.obj_mix.objsgw2
        self.obj_relay = self.obj_mix.objrelay
        self.obj_pgpsu = self.obj_mix.objsgpsu

        self.site = self.driver.get("site")
        self.obj_ti_psu = self.driver.get("ti_psu")
        self.obj_ti_wolverine2 = self.driver.get("ti_wolverine2")
        self.obj_ti_datalogger = self.driver.get("ti_datalogger")
        self.obj_ti_calmux = self.driver.get("ti_calmux")
        self.obj_wibEEprom = self.obj_mix.objwibEEprom
        self.ti_digitizer = self.driver.get("ti_digitizer")

        # self.obj2400 = Inst_2400()
        # self.obj33522 = Inst_33522A()
        # self.objOQCBoard = Inst_Telnet()
        self.obj34461 = Inst_34461A()
        self.obj63600 = Inst_63600()

        # try:
        #     self.obj34461.reset()
        # except Exception as e:
        #     print e

    @handle_response
    def get_cal_voltage_bk(self, *args, **kwargs):
        dmm = DMM(self.obj34461)

        index = str(args[0]).strip()
        para = args[1]
        arr_para = para.split('@')
        if len(arr_para) != 3:
            return "--FAIL--MISS-PARA"
        start_volt = int(arr_para[0])
        stop_volt = int(arr_para[1])
        cal_mode = str(arr_para[2])
        idx = POWER_RAIL_CAL.get(index)
        # start_volt = 0
        # stop_volt = 15000
        # step = 10

        voltage_list = self.calculate_voltage(start_volt, stop_volt, step=CAL_STEP)
        self.x1_list = []
        self.y1_list = []
        # self.obj_ti_psu.psu_power_on(1, 3000)
        for voltage in voltage_list:
            if voltage > 16000:
                return "--FAIL--voltage over range"
            self.obj_ti_psu.psu_power_on(voltage, 1000)
            sleep(0.3)
            # count = 10
            # v = self.obj_w2.read_measure_value(1000, count)
            # v = v * (5.99/4.99)
            # v = v * 4 * 1.009
            if cal_mode == "power_rail":
                v = self.obj_ti_wolverine2._measure_voltage("5V", "mV")
            elif cal_mode == "datalogger":
                v = self.obj_ti_datalogger._datalogger_measure("0", "10", "mV")
            if voltage > 10000:
                v1 = float(dmm.measure("voltage", 100, loop_times=3)) * 1000
            else:
                v1 = float(dmm.measure("voltage", 10, loop_times=3)) * 1000
            self.x1_list.append(v)
            self.y1_list.append(v1)
            self.obj_mix.log_hw("read_voltage", "[sg_w2]={} mV, [34465A]={} mV".format(v, v1))
        # self.obj_ti_psu.psu_power_off()

        gain, offset = np.polyfit(self.x1_list, self.y1_list, 1)
        self.gain, self.offset = gain, offset

        cal_info_to_eeprom.append([idx, gain, offset, stop_volt])
        self.obj_mix.log_hw("cal voltage output", "[{}:{}] gain={}, offset={}".format(start_volt, stop_volt, self.gain, self.offset))
        
        if not self.check_gain(gain, 0.99, 1.02):
            self.cal_result = False
            self.obj_mix.log_hw("read_voltage", "===============")
        if abs(offset) > 100:
            self.cal_result = False
            self.obj_mix.log_hw("read_voltage", "==========9999=====")
        return gain


    @handle_response
    def verify_cal_voltage(self, *args, **kwargs):
        global TOLERANCE
        dmm = DMM(self.obj34461)

        voltage = int(args[0])
        if voltage > 16000:
                return "--FAIL--voltage over range"
        # self.obj_pgpsu.power_output(voltage)
        self.obj_ti_psu.psu_power_on(voltage, 3000)
        sleep(0.1)
        v = self.obj_ti_wolverine2._measure_voltage("5V", "mV")

        if voltage > 10000:
            check_v = float(dmm.measure("voltage", 100)) * 1000
        else:
            check_v = float(dmm.measure("voltage", 10)) * 1000

        # self.obj_ti_psu.psu_power_off()

        flag =  self.check_tolerance(voltage, check_v, v, self.gain, self.offset)

        self.obj_mix.log_hw("verify voltage output", "Result: {}, Gain: {},  Offset: {}".format(flag, self.gain, self.offset))
        print "{}Result: {}, Gain: {},  Offset: {}\033[0m".format("\033[1;32m" if flag else "\033[1;33m\n",
                                                                  flag, self.gain,
                                                                  self.offset)
        if TOLERANCE:
            return v * self.gain + self.offset
        return TOLERANCE

    @handle_response
    def get_cal_voltage(self, *args, **kwargs):
        dmm = DMM(self.obj34461)

        index = str(args[0]).strip()
        para = args[1]
        arr_para = para.split('@')
        if len(arr_para) != 3:
            return "--FAIL--MISS-PARA"
        start_volt = int(arr_para[0])
        stop_volt = int(arr_para[1])
        cal_mode = str(arr_para[2])

        if cal_mode == "power_rail":
            idx = POWER_RAIL_CAL.get(index)
        elif cal_mode == "array_relay":
            idx = ARRAY_RELAY_CAL.get(index)
        elif cal_mode == "datalogger":
            idx = DATALOGGER_CAL.get(index)
        elif cal_mode == "digitizer":
            idx = PS_MUX_CAL.get(index)
        else:
            return "--FAIL--WRONG-PARA"
        # start_volt = 0
        # stop_volt = 15000
        # step = 10

        voltage_list = self.calculate_voltage(start_volt, stop_volt, step=CAL_STEP)
        self.x1_list = []
        self.y1_list = []
        # self.obj_ti_psu.psu_power_on(1, 3000)
        for voltage in voltage_list:
            if voltage > 16000:
                return "--FAIL--voltage over range"
            elif voltage >= 5000 and voltage < 16000:
                # self.obj_ti_calmux.calmux_switch("SET_VOLTAGE_PATH","PP_HIGHT_VOLTAGE_NO_UP_TO_PPVBUS")
                pass
            elif voltage >= 1700 and voltage < 5000:
                voltage = voltage * 3
                # self.obj_ti_calmux.calmux_switch("SET_VOLTAGE_PATH","PP_HIGHT_VOLTAGE_TO_PP_LOW_VOLGAGE_TO_PPOUT_1V7_5V5")
            elif voltage < 1700:
                voltage = voltage * 11
                # self.obj_ti_calmux.calmux_switch("SET_VOLTAGE_PATH","PP_HIGHT_VOLTAGE_TO_PP_LOW_VOLGAGE_TO_PPOUT_0V45_1V4")
            

            self.obj_ti_psu.psu_power_on(voltage, 3000)
            sleep(1)
            # count = 10
            # v = self.obj_w2.read_measure_value(1000, count)
            # v = v * (5.99/4.99) 
            # v = v * 4 * 1.009
            if cal_mode == "power_rail" or cal_mode == "array_relay":                
                v = self.obj_ti_wolverine2._measure_voltage("5V", "mV")
            elif cal_mode == "datalogger":
                v = self.obj_ti_datalogger._datalogger_measure(0, 10, "mV")
            elif cal_mode == "digitizer":
                v = self.obj_ti_digitizer._mux_measure(100, 3, "mV")

            # v1 = 1.568
            if voltage > 10000:
                v1 = float(dmm.measure("voltage", 100, loop_times=3)) * 1000
            else:
                v1 = float(dmm.measure("voltage", 10, loop_times=3)) * 1000

            self.x1_list.append(v)
            self.y1_list.append(v1)

            if cal_mode == "power_rail":
                self.obj_mix.log_hw("read_voltage", "[sg_w2]={} mV, [34465A]={} mV".format(v, v1))
            elif cal_mode == "datalogger":
                self.obj_mix.log_hw("read_voltage", "[datalogger]={} mV, [34465A]={} mV".format(v, v1))
            elif cal_mode == "digitizer":
                self.obj_mix.log_hw("read_voltage", "[digitizer]={} mV, [34465A]={} mV".format(v, v1))
        # self.obj_ti_psu.psu_power_off()

        gain, offset = np.polyfit(self.x1_list, self.y1_list, 1)
        self.gain, self.offset = gain, offset

        cal_info_to_eeprom.append([idx, gain, offset, stop_volt])
        self.obj_mix.log_hw("cal voltage output", "[{}:{}] gain={}, offset={}".format(start_volt, stop_volt, self.gain, self.offset))
        
        # if not self.check_gain(gain, 0.99, 1.02):
        #     self.cal_result = False
        #     self.obj_mix.log_hw("read_voltage", "===============")
        # if abs(offset) > 100:
        #     self.cal_result = False
        #     self.obj_mix.log_hw("read_voltage", "==========9999=====")
        return gain

    @handle_response
    def read_cal_offset(self, *args, **kwargs):
        return self.offset


    @handle_response
    def get_cal_rigel_current(self, *args, **kwargs):

        rigel_channel = str(args[0])
        idx = int(args[1])
        print "!" * 10
        current_list = [200, 300, 400]
        self.x1_list = []
        self.y1_list = []
        dmm = DMM(self.obj34461)
        # dmm.reset()
        dc = DMM(self.obj63600)
        dc.loadon()
        for current in current_list:
            print current
            # duration = current

            dc.write(current)

            time.sleep(1)
            print "%" * 10
            d_val1 = self.obj_ti_wolverine2.w2_multi_sample(rigel_channel)
            # time.sleep(1)

            f_val1 = float(dmm.measure("current", 1, loop_times=3)) * 1000
            self.obj_mix.log_hw("cal current output", "wolverine2={}, DMM={}".format(d_val1, f_val1))
            print "&" * 10
            print f_val1
            # time.sleep(30)
            self.x1_list.append(d_val1)
            self.y1_list.append(f_val1)
            print self.x1_list, self.y1_list
        dc.loadoff()

        gain, offset = np.polyfit(self.x1_list, self.y1_list, 1)
        self.gain, self.offset = gain, offset
        stop_volt = int(100)
        print "1" * 10
        print "gain, offset", gain, offset

        cal_info_to_eeprom.append([idx, gain, offset, stop_volt])
        self.obj_mix.log_hw("cal current output", "gain={}, offset={}".format(self.gain, self.offset))
        
        # if not self.check_gain(gain, 1.05, 1.09999):
        #     self.cal_result = False
        #     self.obj_mix.log_hw("read_voltage", "===============")
        # if abs(offset) > 100:
        #     self.cal_result = False
        #     self.obj_mix.log_hw("read_voltage", "========9999=====")

        return gain


    @handle_response
    def verify_rigel_current(self, *args, **kwargs):

        rigel_channel = str(args[0])
        # idx = int(args[1])
        para = args[1]
        arr_para = para.split('@')
        if len(arr_para) != 2:
            return "--FAIL--MISS-PARA"
        idx = int(arr_para[0])
        current = int(arr_para[1])
        
        # current_list = [200, 300, 400]
        
        dmm = DMM(self.obj34461)
        # dmm.reset()
        dc = DMM(self.obj63600)
        dc.write(current)

        time.sleep(1)
        # print "%" * 10
        d_val = self.obj_ti_wolverine2.w2_multi_verify(rigel_channel, idx)

        f_val = float(dmm.measure("current", 1, loop_times=3)) * 1000
        self.obj_mix.log_hw("current output", "d_val={}, f_val={}".format(d_val, f_val))
        current_val = float(f_val) - float(d_val)
        
        return current_val

    @handle_response
    def get_cal_beast_voltage(self, *args, **kwargs):

        #idx = int(args[1])
        voltage_list = [6000, 7000, 8000, 9000, 10000]
        self.x1_list = []
        self.y1_list = []
        dmm = DMM(self.obj34461)
        time.sleep(1)
        self.obj_mix.log_hw("cal beast voltage output", "voltage_list={}".format(str(voltage_list)))
        for voltage in voltage_list:
            print voltage
            # duration = current
            self.obj_ti_psu.psu_power_on(voltage, 5000)
            time.sleep(1)

            #dmm_voltage = float(dmm.measure("voltage", 10, loop_times=3)) * 1000
            # def measure(self, channel="voltage", mes_range=1.0, loop_times=1, nplc=10):
            # dmm_voltage = float(dmm.measure("voltage", mes_range=10, loop_times=1000, nplc=0.02)) * 1000
            dmm_average_voltage, dmm_voltage_list = dmm.measure_vol("voltage", mes_range=10, loop_times=1000, nplc=0.02)
            self.obj_mix.log_hw("cal beast voltage output", "len(dmm_voltage_list)={}, unit=V, dmm_voltage_list={}".format(len(dmm_voltage_list), dmm_voltage_list))
            dmm_average_voltage = float(dmm_average_voltage)*1000 #mv
            self.obj_mix.log_hw("cal beast voltage output", "dmm_average_voltage={}mV".format(dmm_average_voltage))

            self.ti_digitizer.beast_multi_sample_no_calulate("300_0", 'sensor --sel motor1 --exectest move --testopts "--pos 2000 --dir fwd"', unit="HZ")
            beast_average_voltage = self.ti_digitizer.get_moto_data("AVERAGE")
            self.obj_mix.log_hw("cal beast voltage output", "beast_average_voltage={}mV, dmm_average_voltage={}mV".format(beast_average_voltage, dmm_average_voltage))

            self.x1_list.append(beast_average_voltage)
            self.y1_list.append(dmm_average_voltage)
            print self.y1_list

        gain, offset = np.polyfit(self.x1_list, self.y1_list, 1)
        self.gain, self.offset = gain, offset
        self.obj_mix.log_hw("cal beast voltage output", "gain={}, offset={}".format(gain, offset))
        print "gain, offset", gain, offset

        #cal_info_to_eeprom.append([idx, gain, offset, stop_volt])
        #self.obj_mix.log_hw("cal current output", "gain={}, offset={}".format(self.gain, self.offset))
        
        # if not self.check_gain(gain, 1.05, 1.09999):
        #     self.cal_result = False
        #     self.obj_mix.log_hw("read_voltage", "===============")
        # if abs(offset) > 100:
        #     self.cal_result = False
        #     self.obj_mix.log_hw("read_voltage", "========9999=====")
        cal_info_to_eeprom.append([301, gain, offset, 100])
        cal_info_to_eeprom.append([305, gain, offset, 100])
        return gain


    @handle_response
    def get_cal_dagger_current(self, *args, **kwargs):

        rigel_channel = str(args[0])
        idx = int(args[1])
        # current_list = [2, 7, 20, 50, 80]
        current_list = [1, 2, 3, 4, 7]
        self.obj_mix.log_hw("cal current output", "calibration current_list={}".format(current_list))
        self.x1_list = []
        self.y1_list = []
        self.dmm = DMM(self.obj34461)
        #dc = DMM(self.obj63600)
        self.obj63600.loadon()
        time.sleep(1)
        self.obj63600.write(0)
        time.sleep(1)
        self.obj_ti_datalogger.get_power_voltage_cal(2000, 125000)
        time.sleep(1)

        self.obj_ti_datalogger.get_power_voltage_cal(10000, 125000)
        dagger_base_current = self.obj_ti_datalogger.get_power_current_cal()
        self.obj_mix.log_hw("cal current output", "dagger_base_current={}".format(dagger_base_current))
        dmm_base_curr, dmm_base_curr_list = self.dmm.measure_current(mes_range=1.0, loop_times=1000, nplc=0.02)
        dmm_base_curr, dmm_base_curr_list = dmm_base_curr * 1000, map(lambda x: x * 1000, dmm_base_curr_list)

        self.y1_list.append(dmm_base_curr)
        self.x1_list.append(dagger_base_current)

        self.obj_mix.log_hw("cal current output", "dmm_base_curr={} mA, len(dmm_base_curr_list)={}, dmm_base_curr_list={}".
            format(dmm_base_curr, len(dmm_base_curr_list), dmm_base_curr_list))

        for current in current_list:
            self.obj63600.write(current)

            time.sleep(1)
            self.obj_ti_datalogger.get_power_voltage_cal(10000, 125000)
            dagger_current = self.obj_ti_datalogger.get_power_current_cal()
            time.sleep(1)
            dmm_current, dmm_curr_list = self.dmm.measure_current(mes_range=1.0, loop_times=1000, nplc=0.02)
            dmm_current, dmm_curr_list = dmm_current * 1000, map(lambda x: x * 1000, dmm_curr_list)

            self.obj_mix.log_hw("cal current output", "dagger_current={}mA".format(dagger_current))
            self.obj_mix.log_hw("cal current output", "dmm_current={}mA, len(dmm_curr_list)={}, dmm_curr_list={}".
                format(dmm_current, len(dmm_curr_list), dmm_curr_list))
            self.x1_list.append(dagger_current)
            self.y1_list.append(dmm_current)

        self.obj_mix.log_hw("cal current output", "y1_list={}".format(self.y1_list))
        self.obj_mix.log_hw("cal current output", "x1_list={}".format(self.x1_list))
        # self.obj63600.loadoff()

        gain, offset = np.polyfit(self.x1_list, self.y1_list, 1)
        self.gain, self.offset = gain, offset
        stop_volt = int(100)

        cal_info_to_eeprom.append([idx, gain, offset, stop_volt])
        self.obj_mix.log_hw("cal current output", "gain={}, offset={}".format(self.gain, self.offset))

        return gain

    @handle_response
    def verify_dagger_cal(self, *args, **kwargs):
        current = int(args[0])
        self.obj63600.write(current)
        time.sleep(1)
        self.obj_mix.log_hw("verify_cal_current", "ELoad current set to {}mA".format(current))
        self.obj_ti_datalogger.get_power_voltage_cal(10000, 125000)
        dagger_current = self.obj_ti_datalogger.get_power_current_cal()
        calibrated_dagger_cur = self.obj_wibEEprom.do_system_cal(index=600, value=dagger_current)

        dmm_current, dmm_curr_list = self.dmm.measure_current(mes_range=1.0, loop_times=1000, nplc=0.02)
        dmm_current = dmm_current * 1000
        self.obj_mix.log_hw("verify_dagger_cal", "dmm_current={}mA, calibrated_dagger_cur={}mA".format(dmm_current, calibrated_dagger_cur))
        return calibrated_dagger_cur


    @handle_response
    def read_cal_offset(self, *args, **kwargs):
        return self.offset


    @handle_response
    def script_ver(self, *args, **kwargs):
        return "V0.01"

    @handle_response
    def oqc_open(self, *args, **kwargs):
        global TOLERANCE
        TOLERANCE = True
        del cal_info_to_eeprom[:]
        self.datalogger_init = True
        self.cal_result = True

        if len(args) != 2:
            return "--FAIL--MISS-PARA"
        inst_name = args[0]
        para = args[1]
        if inst_name.lower() == "inst_2400":
            arr_para = para.split('@')
            if len(arr_para) != 3:
                return "--FAIL--MISS-PARA"
            uart_path = arr_para[0]
            baud_rate = arr_para[1]
            timeout = arr_para[2]
            return self.obj2400.open(uart_path.strip(), int(baud_rate), float(timeout))
        elif inst_name.lower() == "inst_33522":
            return self.obj33522.open(str(para.strip()))

        elif inst_name.lower() == "inst_63600":
            return self.obj63600.open(str(para.strip()))


        elif inst_name.lower() == "inst_34461":
            return self.obj34461.open(str(para.strip()))
        elif inst_name.lower() == "inst_oqc_board":
            arr_para = para.split('@')
            if len(arr_para) != 2:
                return "--FAIL--MISS-PARA"
            host = arr_para[0]
            port = arr_para[1]
            return self.objOQCBoard.open(host.strip(), int(port))
        elif inst_name.lower() == "set_system_cal":
            # if para == "SKIP":
            #     self.obj_wibEEprom.write_cal_flag(True)
            return True
        else:
            return "--FAIL--Instr Name Error"

    @handle_response
    def oqc_close(self, *args, **kwargs):
        # self.obj_wibEEprom.write_cal_flag(False)
        if len(args) != 1:
            return "--FAIL--MISS-PARA"
        inst_name = args[0]
        if inst_name.lower() == "inst_2400":
            return self.obj2400.close()
        elif inst_name.lower() == "inst_33522":
            return self.obj33522.close()
        elif inst_name.lower() == "inst_34461":
            return self.obj34461.close()
        elif inst_name.lower() == "inst_oqc_board":
            return self.objOQCBoard.close()
        elif inst_name.lower() == "inst_63600":
            self.obj63600.loadoff()
            return self.obj63600.close()
        else:
            return "--FAIL--Instr Name Error"


    def check_tolerance(self, output, standard_v, measure_v, gain, offset, tolerance=0.5, lls=0.99, uls=1.01):
        global TOLERANCE
        global CURRENT_CAL_INDEX
        cal = measure_v * gain + offset
        # if self.obj_pub:
        #     self.obj_pub.publish("34461A: {}, Fixture: {}, cal:{}={}*{}+({}), 34461A-cal:{}".format(standard_v, measure_v, cal, measure_v, gain, offset, standard_v-cal))
        print "34461A: ", standard_v, 'Fixture: ', measure_v, " cal:", cal, '34461A-cal:', standard_v - cal
        data = '{},{},{},{},{}'.format(output, standard_v, measure_v, cal, standard_v - cal)
        write_csv(data)
        CURRENT_CAL_INDEX += 1
        # if self.obj_pub:
        #     self.obj_pub.publish("current process: {}/{}".format(CURRENT_CAL_INDEX, TOTAL_CAL))
        print 'current process: ', CURRENT_CAL_INDEX, '/', TOTAL_CAL
        # print 'Actual tolerance: ', abs((float(standard_v) - float(measure_v)) / standard_v), '%'
        # print 'Need tolerance: ', tolerance, '%'
        # print 'low: ', cal * (1-tolerance/100.0)
        # print 'high: ', cal * (1 + tolerance / 100.0)
        # if cal * (1 - tolerance / 100.0) <= float(standard_v) <= cal * (1 + tolerance / 100.0):
        # if self.obj_pub:
        #     self.obj_pub.publish("standard_v:{}, low_limit:{}, high_limit:{}".format(standard_v, (cal - abs(cal*tolerance / 100.0)), (cal + abs(cal*tolerance / 100.0))))
        if (cal - abs(cal*tolerance / 100.0)) <= float(standard_v) <= (cal + abs(cal*tolerance / 100.0)):
            TOLERANCE = True
        else:
            TOLERANCE = False
            # if self.obj_pub:
            #     self.obj_pub.publish("TOLERANCE: {}==".format((cal - abs(cal * tolerance / 100.0)), float(standard_v), (cal + abs(cal * tolerance / 100.0))))
            print "TOLERANCE:", (cal - abs(cal * tolerance / 100.0)), float(standard_v), (cal + abs(cal * tolerance / 100.0)), "=="
        # if self.obj_pub:
        #     self.obj_pub.publish("result: ".format(TOLERANCE))
        return self.check_gain(gain, lls, uls)

    def check_gain(self, gain, lls, uls):
        global TOTAL_TEST_COUNT
        global FAIL_TEST_COUNT
        TOTAL_TEST_COUNT += 1
        # print 'gain: ', gain
        # print 'lls: ', lls
        # print 'uls', uls
        if gain >= lls and gain <= uls:
            return True
        else:
            FAIL_TEST_COUNT += 1
            return False

    def calculate_voltage(self, start_volt, stop_volt, step=CAL_STEP):
        step_val = (stop_volt - start_volt) / float(step + 1)
        val_list = [start_volt + i * step_val for i in range(1, step + 1)]
        self.obj_mix.log_hw("calculate_voltage", "[cal list]: {}{}".format(val_list, '$' * 10))
        print 'cal list: ', val_list, '$' * 10, '\n'
        return val_list


    @handle_response
    def popup_alert_window(self, *args, **kwargs):
        ret = os.system( "osascript -e 'tell app \"Python\" to display dialog \"Please make sure you wanna erase calibration data!!!\"'".format(
                    self.site + 1))
        print "popup_alert_window", ret
        if ret != 0:
            return "--FAIL--"
        else:
            return "--PASS--"

    @handle_response
    def erase_calibration(self, *args, **kwargs):
        if len(args) != 1:
            return "--FAIL--MISS-PARA"
        erase = args[0].split("@")
        erase_start = erase[0].strip()
        erase_end = erase[1].strip()
        # for i in range(int(erase_start),int(erase_end)+1):
        #     erase_cal = self.obj_wibEEprom.erase_calibration_cell(i)
        return "--PASS--"


    @handle_response
    def write_to_file(self, *args, **kwargs):
        location = args[0]
        if location == "EEPROM":
            if not self.cal_result:
                del cal_info_to_eeprom[:]
                return "--FAIL--Cal Result Fail"
            for item in cal_info_to_eeprom:
                self.obj_wibEEprom.write_calibration_cell(item[0], item[1], item[2], item[3])

            for item in cal_info_to_eeprom:
                # self.obj_mix.log_hw("dump calibration data", "")
                self.obj_mix.log_hw("dump calibration data", "index={}, value={}".format(item[0], self.obj_wibEEprom.read_calibration_cell(item[0])))
                print "dump calibration data"
                print "index={}, value={}".format(item[0], self.obj_wibEEprom.read_calibration_cell(item[0]))
        else:
            import datetime
            self.write_log_csv(cal_info_to_eeprom, location + "/{}.csv".format(str(datetime.datetime.now())))
        del cal_info_to_eeprom[:]
        if not self.cal_result:
            return "--FAIL--Cal Result Fail"
        return "--PASS--"

    def write_log_csv(self, data, path):
        lines = "index,gain,offset"
        for line in data:
            lines += "\n{},{},{}".format(line[0], line[1], line[2])
        import os
        fold_path = os.path.dirname(path)
        if os.path.exists(fold_path) is False:
            os.makedirs(fold_path)
        with open(path, "w") as f:
            f.write(lines)


if __name__ == '__main__':
    pass



