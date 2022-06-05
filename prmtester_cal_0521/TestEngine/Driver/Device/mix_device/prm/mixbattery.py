# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class battery(object):

    def __init__(self, client):
        self.client = client
        self.measure_path = dict()

    def on(self, voltage, current=500):
        self.setOutput(voltage)
        self.setCurrentLimit(current)
        return True

    def off(self):
        self.client.odin.disable_battery_output()
        self.setCurrentLimit(0)
        return True

    def setOutput(self, voltage):
        '''
        Enable battery output

        Args: voltage: int   0～4500  unit is mV
        Returns: done
        Examples:
                enable_battery_output(3800)
        '''
        return self.client.odin.enable_battery_output(voltage)

    def setCurrentLimit(self, current):
        """
        Odin current limit set

        Args:
            dac_name: str   battery/charger
            threshold: int  0～1000(for battery) 0～600(for charger)  unit is mA
        Returns:
            done
        Examples:
                set_current_limit("battery",500)
        """
        return self.client.odin.set_current_limit("battery", current)

    def set_measure_path(self, channel, scope):
        """
        Battery set measure path

        :param ch_type: str   battery/charger/ex_voltage
        :param channel: str   ch0/ch1/ex_voltage, ch0 for voltage channel, ch1 for current channel
        :param scope: str (50ua/500ua/5ma/50ma/500ma/650ma/5mv/50mv/500mv/5000mv)
        :return: done
        :example:
                set_measure_path("battery","ch0","5000mv")
                set_measure_path("battery","ch1","500ma")
        """
        self.measure_path = dict()
        self.client.odin.set_measure_path("battery", channel, scope)
        self.measure_path[channel] = scope
        print "*"*100
        print self.measure_path
        print "*"*100

    def voltage_measure(self, scope="5000mv"):
        channel = "ch0"
        _scope = self.measure_path.get(channel)
        if not _scope:
            self.set_measure_path(channel, scope)
        else:
            if _scope != scope:
                self.set_measure_path(channel, scope)
        return self.client.odin.voltage_measure("battery")

    def current_measure(self, scope="500ma"):
        channel = "ch1"
        _scope = self.measure_path.get(channel)
        if not _scope:
            self.set_measure_path(channel, scope)
        else:
            if _scope != scope:
                self.set_measure_path(channel, scope)
        result = self.client.odin.current_measure("battery")
        return result

    def voltage_sample(self, points, raw=0, sample_rate=None, scope="5000mv"):
        """
        Battery get continuous voltage measure result

        Args:
            points: int (1~512)
            raw: bool True/False
            sample_rate: int 5/10/20/100/200/500/1000/2500/5000/10000/25000/50000/125000/250000
        Returns:
            dict   the dict contains rms,avr,max,min,vpp,result
        Examples:
                result = voltage_sample(512,True,10000)
        """
        channel = "ch0"
        if not self.measure_path or self.measure_path[channel] != scope:
            self.set_measure_path(channel, scope)
        return self.client.odin.voltage_sample(points, raw, sample_rate)

    def current_sample(self, points, raw=0, sample_rate=None, scope="500ma"):
        """
        Battery get continuous current measure result

        Args:
            points: int (1~512)
            raw: bool True/False
            sample_rate: int 5/10/20/100/200/500/1000/2500/5000/10000/25000/50000/125000/250000
        Returns:
            dict   the dict contains rms,avr,max,min,vpp,result
        Examples:
                result = current_sample(512,True,10000)
        """
        channel = "ch1"
        if not self.measure_path or self.measure_path[channel] != scope:
            self.set_measure_path(channel, scope)
        return self.client.odin.current_sample(points, raw, sample_rate)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
