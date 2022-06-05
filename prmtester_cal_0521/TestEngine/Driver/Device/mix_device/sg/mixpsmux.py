# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class ps_mux(object):
    """
    class PS MUX
    """
    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def start_monitor(self, sample_rate, channel_list, monitor_time, use_avg=True):
        '''
        POWER_SEQUENCE start monitor to upload data

        Args:
            sample_rate:     int, [1000~4000000], unit Hz, Set ADC measure sample rate.
            channel_list:    list, ([x,x,...x]) x=(0-39), Need monitor channel list.
            monitor_time:    int, [1~65535], unit ms, Need monitor time.
            use_avg:         bool,                        use average value when capture the data by scope

        Returns:
            string, "done", api execution successful.

        Examples:
            power_sequence.start_monitor(1000, [0,1,2,3,4,5,6,7])

        '''
        self.log('ps_mux', "start_monitor({} {} {} {})".format(sample_rate, channel_list, monitor_time, use_avg))
        ret = self.client.ps_mux.start_monitor(sample_rate, channel_list, monitor_time, use_avg)
        self.log('ps_mux start_monitor', ret)
        return ret

    def stop_monitor(self):
        '''
        POWER_SEQUENCE stop monitor to stop upload data

        Returns:
            string, "done", api execution successful.

        Examples:
            power_sequence.stop_monitor()

        '''
        self.log('ps_mux', "stop_monitor")
        ret = self.client.ps_mux.stop_monitor()
        self.log('ps_mux_stop_monitor', ret)
        return ret

    def set_trigger_ref_voltage(self, channel, voltage):
        '''
        POWER_SEQUENCE set trigger ref voltage.

        Args:
            channel:     int/string, [0~39] | ["ALL"], Select specify channel.
            voltage:     float, [0~5000], unit mV, Set specify channel output voltage.

        Returns:
            string, "done", api execution successful.

        Examples:
            power_sequence.set_trigger_ref_voltage(3, 2000)

        '''
        self.log('ps_mux', "set_trigger_ref_voltage({} {})".format(channel, voltage))
        ret = self.client.ps_mux.set_trigger_ref_voltage(channel, voltage)
        self.log('ps_mux set_trigger_ref_voltage', ret)
        return ret

    def read_last_trigger_time(self, channel_list, mode):
        '''
        POWER_SEQUENCE get each channel last trigger time

        Args:
            channel_list:    list, ([x,x,...x]) x=(0-39).
            mode:            string, ['rise', 'fall'].

        Returns:
            string, str, ("chX=Yns,....") X: 0-39; Y: trigger time value, unit is ns.

        Examples:
            result = power_sequence.read_trigger_time([0,1,2,3,4,39],'rise')

        '''
        self.log('ps_mux', "read_last_trigger_time({} {})".format(channel_list, mode))
        ret = self.client.ps_mux.read_last_trigger_time(channel_list, mode)
        self.log('ps_mux read_last_trigger_time', ret)
        return ret

    def read_first_trigger_time(self, channel_list, mode):
        '''
        POWER_SEQUENCE get each channel first trigger time

        Args:
            channel_list:    list, ([x,x,...x]) x=(0-39).
            mode:            string, ['rise', 'fall'].

        Returns:
            string, str, ("chX=Yns,....") X: 0-39; Y: trigger time value, unit is ns.

        Examples:
            result = power_sequence.read_trigger_time([0,1,2,3,4,39],'rise')

        '''
        self.log('ps_mux', "read_first_trigger_time({} {})".format(channel_list, mode))
        ret = self.client.ps_mux.read_first_trigger_time(channel_list, mode)
        self.log('ps_mux read_first_trigger_time', ret)
        return ret

    def board_init(self):
        '''
        POWER_SEQUENCE initialize the board, need to DAC 1~5 output 4990mV voltage to Comparators,
        set the pin output

        Returns:
            string, "done", api execution successful.

        Examples:
            result = power_sequence.board_init()

        '''
        self.log('ps_mux', "board_init")
        ret = self.client.ps_mux.board_init()
        self.log('ps_mux_board_init', ret)
        return ret


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
