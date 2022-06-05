# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class dac(object):

    def __init__(self, client):
        self.client = client

    def module_init(self):
        """

        :return:
        """
        return self.client.dac.module_init()

    def set_dac_output(self, index, channel, voltage):
        """

        :param index:
        :param channel:
        :param voltage:
        :return:
        """

        return self.client.dac.set_dac_output(index, channel, voltage)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
