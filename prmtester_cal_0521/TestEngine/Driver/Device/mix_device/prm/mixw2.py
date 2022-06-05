# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class w2(object):

    def __init__(self, client):
        self.client = client
        self.measure_path = None

    def set_sampling_rate(self, sample_rate):
        '''
        :param sample_rate: int 5,10, 16.66,20, 49.96,59.92, 100,200, 397.5,500, 1000,2500, 5000 ,
                            10000, 15625,25000, 31250,50000, 62500,125000, 250000
        :return:
        '''
        return self.client.dmm.set_sampling_rate(sample_rate)

    def get_sampling_rate(self, channel):
        '''
        :param channel:‘7V’: voltage channel #1 ’7VCH2’: voltage channel #2 ‘7VBOTH’: both voltage channels ’200uA’:
        200uA current channel ‘5mA’: 5mA current channel
        :return:
        '''
        return self.client.dmm.get_sampling_rate(channel)

    def set_measure_path(self, channel):
        '''
        :param channel:‘7V’: voltage channel #1 ’7VCH2’: voltage channel #2 ‘7VBOTH’: both voltage channels ’200uA’:
        200uA current channel ‘5mA’: 5mA current channel
        :return:
        '''
        return self.client.dmm.set_measure_path(channel)

    def get_measure_path(self):
        '''
        :return:
        '''
        return self.client.dmm.get_measure_path()

    def read_measure_value(self, scope, sample_rate=1000, count=1, timeout_ms=50000):
        '''
        :param sample_rate:
        :param count:
        :return:
        '''
        if not self.measure_path:
            self.set_measure_path(scope)
        elif self.measure_path != scope:
            self.set_measure_path(scope)
        return self.client.dmm.read_measure_value(sample_rate, count, timeout_ms=timeout_ms)


    def read_measure_list(self, scope, sample_rate=1000, count=5, timeout_ms=50000):
        '''
        :param sample_rate:
        :param count:
        :return:
        '''
        if not self.measure_path or self.measure_path != scope:
            self.set_measure_path(scope)
        return self.client.dmm.read_measure_list(sample_rate, count, timeout_ms=timeout_ms)

    def disable_continuous_sampling(self):
        '''
        disable datalogger

        Returns:
            integer, time stamp
        Examples:
            curr = dmm2.disable_continuous_measure()
        '''
        return self.client.dmm.disable_continuous_sampling()

    def enable_continuous_sampling(self, channel, sample_rate=1000, down_sample=1, selection='max'):
        '''
        enable datalogger

        Args:
        channel:‘7V’: voltage channel #1 ’7VCH2’: voltage channel #2 ‘7VBOTH’: both voltage channels ’200uA’:
            200uA current channel ‘5mA’: 5mA current channel
        sample_rate: int
            set sampling rate of data acquisition, in SPS. Default 1000
        down_sample: int
            down sample rate for decimation.
        selection: string
            ‘max’|’min’. This parameter takes effect as long as down_sample is higher than 1. Default ‘max’
        Returns:
            integer, time stamp
        Examples:
            curr = dmm2.enable_continuous_measure()
        '''
        return self.client.dmm.enable_continuous_sampling(channel, sample_rate, down_sample, selection)

    def sample_datalogging(self):
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
        return self.client.dmm.sample_datalogging()

    def read_continuous_sampling_statistics(self, count):
        '''
        call set_measure_path and set_sampling_rate first
        Args:count: int
            samples count taken for calculation. Default 1
        Returns:
            dic, {
                    (rms_v1, <RMS in mVrms>),
                    (avg_v1, <average in mVrms>),
                    (max_v1, <maximal in mV>),
                    (min_v1, <minimal in mV>),
                    (rms_v2, <RMS in mVrms>),
                    (avg_v2, <average in mVrms>),
                    (max_v2, <maximal in mV>),
                    (min_v2, <minimal in mV>)
                    (rms_i, <RMS in mArms>),
                    (avg_i, <average in mArms>),
                    (max_i, <maximal in mA>),
                    (min_i, <minimal in mA>)
                    }
        Examples:
            curr_list = self.voltage_sample_datalogging("ch1", 2000)
        '''
        return self.client.dmm.read_continuous_sampling_statistics(count)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
