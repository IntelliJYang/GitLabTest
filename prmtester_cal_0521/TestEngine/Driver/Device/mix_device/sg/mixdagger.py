# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class dagger(object):
    """dagger"""
    
    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def get_driver_version(self):
        '''
        Get Dagger driver version.

        Returns:
            string, current driver version.
        '''
        self.log('dagger', "get_driver_version")
        ret = self.client.dagger.get_driver_version()
        self.log('dagger_get_driver_version', ret)
        return ret

    def get_sampling_rate(self, channel):
        '''
        Get specific channel sampling rate.

        Args:
            channel:    int, [0, 1], 0 for current channel, 1 for voltage channel.

        Returns:
            float, value, AD7175 current sampling rate.

        '''
        self.log('dagger', "get_sampling_rate({})".format(channel))
        ret = self.client.dagger.get_sampling_rate(channel)
        self.log("dagger get_sampling_rate" , ret)
        return ret

    def multi_points_measure_enable(self, channel, sampling_rate):
        '''
        Dagger enable continuous measure mode.

        When continuous measure mode enabled, no function except
        continuous_measure_current shall be called. This function will start data upload through dma.

        Args:
            channel:         int/string, [0, 1, 'all'],  the specific channel to enable continuous measure mode.
            sampling_rate:   float, [5~250000], please refer to ad7175 datasheet.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('dagger', "multi_points_measure_enable({} {})".format(channel, sampling_rate))
        ret = self.client.dagger.multi_points_measure_enable(channel, sampling_rate)
        self.log("dagger multi_points_measure_enable" , ret)
        return ret

    def multi_points_measure_disable(self, channel):
        '''
        Dagger disable continuous measure mode. This function will disable data upload through dma.

        Args:
            channel:         int/string, [0, 1, 'all'],   the specific channel to disable continuous measure mode.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('dagger', "multi_points_measure_disable({})".format(channel))
        ret = self.client.dagger.multi_points_measure_disable(channel)
        self.log("dagger multi_points_measure_disable" , ret)
        return ret

    def multi_points_voltage_measure(self, channel, count=1):
        '''
        Do measure voltage in continuous mode.

        Note that when call this function, AD7175 shall have entered continuous
        mode by calling 'enable_continuous_measure'.

        Args:
            channel:     int, [0, 1], the specific channel to measure voltage.
            count:       int, [1~512], default 1, number of voltage to measure, max value is 512.

        Returns:
            dict, {"min": (value, 'mV'), "max": (value, 'mV'), "sum": (value, 'mV'),
                   "average": (value, 'mV'), "rms": (value, 'mVrms')},
                  min, max, sum, average and rms with unit.

        '''
        self.log('dagger', "multi_points_voltage_measure({} {})".format(channel, count))
        ret = self.client.dagger.multi_points_voltage_measure(channel, count)
        self.log("dagger multi_points_voltage_measure" , ret)
        return ret

    def voltage_measure(self, channel, sampling_rate=1000):
        '''
        Do measure voltage in single mode.

        Note that when call this function, AD7175 shall have exited continuous
        mode by calling 'disable_continuous_measure'.

        Args:
            channel:        int, [0, 1], the specific channel to measure voltage.
            sampling_rate:  float, [5~250000], please refer to ad7175 datasheet.

        Returns:
            list, [avg_volt, "mV"].

        '''
        self.log('dagger', "voltage_measure({} {})".format(channel, sampling_rate))
        ret = self.client.dagger.multi_points_voltage_measure(channel, sampling_rate)
        self.log("dagger voltage_measure" , ret)
        return ret

    def read_serial_number(self):
        '''
        MIXBoard read board serial-number: (247,59)

        :example:
                            sn = w2.read_serialnumber()
                            print(sn)
        '''
        self.log('dagger', "read_serial_number")
        ret = self.client.dagger.read_serial_number()
        self.log('dagger read_serial_number', ret)
        return ret


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
