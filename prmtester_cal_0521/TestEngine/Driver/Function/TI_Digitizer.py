from ..Function.TI_Common import RootFunction
from ..Device.mix_device.sg.mixdigitizer import digitizer
from mix.lynx.rpc.profile_client import RPCClientWrapper
from TI_Define import *
from datetime import datetime, timedelta
import pypudding
from ..Utility.utility import Unit
import time
import re
from ..Device.mix_device.cal_table import PS_MUX_CAL
import numpy as np

class TI_Digitizer(RootFunction):
    def __init__(self, rpc_endpoint, stream_endpoint, driver=None):
        super(TI_Digitizer, self).__init__(driver)
        self.site = None
        self.obj_mix = None
        self.obj_digitizer = None
        self.rpc_endpoint = rpc_endpoint
        self.stream_endpoint = stream_endpoint
        self.head = ''
        self.is_running = False
        self.log_paths = []
        self.resp = None
        self.obj_ti_dut  = None
        self.moto_data = {}

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.site = self.get_method("site")
        self.obj_digitizer = digitizer(self.obj_mix.client, self.rpc_endpoint, self.stream_endpoint, self.site)
        self.obj_wibEEprom = self.obj_mix.objwibEEprom
        self.obj_ti_dut = self.driver.get("ti_dut")
        self.moto_data.setdefalut('PEAK', 0)
        self.moto_data.setdefalut('FREQ_HIGH', 0)
        self.moto_data.setdefalut('FREQ_LOW', 0)

    @handle_response
    def start(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        mode = args[0]
        if mode not in ["Power_Up", "Power_Down"]:
            return PARA_ERROR

        self.head = 'time'
        if mode == 'Power_Up':
            io_list = [
                [0, 2900], [1, 400], [2, 360], [3, 625], [4, 400], [5, 400], [6, 360], [7, 400], [8, 400], [9, 400],
                [10, 400], [11, 400], [12, 400], [13, 400], [14, 400], [15, 360], [16, 400], [17, 400], [18, 400], [19, 400],
                [20, 400], [21, 400], [22, 400], [23, 400], [24, 400], [25, 400], [26, 400], [27, 400], [28, 400], [29, 400],
                [30, 400], [31, 400], [32, 400], [33, 400], [34, 3025], [35, 400], [36, 400], [37, 400], [38, 400], [39, 400]
            ]
        else:
            io_list = [
                [0, 2900], [1, 400], [2, 360], [3, 2500], [4, 400], [5, 400], [6, 360], [7, 400], [8, 400], [9, 400],
                [10, 400], [11, 400], [12, 400], [13, 400], [14, 400], [15, 360], [16, 400], [17, 400], [18, 400], [19, 400],
                [20, 400], [21, 400], [22, 400], [23, 400], [24, 400], [25, 400], [26, 400], [27, 400], [28, 400], [29, 400],
                [30, 400], [31, 400], [32, 400], [33, 400], [34, 100], [35, 400], [36, 400], [37, 400], [38, 400], [39, 400]
            ]
        for item in range(0, len(io_list)):
            channel_name = self._get_channel_name('ch{}'.format(item))
            self.head += ',{}'.format(channel_name)

        cal_data = []
        try:
            for i in range(40):
                channel_name = self._get_channel_name('ch{}'.format(i))
                index = PS_MUX_CAL.get(channel_name)
                if index:
                    self.obj_mix.log_hw("channel", "[result]={}".format(channel_name))
                    cal_info = self.obj_wibEEprom.read_calibration_cell(index)
                    cal_data.append(cal_info)
            self.obj_digitizer.set_cal_data(cal_data)
        except Exception as e:
            self.obj_mix.log_hw("read_cal_data", "[result]={}".format(e))

        time_out = int(args[1])
        self.obj_digitizer.enable(io_list, mode, monitor_time=time_out)
        self.is_running = True
        return "--PASS--"

    @handle_response
    def stop(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        file_name = args[0]
        dict_data = self.obj_digitizer.disable()
        self.is_running = False
        if type(dict_data) is dict and len(dict_data) > 0:
            self._write_file(dict_data, file_name)
        else:
            return "--FAIL--No digitizer data"
        return "--PASS--"

    def _write_file(self, dict_data, file_name):
        gh_info = pypudding.IPGHStation()
        product = gh_info[pypudding.IP_PRODUCT]
        station_type = gh_info[pypudding.IP_STATION_TYPE]
        max_count = max(len(item) for item in dict_data.values())
        arr_keys = dict_data.keys()
        arr_keys.sort()

        data_tmp = []
        # data_tmp = ''
        date_now = datetime.now()
        for i in range(0, max_count):
            time_now = datetime.strftime(date_now + timedelta(milliseconds=-1*(max_count-i-1)), '%m/%d/%Y %H:%M:%S.%f')
            data_tmp.append(time_now)
            for key in arr_keys:
                arr_tmp = dict_data.get(key)
                if len(arr_tmp) > i:
                    data_tmp.append(',')
                    data_tmp.append(str(arr_tmp[i]))
                    # data_tmp = data_tmp + ',' + str(arr_tmp[i])
                else:
                    data_tmp.append(',')
                    # data_tmp = data_tmp + ','
            data_tmp.append('\r\n')
            # data_tmp += '\r\n'
        str_tmp = ''.join(data_tmp)
        data_write = '{}\r\n{}'.format(self.head, str_tmp)
        file_path = '/vault/Station_log/{}_{}_UUT{}__{}_digitizer_{}.csv'.format(product, station_type, self.site,
                                                                             self.obj_mix.logging_time, file_name)
        self.log_paths.append(file_path)
        with open(file_path, 'w') as f:
            f.write(data_write)

    @handle_response
    def read_trigger_time(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        mode = args[0]
        pos = args[1]
        if mode not in ["rise", "fall"] or pos not in ["last", "first"]:
            return PARA_ERROR

        try:
            self.resp = self.obj_digitizer.read_trigger_time(pos, mode)
            self.obj_mix.log_hw("delay_time", "[result]={}".format(self.resp))
        except Exception as e:
            self.obj_mix.log_hw("read_trigger_time", "[result]={}".format(e))
            return "--FAIL--"
        return '--PASS--'

    @handle_response
    def parse_delay_time(self, *args, **kwargs):

        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        channel_a = int(args[0])
        channel_b = int(args[1])

        try:
            patt_a = re.compile("ch{}=(\d+)ns".format(channel_a))
            patt_b = re.compile("ch{}=(\d+)ns".format(channel_b))
            time_a = int(patt_a.findall(self.resp)[0])
            time_b = int(patt_b.findall(self.resp)[0])
            val = (time_b - time_a)/1000
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(val, "us", str(unit))
            self.obj_mix.log_hw("delay_time", "[result]={} {}".format(ret, unit))
        except Exception as e:
            self.obj_mix.log_hw("read_trigger_time", "[result]={}".format(e))
            return "--FAIL--"
        return ret

    @handle_response
    def parse_special_delay_time(self, *args, **kwargs):

        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        channel_a = int(args[0])
        channel_b = int(args[1])
        mode = "rise"
        pos = "first"

        try:
            data = self.obj_digitizer.read_trigger_time(pos, mode)

            patt_a = re.compile("ch{}=(\d+)ns".format(channel_a))
            patt_b = re.compile("ch{}=(\d+)ns".format(channel_b))
            time_a = int(patt_a.findall(self.resp)[0])
            time_b = int(patt_b.findall(data)[0])
            val = (time_b - time_a)/1000
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(val, "us", str(unit))
            self.obj_mix.log_hw("delay_time", "[result]={} {}".format(ret, unit))
        except Exception as e:
            self.obj_mix.log_hw("read_trigger_time", "[result]={}".format(e))
            return "--FAIL--"
        return ret

    @handle_response
    def parse_rise_first_data(self, *args, **kwargs):

        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        channel_a = int(args[0])
        channel_b = int(args[1])
        mode = "rise"
        pos = "first"

        try:
            data = self.obj_digitizer.read_trigger_time(pos, mode)

            patt_a = re.compile("ch{}=(\d+)ns".format(channel_a))
            patt_b = re.compile("ch{}=(\d+)ns".format(channel_b))
            time_a = int(patt_a.findall(self.resp)[0])
            time_b = int(patt_b.findall(data)[0])
            val = (time_a - time_b)/1000
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(val, "us", str(unit))
            self.obj_mix.log_hw("delay_time", "[result]={} {}".format(ret, unit))
        except Exception as e:
            self.obj_mix.log_hw("read_trigger_time", "[result]={}".format(e))
            return "--FAIL--"
        return ret

    @handle_response
    def mux_measure(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        try:
            duration = int(args[0])
            channel = int(args[1])
            rms, average = self.obj_digitizer.mux_measure(duration, channel)
            unit = kwargs.get("unit")
            rms = Unit.convert_unit(rms, "mV", str(unit))
            average = Unit.convert_unit(average, "mV", str(unit))
            return rms
        except Exception as e:
            self.obj_mix.log_hw("mux_measure", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def mux_tonmax_measure(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        try:
            duration = int(args[0])
            channel = int(args[1])
            freq, duty = self.obj_digitizer.mux_freq_measure(duration, channel)

            self.obj_mix.log_hw("mux_tonmax_measure", "[result]={} {}".format(freq, duty))
            ton_duty = 1000 / freq * duty / 100

            return ton_duty
        except Exception as e:
            self.obj_mix.log_hw("mux_tonmax_measure", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def get_moto_data(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        dict_key = (args[0])
        self.obj_mix.log_hw("get_moto_data", "[dict_key]={}".format(dict_key))
        if dict_key in self.moto_data.keys():
            self.obj_mix.log_hw("get_moto_data", "[dict_key]={}, [self.moto_data]={}".format(dict_key, self.moto_data))
            return self.moto_data.get(dict_key)
        else:
            self.obj_mix.log_hw("get_moto_data", "[result]={}".format("no keys in dict data"))
            return "--FAIL--"

    @handle_response
    def beast_multi_sample_no_calulate(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        list_data = args[0].split('_')
        duration = int(list_data[0])
        delay_cmd = int(list_data[1])
        if len(list_data)>2:
            measure_type = str(list_data[2])
        else:
            measure_type = "HP"
        cmd = str(args[1])
        unit = kwargs.get("unit")
        #self.moto_data['PEAK'] = 0
        self.moto_data["AVERAGE"] = 0

        ret = 0
        try:
            samplerate = 100000
            # self.obj_ti_dut._diags_clear()
            if delay_cmd == 0:
                self.obj_digitizer.open_datalogger(duration, samplerate)
            # self.obj_ti_dut._diags_send(cmd)

            time.sleep(delay_cmd/1000.0)                     
            if delay_cmd > 0:
                self.obj_digitizer.open_datalogger(duration, samplerate)
            raw_data = self.obj_digitizer.get_datalogger_data(duration, samplerate)
            #self.obj_mix.log_hw("beast_multi_sample_no_calulate", "len(raw_data)={}, raw_data={}".format(len(raw_data),raw_data))

            result = self.obj_digitizer.parse_datalogger_data(raw_data)
            # self.obj_mix.log_hw("beast_multi_sample_no_calulate", "[parse_datalogger_data]=length:{} {}".format(len(result), result))

            i = 0
            log_out = []
            for temp in result:
                if i % 10 == 0:
                    log_out.append(temp)
                i = i + 1
            #self.obj_mix.log_hw("[beast_multi_sample_no_calulate]", "[parse_datalogger_data]={}".format(log_out))

            data = self.filter_data(result)

            gain = 2
            # peak = np.max(data)
            average_beast_voltage = float(np.average(data))
            self.moto_data["AVERAGE"] = average_beast_voltage * gain
            self.obj_mix.log_hw("beast_multi_sample_no_calulate", "self.moto_data:{}".format(self.moto_data))
            ret = self.calculate_fft(data, samplerate)
            self.obj_mix.log_hw("beast_multi_sample_no_calulate", "[result]=frequence:{} average_beast_voltage:{}".format(ret, average_beast_voltage))

            # self.obj_ti_dut._diags_read(":-)", timeout=10,is_match=True)

            if measure_type == "LP":
                value =  Unit.convert_unit(ret[0], "HZ", str(unit))
            else:
                value =  Unit.convert_unit(ret[1], "HZ", str(unit))
            return value
        except Exception as e:
            self.obj_mix.log_hw("beast_multi_sample_no_calulate", "[result]={}".format(e))
            # self.obj_ti_dut._diags_read(":-)", timeout=10,is_match=True)
            ret = '--FAIL--{}'.format(e)
        
    def filter_data(self, input_data, threshold = 2000):
        data_len = len(input_data)
        if data_len <= 4096:
            return input_data

        filtered_out = []
        data_start = 0
        for i in range(data_len):
            if input_data[i] > threshold:
                data_start = i
                break

        data_end = data_len - 1
        for i in range(data_len):
            if input_data[data_len - i - 1] > threshold:
                data_end = data_len - i
                break

        filtered_out = input_data[data_start:data_end]

        # start = 0
        # if (data_start + data_end)/2 - 2048 > 0:
        #     start = (data_start + data_end)/2 - 2048 - data_start
        # filtered_out = filtered_out[start:]
        return filtered_out

    def calculate_fft(self, input_data, sample_rate):
        if len(input_data) < 4096:
            return []

        start = 0
        fft_N = 4096
        input_data = input_data[start:start+fft_N]
        input_data = input_data - np.mean(input_data)  # remove dc offset
        fft_out = np.absolute(np.fft.fft(input_data)) / float(fft_N)
        freq = np.absolute(np.fft.fftfreq(fft_N, d=1/float(sample_rate)))

        high_start = 0
        fft_low = 0
        i = 0
        j = 0
        temp = 0
        for data in fft_out:
            if data > temp:
                temp = data
                j = i
            if freq[i] > 5000 and high_start == 0:
                high_start = i
                break
            i = i + 1

        if freq[j] > 10:
            fft_low = freq[j]

        fft_high = 0
        i = high_start
        j = high_start
        temp = 0
        for data in fft_out[high_start:len(fft_out)-high_start]:
            if data > temp:
                temp = data
                j = i
            i = i + 1
        if freq[j] > 10:
            fft_high = freq[j]
        return [fft_low, fft_high]

    @handle_response
    def read_beast_sn(self, *args, **kwargs):
        try:
            ret = self.obj_digitizer.read_serial_number()
            return ret
        except Exception as e:
            self.obj_mix.log_hw("read_beast_sn", "[result]={}".format(e))
            return "--FAIL--"

    def _get_channel_name(self, channel):
        mapping_table = {
            "ch0": "PP3V8_VCC_MAIN",
            "ch1": "PP1V2_EXTSW",
            "ch2": "IO_MCONN_DETECT_L_3V8",
            "ch3": "PPVBUS_SYS",
            "ch4": "PP_CSOC_VDD_ICS_PHY",
            "ch5": "PP_CSOC_VDD_CIO",
            "ch6": "IO_CPMU_TO_CSOC_RESET_L",
            "ch7": "PP_CSOC_VDD_ICS_MCU",
            "ch8": "PP_CSOC_VDD_SOC",
            "ch9": "PP1V2_CSOC_VDD12_S2",
            "ch10": "PP_CSOC_VDD2_S2",
            "ch11": "PP0V7_CSOC_VDD_LOW_S2",
            "ch12": "PP_CSOC_VDD_SRAM",
            "ch13": "PP0V8_CSOC_VDD_FIXED",
            "ch14": "PP_CSOC_VDD_DISP",
            "ch15": "IO_SYS_ALIVE",
            "ch16": "PP1V2_CSOC_VDD12",
            "ch17": "PPVDD_AMPH_S2",
            "ch18": "PP1V8_CPMU_S2",
            "ch19": "PPVDD_ECPU",
            "ch20": "PPVDD_S1_SOC",
            "ch21": "PP1V8_S2",
            "ch22": "PP1V25_S2_SW5_TO_MBNRT",
            "ch23": "PPVDD_S1_SRAM",
            "ch24": "PPVDD_CPU",
            "ch25": "PP1V25_S2",
            "ch26": "PP1V2_SOC_LN",
            "ch27": "RIGEL_CURRENT_OPA_OUT_TO_BEAST_AND_DMM",
            "ch28": "PPVDD_S1_DISP",
            "ch29": "PP1V2_LDOX0_TO_XCAM_DVDD_CORE_PHY",
            "ch30": "PP1V06_S2",
            "ch31": "PPVDD_S1_QL",
            "ch32": "PP1V2_S2_CIO",
            "ch33": "PP1V8_S2_LDO15_TO_MBNRT",
            "ch34": "PPVBUS_SPFCAP_BOOST_ALWAYS",
            "ch35": "PP0V88_NAND",
            "ch36": "PP0V8_S1_SOC_FIXED",
            "ch37": "PP0V72_S2_VDDLOW",
            "ch38": "PP2V63_NAND",
            "ch39": "PP1V2_NAND"
        }
        if channel in mapping_table:
            return mapping_table[channel]
        else:
            return channel

