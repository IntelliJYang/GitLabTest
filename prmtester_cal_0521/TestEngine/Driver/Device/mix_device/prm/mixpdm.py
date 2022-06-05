# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class pdm(object):
    """pdm"""

    def __init__(self, client):
        self.client = client

    def pdm_output_enable(self, frequency, dbfs, samplerate=1000000):
        '''
        Output PDM

        :param:   frequency    int eg:[10000]
        :param:   dbfs         int eg:[10]
        :param:   samplerate   int eg:[1000000]
        :return:  bool
        :example: J420fctfunction.pdm_output_enable(10000,10,1000000)
        '''
        return self.client.pdm.pdm_output_enable(frequency, dbfs, samplerate)

    def pdm_output_disable(self):
        '''
        Disable PDM

        :return:  bool
        :example: J420fctfunction.pdm_output_disable()
        '''
        return self.client.pdm.pdm_output_disable()


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
