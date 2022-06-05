# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class pcf8574(object):

    def __init__(self, client):
        self.client = client

    def set_pin(self, pin_id, level):
        '''
        Set the level of PCF8574 pin

        Args:
            pin_id:   int, [0~7],   Pin id you can choose of PCF8574.
            level:    int, [0, 1],   set pin level like 0 or 1.

        Examples:
            pcf8574.set_pin(5,1)
        '''
        return self.client.pcf8574.set_pin(pin_id, level)

    def get_pin(self, pin_id):
        '''
        Get the level of PCF8574 pin

        Args:
            pin_id:   int, [0~7],   Pin id you can choose of PCF8574.

        Returns:
            int, [0, 1].

        Examples:
            pcf8574.get_pin(12)

        '''
        return self.client.pcf8574.get_pin(pin_id)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
