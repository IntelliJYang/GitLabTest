# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class starlord(object):

    def __init__(self, client):
        '''
        audio user example:
        1. audio.enable()
        2. audio.measure('right', '2V', 10000, 1)
        3. audio.disable()
        '''
        self.client = client

    def enable(self):
        '''
        Enable module data upload.

        Returns:
            string, "done", execution successful.
        '''
        return self.client.starlord.enable_upload()

    def disable(self):
        '''
        Disable module data upload.

        Returns:
            string, "done", execution successful.
        '''
        return self.client.starlord.disable_upload()

    def measure(self, duration_ms=200, channel='right', scope='2V', bandwidth_hz=10000, decimation_type=0xFF):
        '''
        Measure audio input signal, which captures data using CS5361.

        Args:
            channel:         string, ['left', 'right'], select input signal channel.
            scope:           string, ['2V', '20mV'], AD7175 measurement range.
            bandwidth_hz:    int/string, [42~48000], unit Hz, the signal bandwidth.
                             In theory the bandwidth must smaller than half the sampling rate.
                             eg, if sampling_rate = 192000, so bandwidth_hz  < 96000.
                             The bandwidth must be greater than the frequency of the input signal.
            decimation_type: int, [1~255], default 0xFF, sample data decimation.
                             decimation_type is 1 means not to decimate.
                             The smaller the input frequency, the larger the value should be.
            sampling_rate:   int, [0~192000], default 48000, unit Hz, ADC sampling rate.

        Returns:
            dict, {'vpp': value, 'freq': value, 'thd': value, 'thdn': value, 'rms': value, 'noisefloor': value},
            measurement result.
        '''
        self.enable()
        time.sleep(duration_ms/1000.0)
        result =  self.client.starlord.measure(channel, scope, bandwidth_hz, decimation_type, 48000)
        self.disable()
        return result


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
