# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class aidslave(object):

    def __init__(self, client):
        self.client = client
        # self.aid_init()


    def aid_init(self, dev_name="aid1"):
        """

        :return: str "done"/"error";
        :example:
                
        """
        if dev_name == "aid0":
            return self.client.aid_slave_0.aid_reset()
        else:
            return self.client.aid_slave_1.aid_reset()

    def aid_set_response(self, dev_name, response=None):
        """

        :return:
        """
        if response == None:
            response = [0, 242, 1, 0, 13, 0]
            # response = [0, 1, 2, 3, 4, 5]
        if dev_name == "aid0":
            return self.client.aid_slave_0.aid_set_response(response)
        else:
            # return self.client.aid_slave_1.aid_set_response(0x74,response)
            return self.client.aid_slave_1.aid_set_response(response)

    def aid_reset(self, dev_name):
        """

        :return:
        """
        if dev_name == "aid0":
            return self.client.aid_slave_0.aid_reset()
        else:
            return self.client.aid_slave_1.aid_reset()

    def aid_handle_command(self, dev_name):
        """

        :return:
        """
        if dev_name == "aid0":
            return self.client.aid_slave_0.aid_handle_command()
        else:
            return self.client.aid_slave_1.aid_handle_command()


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
