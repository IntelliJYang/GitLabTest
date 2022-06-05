# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class tmp1117(object):
    """sensor"""

    def __init__(self, client):
        self.client = client

    def readID(self):
        """
        Read Tmp 1117 ID
        :return:
        """
        return self.client.sensor.readID()

    def osRead(self):
        """
        Read Tempture
        :return:
        """
        return self.client.sensor.osRead()


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
