# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class charger(object):

    def __init__(self, client):
        self.client = client

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
        Enable charger output

        Args: voltage: int   0～4500  unit is mV
        Returns: done
        Examples:
                enable_battery_output(3800)
        '''
        return self.client.odin.enable_charger_output(voltage)

    def setCurrentLimit(self, current):
        """
        Odin current limit set

        Args:
            dac_name: str   battery/charger
            threshold: int  0～1000(for battery) 0～600(for charger)  unit is mA
        Returns:
            done
        Examples:
                set_current_limit("charger",500)
        """
        return self.client.odin.set_current_limit("charger", current)

    def voltage_measure(self):
        return self.client.odin.voltage_measure("charger")

    def current_measure(self):
        return self.client.odin.current_measure("charger")


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
