# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class sgw2(object):
    """
    class dmm002001
    """

    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def reset(self):
        self.log('sgw2', "reset")
        ret = self.client.w2.reset()
        self.log('sgw2_reset', ret)

    def set_measure_path(self, channel):
        '''
        WolverineII set measure path.

        Args:
            channel:   string, ['100uA', '2mA', '5V', '5VCH2'], default '5V', set range for different channel.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('sgw2', "set_measure_path({})".format(channel))
        ret = self.client.w2.set_measure_path(channel)
        self.log("sgw2 set_measure_path" , ret)
        return ret

    def read_measure_value(self, sample_rate=1000, count=1):
        '''
        Read current average value. The returned value is calibrated if calibration mode is `cal`

        Args:
            sample_rate:    int, [5~250000], unit Hz, default 1000, set sampling rate of data acquisition, in SPS.
            count:          int, (>0), default 1, samples count taken for averaging.

        Returns:
            int, value, measured value defined by set_measure_path()
                        Voltage Channel always in mV
                        Current Channel always in mA
        '''
        self.log('sgw2', "read_measure_value({} {})".format(sample_rate, count))
        ret = self.client.w2.read_measure_value(sample_rate, count)
        self.log("sgw2 read_measure_value" , ret)
        return ret

    def read_measure_list(self, sample_rate=1000, count=1):
        '''
        Read measured data in list.

        For example if count is 5, the return list can be: [3711, 3712, 3709, 3703, 3702].
        The returned value is calibrated if calibration mode is `cal`

        Args:
            sample_rate:    float, [5~250000], unit Hz, default 1000, set sampling rate of data acquisition, in SPS.
            count:          int, (>0), defualt 1, samples count taken for averaging. Default 1

        Returns:
            list, [value1, ..., valueN], measured value defined by set_measure_path()
                    Voltage Channel always in mV
                    Current Channel always in mA
        '''
        self.log('sgw2', "read_measure_list({} {})".format(sample_rate, count))
        ret = self.client.w2.read_measure_list(sample_rate, count)
        self.log("sgw2 read_measure_list" , ret)
        return ret

    def enable_continuous_sampling(self, channel='5V', sample_rate=1000, down_sample=1, selection='max'):
        '''
        This function enables continuous sampling and data throughput upload to upper stream.

        Down sampling is supported. For example, when down_sample =5, selection=max,
        select the maximal value from every 5 samples, so the actual data rate is reduced by 5.
        The output data inflow is calibrated if calibration mode is `cal`
        During continuous sampling, the setting functions, like set_calibration_mode(),
        set_measure_path(), cannot be called.

        Args:
            channel:    string, ['5V', '5VCH2', '5VBOTH', '100uA', '2mA'], default '5V', '5V' is voltage channel1.
                                '5VCH2' is voltage channel 2. '5VBOTH' is both voltage channels
                                '100uA' is 100uA current channel.
                                '2mA' is 2mA current channel.
            sample_rate:    float, [5~250000], unit Hz, default 1000, set sampling rate of data acquisition in SPS.
                                               please refer to AD7175 data sheet for more.
            down_sample:    int, (>0), default 1, down sample rate for decimation.
            selection:      string, ['max', 'min'], default 'max'. This parameter takes effect as long as down_sample is
                                    higher than 1. Default 'max'

        Returns:
            Str, 'done'
        '''
        self.log('sgw2', "enable_continuous_sampling({} {} {} {})".format(channel, sample_rate, down_sample, selection))
        ret = self.client.w2.enable_continuous_sampling(channel, sample_rate, down_sample, selection)
        self.log("sgw2 enable_continuous_sampling" , ret)
        return ret

    def disable_continuous_sampling(self):
        '''
        This function disables continuous sampling and data throughput upload to upper stream.

        This function can only be called in continuous mode, a.k.a, after continuous_sampling_enable()
            function is called.

        Returns:
            Str: 'done'
        '''
        self.log('sgw2', "disable_continuous_sampling")
        ret = self.client.w2.disable_continuous_sampling()
        self.log('sgw2_disable_continuous_sampling', ret)
        return ret

    def read_continuous_sampling_statistics(self, count=1):
        '''
        This function takes a number of samples to calculate RMS/average/max/min value of the set of sampled value.

        This function can only be called in continuous mode, a.k.a, after
        continuous_sampling_enable() function is called. Return 0 for the channels that are not enabled.
        The returned value is calibrated if calibration mode is `cal`

        Args:
            count:  int, (>0), defualt 1, samples count taken for calculation.

        Returns:
            dict, the channel data to be measured. {
                (rms_v1, <RMS in mVrms>),
                (avg_v1, <average in mVrms>),
                (max_v1, <maximal in mV>),
                (min_v1, <minimal in mV>),
                (rms_v2, <RMS in mVrms>),
                (avg_v2, <average in mVrms>),
                (max_v2, <maximal in mV>),
                (min_v2, <minimal in mV>),
                (rms_i, <RMS in mArms>),
                (avg_i, <average in mArms>),
                (max_i, <maximal in mA>),
                (min_i, <minimal in mA>)
            },
            for voltage voltage channel #1 and #2.
        '''
        self.log('sgw2', "read_continuous_sampling_statistics({})".format(count))
        ret = self.client.w2.read_continuous_sampling_statistics(count)
        self.log("sgw2 read_continuous_sampling_statistics" , ret)
        return ret

    def read_serial_number(self):
        '''
        MIXBoard read board serial-number: (247,59)

        :example:
                            sn = w2.read_serialnumber()
                            print(sn)
        '''
        self.log('sgw2', "read_serial_number")
        ret = self.client.w2.read_serial_number()
        self.log("sgw2 read_serial_number" , ret)
        return ret

    def sample_datalogging(self, timeout_ms=10000):
        '''
        voltage measurement data logging, return list raw data

        Returns:
            list data (it will effect by variable cal_mode)
        Examples:
            volt = dmm2.sample_datalogging()
            print volt
        Exceptions:
            WolverineException('Read DMA fail.') when read data from DMA fail.
        '''
        # don't judge return value due to we'll get empty response while reading
        self.log('sgw2', "dmm.sample_datalogging()")
        r = self.client.wpdmm.sample_datalogging(timeout_ms=timeout_ms)
        # self.log('sgw2', "wpdmm sample_datalogging return = {}".format(r))
        return r

    def datalogger_open(self, scope, sample_rate=2000, timeout_ms=2000):
        '''

        :param scope:
        :return:
        '''
        self.log('sgw2', "dmm.datalogger_open({}, {})".format(scope, sample_rate))
        channel = scope.upper()
        # channel = str(scope).lower()
        # if channel == "both":
        #     channel = "5VBOTH"
        # else:
        #     channel = self.switch_channel(channel)
        r = self.client.wpdmm.start_datalogger(channel, sample_rate, timeout_ms=timeout_ms)
        self.log('sgw2', "dmm.datalogger_open ret={}".format(r))
        if not r:
            self.log('sgw2', "--FAIL--_{}.{}_Response is {}".format("wpdmm", "start_datalogger", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wpdmm", "start_datalogger", r))
        return r


    def datalogger_read(self, duration_ms):
        '''
        :return:
        '''
        start_time = time.time()
        duration_ms = float(duration_ms) / 1000.0
        data_list = []
        while True:
            time.sleep(0.01)
            if time.time() - start_time > duration_ms:
                break
            d = self.sample_datalogging()
            if d:
                data_list += d
        return data_list

    def datalogger_close(self, timeout_ms=500):
        self.log('sgw2', "dmm.datalogger_close()")
        r = self.client.wpdmm.stop_datalogger(timeout_ms=timeout_ms)
        self.log('sgw2', "dmm.datalogger_close ret={}".format(r))
        if not r:
            self.log('sgw2', "--FAIL--_{}.{}_Response is {}".format("wpdmm", "stop_datalogger", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wpdmm", "stop_datalogger", r))
        return r

    def parse_data_bk(self, raw_data):
        ret = list()
        # every_channel_num = dict()
        i = 0
        while len(raw_data) > 4:
            channel = raw_data[0]
            code = raw_data[1] | raw_data[2] << 8 | raw_data[3] << 16
            voltage = self._value_2_mvolt(code, 5000.0, 24) * 1
            raw_data = raw_data[4:]
            ret.append(voltage)
            i = i + 1
            if i % 5000 == 0:
                time.sleep(0.001)
        # ret = self.datalogger_calibration_with_data(ret, W2_CURRENT_MEASUMENT_INDEX)
        return ret

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
            voltage = self._value_2_mvolt(code, 5000.0, 24) * 1
            # raw_data = raw_data[4:]
            ret.append(voltage)
            i = i + 1
            if i % 5000 == 0:
                time.sleep(0.001)
        return ret

    def _value_2_mvolt(self, code, mvref, bits, gain=0x555555, offset=0x800000):
        '''
        translate the value to voltage value
        Args:
            code:    int.
            mvref:   float, unit mV.
            bits:    int, [16, 24, 32]
        Returns:
            float, value, unit mV.
        '''
        tmp = float(code - (1 << bits - 1)) * 0x400000 / gain
        volt = float(tmp + (offset - 0x800000)) / (1 << bits - 1) * mvref / 0.75
        return volt



if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}