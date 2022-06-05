# -*-coding:utf-8 -*-
import time
from threading import Thread
from mixbeast import beast
from mixpsmux import ps_mux
from datapath.datalogger import DataLogger
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class digitizer(object):
    def __init__(self, client, rpc_endpoint, streaming_endpoint, site):
        super(digitizer, self).__init__()
        self.client = client
        self.beast = beast(client)
        self.psmux = ps_mux(client)
        self.logger = DataLogger(rpc_endpoint, streaming_endpoint)
        self.logger.open('datalogger', 'ch2')
        self.channel_list = list()
        self.runFlag = False
        self.thread = None
        self.site = site
        self.mode = None
        self.cal_data = list()

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def __del__(self):
        self.logger.close()

    def set_ref_voltage(self, voltage_list):
        """
        voltage_list = [[0, 450], [1, 400], [2, 350]]
        voltage_list = ["all", 450]
        """
        self.channel_list = list()
        assert isinstance(voltage_list, list)

        if isinstance(voltage_list[0], basestring):
            self.psmux.set_trigger_ref_voltage(voltage_list[0], voltage_list[1])
            self.channel_list = [i for i in xrange(40)]
        elif isinstance(voltage_list, list):
            for item in voltage_list:
                self.psmux.set_trigger_ref_voltage(item[0], item[1])
                self.channel_list.append(item[0])
        else:
            return False
        return True

    def mux_measure(self, duration, channel):
        self.log('digitizer', "set_ref_voltage({})".format(duration))
        self.beast.select_range('DC_VOLT', 20)
        self.beast.set_measure_mask(0x30)

        samplerate = 1000
        channel_list = [channel]
        monitor_time = 1000
        self.beast.adc_enable()
        self.psmux.start_monitor(samplerate, channel_list, monitor_time, False)

        
        time.sleep(0.2)
        rms, average = self.beast.rms_measure(duration)
        self.beast.adc_disable()
        return rms, average

    def mux_freq_measure(self, duration, channel):
        self.log('digitizer', "mux_freq_measure({})".format(duration))
        # self.beast.select_range('DC_VOLT', 20)
        # self.beast.set_measure_mask(0xC0)

        samplerate = 1000
        channel_list = [channel]
        monitor_time = 5000

        self.beast.reset()
        time.sleep(0.2)
        self.beast.select_range('AC_VOLT', 20)
        self.beast.set_measure_mask(0)
        # self.beast.set_measure_mask(0xC0)
        
        self.psmux.board_init()
        time.sleep(0.2)
        # self.psmux.set_trigger_ref_voltage("all",10)
        
        self.psmux.start_monitor(1000, [27], 1000, False)
        time.sleep(0.2)
        
        # freq=10
        # duty=10
        self.beast.adc_enable()
        time.sleep(0.5)
        freq, duty = self.beast.frequency_measure(500,"LP")
        # ret = self.beast.vpp_measure(200)
        # self.log("digitizer_enable", "[result]={}".format(ret))
        # self.psmux.stop_monitor()
        self.beast.adc_disable()
        return freq, duty

    def enable(self, voltage_list, mode, monitor_time=20000, samplerate=1000):
        '''
        voltage_list = [[0, 450], [1, 400], [2, 350]]
        voltage_list = ["all", 450]
        '''
        try:
            self.mode = mode
            self.runFlag = True
            self.beast.reset()
            time.sleep(0.2)
            self.beast.select_range('DC_VOLT', 20)
            self.beast.set_measure_mask(0x30)
            self.psmux.board_init()
            time.sleep(0.2)
            self.set_ref_voltage(voltage_list)
            self.beast.adc_enable()
            self.psmux.start_monitor(samplerate, self.channel_list, monitor_time, False)
            self.thread = Thread(target=self._start_read_data, name='digitizer')
            self.thread.setDaemon(True)
            self.thread.start()
            time.sleep(0.2)
            self.logger.start()
        except Exception as e:
            self.log("digitizer_enable", "[result]={}".format(e))
            print(e)

    def _start_read_data(self):
        import os
        file_name = '/tmp/digitizer_raw_site{}_{}.txt'.format(self.site, self.mode)
        if os.path.exists(file_name):
            os.remove(file_name)
        fh = open(file_name, 'w')
        while self.runFlag:
            raw_data = self.logger.read_data()
            if raw_data and len(raw_data) > 0:
                data = ','.join(map(str, raw_data))
                fh.write(data + ',')
                time.sleep(0.001)
        fh.close()

    def disable(self):
        try:
            self.runFlag = False
            self.psmux.stop_monitor()
            self.beast.adc_disable()
            self.logger.stop()
            self.thread.join()
            self.client.dma_ip.reset_channel(2)
            dict_data = self.parse_data()
            return dict_data
        except Exception as e:
            print(e)
            self.log("digitizer_disable", "[result]={}".format(e))
        return True

    def read_trigger_time(self, trigger_time="last", trigger_mode="fall"):
        assert trigger_time in ("last", "first")
        assert trigger_mode in ("rise", "fall")
        if trigger_time == "last":
            result = self.psmux.read_last_trigger_time(self.channel_list, trigger_mode)
        else:
            result = self.psmux.read_first_trigger_time(self.channel_list, trigger_mode)
        return result

    def parse_data(self):
        channel_raw_data = {}
        raw_data = open('/tmp/digitizer_raw_site{}_{}.txt'.format(self.site, self.mode), 'rb')
        data = raw_data.readlines()
        list_data = data[0].strip().split(',')
        pos = 0
        len_data = len(list_data)
        while pos + 4 <= len_data:
            buf = list_data[pos:pos + 4]
            pos = pos + 4
            buf3 = buf[3]
            if type(buf3) is str:
                buf3 = int(buf3)
            if buf3 != 0:
                continue
            channel = str(buf[2])
            buf0 = buf[0]
            buf1 = buf[1]
            if type(buf0) is str:
                buf0 = int(buf0)
            if type(buf1) is str:
                buf1 = int(buf1)

            raw_data = buf0 | (buf1 << 8)
            real_data = (raw_data - 0x8000) * 20200.0 / 0x10000

            if int(channel) == 3 or int(channel) == 34:
                real_data = real_data * 4 * 1.009
            if len(self.cal_data) == 40:
                if int(channel) < 40:
                    cal_info = self.cal_data[int(channel)]
                    isUsed = cal_info.get("is_use")
                    if isUsed:
                        offset = cal_info.get("offset")
                        gain = cal_info.get("gain")
                        real_data = real_data*gain + offset


            real_data = round(real_data, 2)
            if int(channel) in channel_raw_data:
                channel_raw_data[int(channel)].append(real_data)
            else:
                channel_raw_data[int(channel)] = []
                channel_raw_data[int(channel)].append(real_data)
        return channel_raw_data

    def read_serial_number(self):
        return self.beast.read_serial_number()

    def set_cal_data(self, cal_data):
        self.cal_data = cal_data

    def open_datalogger(self, duration_ms, samplerate):
        '''
        :param scope:
        :return:
        '''
        # self.beast.reset()
        # time.sleep(0.2)
        self.beast.select_range('DC_VOLT', 20)
        self.beast.set_measure_mask(0x30)
        # self.psmux.board_init()
        time.sleep(0.1)
        self.beast.adc_enable()
        self.psmux.start_monitor(samplerate, [0], duration_ms+200, False)
        self.logger.start()

    def get_datalogger_data(self, duration_ms, samplerate):
        
        start_time = time.time()
        duration = float(duration_ms) / 1000.0
        data_list = []
        # self.log("get_datalogger_data", "[result]={}".format("e"))
        raw_data = []
        while True:
            time.sleep(0.05)
            raw_data = self.logger.read_data()
            if raw_data:
                data_list += raw_data
            if time.time() - start_time > duration:
                break
        
        if len(data_list) < 10000:
            start_time = time.time()
            while True:
                time.sleep(0.05)
                raw_data = self.logger.read_data()
                if raw_data:
                    data_list += raw_data
                if time.time() - start_time > duration:
                    break
        self.psmux.stop_monitor()
        self.beast.adc_disable()
        time.sleep(0.1)
        raw_data = self.logger.read_all(5)
        if raw_data:
            data_list += raw_data
        self.logger.stop()
        time.sleep(0.1)
        self.client.dma_ip.reset_channel(2)
        return data_list

    def parse_datalogger_data(self, list_data):
        channel_data = []
        
        pos = 0
        len_data = len(list_data)
        while pos + 4 <= len_data:
            buf = list_data[pos:pos + 4]
            pos = pos + 4
            buf3 = buf[3]
            if type(buf3) is str:
                buf3 = int(buf3)
            if buf3 != 0:
                continue
            channel = str(buf[2])
            buf0 = buf[0]
            buf1 = buf[1]
            if type(buf0) is str:
                buf0 = int(buf0)
            if type(buf1) is str:
                buf1 = int(buf1)

            raw_data = buf0 | (buf1 << 8)
            real_data = (raw_data - 0x8000) * 20200.0 / 0x10000

            real_data = round(real_data, 2)
            channel_data.append(real_data)
        return channel_data


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
    d = digitizer(client, rpc_endpoint, streaming_endpoint)

    d.enable([[0, 100], [1, 200], [3, 400], [5, 450]])
    time.sleep(5)
    d.disable()