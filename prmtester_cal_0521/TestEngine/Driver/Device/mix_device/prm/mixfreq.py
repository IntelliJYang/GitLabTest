# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class freql(object):

    def __init__(self, client):
        self.client = client

    def measure_frequency(self, measure_time):
        return self.client.freq.measure_frequency(measure_time)

    def beast_adc_reset(self):
        self.client.beast.reset()
        return 'done'

    def beast_measure_freq(self, duration):
        # self.client.beast.select_range('DC_VOLT', 20)
        # self.client.beast.set_measure_mask(0xC0)
        self.client.beast.adc_enable()
        time.sleep(0.2)
        ret = self.client.beast.frequency_measure(duration)
        self.client.beast.adc_disable()
        return ret
        # return self.client.beast.frequency_measure(duration)

    def vpp_measure(self, duration):
        # self.client.beast.select_range('DC_VOLT', 20)
        # self.client.beast.set_measure_mask(0x30)
        self.client.beast.adc_enable()
        time.sleep(0.05)
        ret = self.client.beast.vpp_measure(duration)
        self.client.beast.adc_disable()
        return ret

    def rms_measure(self, duration):
        self.client.beast.select_range('DC_VOLT', 20)
        # self.client.beast.set_measure_mask(0x30)
        self.client.beast.adc_enable()
        time.sleep(0.05)
        ret = self.client.beast.rms_measure(duration)
        self.client.beast.adc_disable()
        return ret

    def pwm_out_0(self, freq, duty, type):
        self.client.pwm_out_0.close()
        time.sleep(0.05)
        self.client.pwm_out_0.set_signal_type('square')
        self.client.pwm_out_0.set_signal_time(0xffffffff)
        self.client.pwm_out_0.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
        self.client.pwm_out_0.open()
        self.client.pwm_out_0.output_signal()
        return 'done'

    def pwm_out_1(self, freq, duty, type):
        self.client.pwm_out_1.close()
        time.sleep(0.05)
        self.client.pwm_out_1.set_signal_type('square')
        self.client.pwm_out_1.set_signal_time(0xffffffff)
        self.client.pwm_out_1.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
        self.client.pwm_out_1.open()
        self.client.pwm_out_1.output_signal()
        return 'done'

    def pwm_out_2(self, freq, duty, type):
        self.client.pwm_out_2.close()
        time.sleep(0.05)
        
        self.client.pwm_out_2.set_signal_type('square')
        self.client.pwm_out_2.set_signal_time(0xffffffff)
        self.client.pwm_out_2.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
        self.client.pwm_out_2.open()
        self.client.pwm_out_2.output_signal()
        return 'done'

    def pwm_out_3(self, freq, duty, type):
        self.client.pwm_out_3.close()
        time.sleep(0.05)
        
        self.client.pwm_out_3.set_signal_type('square')
        self.client.pwm_out_3.set_signal_time(0xffffffff)
        self.client.pwm_out_3.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
        self.client.pwm_out_3.open()
        self.client.pwm_out_3.output_signal()
        return 'done'

    def pwm_close(self, channel):
        if channel == 0:
            self.client.pwm_out_0.close()
        elif channel == 1:
            self.client.pwm_out_1.close()
        elif channel == 2:
            self.client.pwm_out_2.close()
        elif channel == 3:
            self.client.pwm_out_3.close()
        else:
            return 'Invalid channel'
        return 'done'

    def pwm_set_freq_duty(self, freq, duty, type, channel):
        if channel == 0:
            self.client.pwm_out_0.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
            self.client.pwm_out_0.output_signal()
        elif channel == 1:
            self.client.pwm_out_1.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
            self.client.pwm_out_1.output_signal()
        elif channel == 2:
            self.client.pwm_out_2.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
            self.client.pwm_out_2.output_signal()
        elif channel == 3:
            self.client.pwm_out_3.set_swg_paramter(125000000, freq, 0.5, duty / 100.0, 0)
            self.client.pwm_out_3.output_signal()
        else:
            return 'Invalid channel'
        return 'done'


class freqh(object):

    def __init__(self, client):
        self.client = client

    def measure_frequency(self, measure_time):
        return self.client.freq.measure_frequency(measure_time)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
