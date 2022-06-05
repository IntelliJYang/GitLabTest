# -*-coding:utf-8 -*-
from datetime import datetime, timedelta
from mixdagger import dagger
from mix.lynx.rpc.profile_client import RPCClientWrapper
from threading import Thread
from datapath.datalogger import DataLogger
import time
import numpy as np

#############SG############
class datalogger(object):
    '''
    instance    datalogger
    
    rpc_endpoint = {"requester": "tcp://169.254.1.31:7801", "receiver": "tcp://169.254.1.31:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.10:5553", "upstream": "tcp://169.254.1.10:15553"}
    edp = {
        "rpc_endpoint": rpc_endpoint,
        "streaming_endpoint": streaming_endpoint
    }
    '''
    def __init__(self, client, rpc_endpoint, streaming_endpoint, publisher):
        super(datalogger, self).__init__()
        self.dagger = dagger(client)
        self.client = client
        print(rpc_endpoint, streaming_endpoint, "==9")
        self.datalogger = DataLogger(rpc_endpoint, streaming_endpoint)
        self.runFlag = False
        self.thread = None
        self.publisher = publisher
        self.client.publisher.publish('[{}]:    {}\r'.format(rpc_endpoint, streaming_endpoint))
        self.data = ""
        self.voltage_list = []
        self.current_list = []
        self.cal_data = list()

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def open(self, dma_ch='ch1'):
        """
        dagger_ch:         int/string, [0, 1, 'all'],   the specific channel to disable continuous measure mode.
        """
        self.runFlag = True
        self.datalogger.open('datalogger', dma_ch)
        return True

    def start(self, dagger_ch='all', sample_rate=1000):
        self.runFlag = True
        self.datalogger.start()
        self.dagger.multi_points_measure_disable(dagger_ch)
        self.dagger.multi_points_measure_enable(dagger_ch, sample_rate)
        self.thread = Thread(target=self._start_monitor, name='datalogger')
        self.thread.setDaemon(True)
        self.thread.start()
        return True

    def stop(self, dagger_ch='all'):
        self.runFlag = False
        self.dagger.multi_points_measure_disable(dagger_ch)
        self.datalogger.stop()
        if self.thread:
            self.thread.join()
        self.client.dma_ip.reset_channel(1)
        return True

    def close(self):
        self.runFlag = False
        self.datalogger.close()
        return True

    def shutdown_all(self):
        self.client.datalogger.shutdown_all()
        return True

    def _start_monitor(self):
        self.publisher.publish('timestamp1,voltage(mV),timestamp2,current(mA)\r\n')
        while self.runFlag:
            data = self.datalogger.read_data()
            if data:
                val = self._parse_data(data)
                self.publisher.publish(val)

    def _parse_data(self, raw_data):
        ret = []
        # ret = ''
        volts = dict()
        every_channel_num = dict()
        while len(raw_data) >= 4:
            channel = raw_data[0]
            code = raw_data[1] | raw_data[2] << 8 | raw_data[3] << 16
            voltage = self.code_2_mvolt(code, 5000.0, 24) * 1
            idx_voltage = "1"
            idx_current = "3"
            if channel == 0:
                voltage = voltage * 4   # ch0 voltage has 4x div
                voltage = self.do_cal(voltage, idx_voltage)
            else:
                voltage = self.do_cal(voltage, idx_current)
            raw_data = raw_data[4:]
            if not volts.get(channel):
                volts[channel] = [str(voltage)]
                every_channel_num[channel] = 1
            else:
                volts[channel].append(str(voltage))
                every_channel_num[channel] += 1
        min_count = min(every_channel_num.values())
        arr_keys = every_channel_num.keys()
        arr_keys.sort()
        for i in range(0, min_count):
            time_now = datetime.strftime(datetime.now() + timedelta(milliseconds=-1 * (min_count - i - 1)), '%m/%d/%Y %H:%M:%S.%f')
            for key in arr_keys:
                ret.append(time_now + ',')
                ret.append(volts.get(key)[i])
                if key != arr_keys[-1]:
                    ret.append(',')
                # ret = ret + ',' + volts.get(key)[i]
            # ret += '\r\n'
            ret.append('\r\n')
        return ''.join(ret)
        # return ret
    
    def code_2_mvolt(self, code, mvref, bits):
        range_code = 1 << (bits - 1)
        volt = code
        volt -= range_code
        volt /= float(range_code)
        volt *= mvref
        return volt

    def read_serial_number(self):
        return self.dagger.read_serial_number()

    def start_datalogger(self, dagger_ch='all', sample_rate=1000):
        self.runFlag = True
        self.datalogger.start()
        self.dagger.multi_points_measure_disable(dagger_ch)
        self.dagger.multi_points_measure_enable(dagger_ch, sample_rate)
        return True

    def set_datalogger_flag(self, flag):
        self.data = ""
        self.voltage_list = []
        self.current_list = []
        self.log('set_datalogger_flag', "result={}".format("True"))

    def get_data(self, duration_ms, sample_rate=1000):
        start_time = time.time()
        duration = float(duration_ms) / 1000.0
        ret_v = 0
        ret_c = 0
        length = 0
        i = 0
        raw_data = []
        while True:
            raw_data = raw_data + self.datalogger_read(1000)
            self.log('raw_data', "length={}".format(len(raw_data)))

            if time.time() - start_time > duration:
                self.log('raw_data', "length={}".format(len(raw_data)))
                self.parse_data(raw_data)
                self.voltage_list = self.voltage_list[-125000:]
                self.current_list = self.current_list[-125000:]
                self.log('datalogger_data', "current(length:{} {}\r\n)".format(len(self.current_list), self.current_list[-10:]))
                length = length + len(self.current_list)
                temp1 = np.mean(self.voltage_list)
                temp2 = np.mean(self.current_list)
                ret_v = (ret_v + temp1)
                ret_c = (ret_c + temp2)
                i = i + 1
                self.voltage_list = []
                self.current_list = []
                break
            time.sleep(0.001)
        if i > 0:
            ret_v = ret_v/i
            ret_c = ret_c/i
        idx_voltage = "1"
        idx_current = "3"
        # ret_v = self.do_cal(ret_v, idx_voltage)
        # ret_c = self.do_cal(ret_c, idx_current)

        self.log('datalogger_data', "voltage(length:{} {} {}\r\n)".format(length, ret_v, ret_c))
        return ret_v, ret_c

    def datalogger_read(self, duration_ms):
        '''
        :return:
        '''
        start_time = time.time()
        duration_ms = float(duration_ms) / 1000.0
        data_list = []
        while True:
            # time.sleep(0.001)
            d = self.datalogger.read_data()
            if d:
                data_list += d
            if time.time() - start_time > duration_ms:
                break
        return data_list

    def parse_data(self, raw_data):
        ret = list()
        # every_channel_num = dict()
        i = 0
        pos = 0
        len_data = len(raw_data)
        while pos + 4 <= len_data:
            # print raw_data
            buf = raw_data[pos:(pos + 4)]
            pos = pos + 4
            channel = buf[0]
            code = buf[1] | buf[2] << 8 | buf[3] << 16
            voltage = self.code_2_mvolt(code, 5000.0, 24) * 1
            if channel == 0:
                voltage = voltage * 4
                self.voltage_list.append(voltage)
            else:
                self.current_list.append(voltage)
            i = i + 1
            if i % 20000 == 0:
                time.sleep(0.001)
        return True

    def set_cal_data(self, cal_data):
        self.cal_data = cal_data

    def do_cal(self, value, channel):
        cal_info = self.cal_data[int(channel)]
        isUsed = cal_info.get("is_use")
        if isUsed:
            offset = cal_info.get("offset")
            gain = cal_info.get("gain")
            real_data = value*gain + offset
            self.log("calibration", "offset={}, gain={}, orignal_value={}, calibration_vaule={}".format(offset, gain, value, real_data))
            return real_data
        return value

        

if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}