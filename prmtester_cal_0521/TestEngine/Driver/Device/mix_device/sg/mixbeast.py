# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class beast(object):
    """
    class beast
    """
    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def reset(self):

        self.log('beast', "reset")
        ret = self.client.beast.reset()
        self.log('beast_reset', ret)
        return ret

    def select_range(self, signal_type, value):
        '''
        Select Beast measurement range. All support range shown as below.

        Args:
            signal_type:    string, ['DC_VOLT', 'AC_VOLT'], Range signal_type string.
            value:          int, [2, 20], Range value.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('beast', "select_range({} {})".format(signal_type, value))
        ret = self.client.beast.select_range(signal_type, value)
        self.log("beast select_range" , ret)
        return ret

    def enable_continuous_measure(self):
        '''
        Beast enable_continuous_measure function. board data will be copyed to dma when this function called.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('beast', "enable_continuous_measure")
        ret = self.client.beast.enable_continuous_measure()
        self.log('beast_enable_continuous_measure', ret)
        return ret

    def disable_continuous_measure(self):
        '''
        Beast disable_continuous_measure function. Data will disable upload, when this function called.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('beast', "disable_continuous_measure")
        ret = self.client.beast.disable_continuous_measure()
        self.log('beast_disable_continuous_measure', ret)
        return ret

    def set_measure_mask(self, mask=0):
        '''
        Beast set signal meter measure mask.

        Args:
            mask:    int, default 0, mask bit value shown as below.

            +---------------+-------------------+
            |   mask        |       function    |
            +===============+===================+
            | bit[0:3]      | Reserved          |
            +---------------+-------------------+
            | bit[4]        | Frequency mask    |
            +---------------+-------------------+
            | bit[5]        | Duty mask         |
            +---------------+-------------------+
            | bit[6]        | Vpp mask          |
            +---------------+-------------------+
            | bit[7]        | rms mask          |
            +---------------+-------------------+

        Returns:
            string, "done", api execution successful.

        '''
        self.log('beast', "set_measure_mask({})".format(mask))
        ret = self.client.beast.set_measure_mask(mask)
        self.log("beast set_measure_mask" , ret)
        return ret

    def frequency_measure(self, duration, measure_type="LP"):
        '''
        Measure input signal frequncy and duty in a defined duration.

        Args:
            duration:      int, [1~2000], millisecond time to measure frequncy.
            measure_type:  string, ["HP", "LP"], default "LP", type of measure.

        Returns:
            list, [value, value], result value contain freq and duty, units are Hz, %.

        Examples:
            # adc_enable() and adc_disable() will operate on Pin
            # which might belongs to another i2c Mux port from on-board eeprom so put outside.
            beast.adc_enable()
            ret = beast.frequency_measure(10)
            beast.adc_disable()
            # ret will be list: [freq, duty]

        '''
        self.log('beast', "frequency_measure({} {})".format(duration, measure_type))
        ret = self.client.beast.frequency_measure(duration, measure_type)
        self.log("beast frequency_measure" , ret)
        return ret

    def vpp_measure(self, duration):
        '''
        Measure input signal vpp, max and min voltage in a defined duration.

        Args:
            duration:   int, [1~2000], millisecond time to measure vpp.

        Returns:
            list, [value, value, value], result value contain vpp, max and min voltage, unit is mV.

        Examples:
            # adc_enable() and adc_disable() will operate on Pin
            # which might belongs to another i2c Mux port from on-board eeprom so put outside.
            beast.adc_enable()
            ret = beast.vpp_measure(10)
            beast.adc_disable()
            # ret will be list: [vpp, max, min]

        '''
        self.log('beast', "vpp_measure({})".format(duration))
        ret = self.client.beast.vpp_measure(duration)
        self.log("beast vpp_measure" , ret)
        return ret

    

    def level(self):
        '''
        Get current voltage level.

        Returns:
            int, [0, 1], 0 for low level, 1 for high level.

        '''
        self.log('beast', "level")
        ret = self.client.beast.level()
        self.log('beast_level', ret)
        return ret

    def adc_enable(self):
        '''
        This function is used for enable adc output, it is an internal interface function.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('beast', "adc_enable")
        ret = self.client.beast.adc_enable()
        self.log('beast_adc_enable', ret)
        return ret

    def adc_disable(self):
        '''
        This function is used for disable adc output, it is an internal interface function.

        Returns:
            string, "done", api execution successful.

        '''
        self.log('beast', "adc_disable")
        ret = self.client.beast.adc_disable()
        self.log('beast_adc_disable', ret)
        return ret

    def read_serial_number(self):
        '''
        MIXBoard read board serial-number: (247,59)

        :example:
                            sn = beast.read_serialnumber()
                            print(sn)
        '''
        self.log('beast', "read_serial_number")
        ret = self.client.beast.read_serial_number()
        self.log('beast read_serial_number', ret)
        return ret



if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}