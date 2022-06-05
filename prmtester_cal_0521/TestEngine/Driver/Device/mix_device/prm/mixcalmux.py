# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class calmux(object):

    def __init__(self, client):
        self.client = client

    def module_init(self):
        """
        Translation Board Init cat9555 output mode
        :return: str "done"/"error";
        :example:
                self.init_baseboard_device()
        """
        return self.client.calmux.module_init()

    def relay_init(self):
        """
        Translation Board Init cat9555 output mode
        :return: str "done"/"error";
        :example:
                self.init_baseboard_device()
        """
        return self.client.calmux.relay_init()

    def set_io_switch(self, io_list):
        """
        switch 3 cat9555 io;check i2c_channel is 0
        set io switch
        :param io_list:     list,[[9,1],[10,0],[12,1]]
        :return: str "done"/"error";
        :example:
                self.set_io_switch([[9,1],[10,1],[11,0],[12,1]])
                self.set_io_switch([[9,0]])
        """
        return self.client.calmux.set_io_switch(io_list)

    def read_io_status(self, pin_id):
        """
        :param pin_id:
        :return:
        """
        return self.client.calmux.read_io_status(pin_id)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
