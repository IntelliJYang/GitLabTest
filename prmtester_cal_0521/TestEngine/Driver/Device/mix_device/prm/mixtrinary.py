# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class trinary(object):
    def __init__(self, client):
        self.client = client

    def init(self):
        return '--PASS--'

    def trinary_init(self, device, mode):
        """
        :param mode:
        :param device:
        :return:
        """
        if device == 'OQC':
            return self.client.oqc_trinary.trinary_init(mode)
        else:
            return self.client.trinary.trinary_init(mode)

    def check_swire_path(self, device):
        """
        :param device:
        :return:
        """
        if device == 'OQC':
            return self.client.oqc_trinary.one_key_all()
        else:
            return self.client.trinary.one_key_all()


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
