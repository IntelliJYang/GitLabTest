# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class adgarray(object):
    """adgarray"""

    def __init__(self, client):
        self.client = client

    def set_io_switch(self, io_list):
        """
        switch 3 adg2128 io
        set io switch
        :param io_list:     list, eg: [[1,2,0], [3,4,1] means X1Y2=0 ,X3Y4=1.
        :return: str "done"/"error";
        :example:
                self.set_io_switch([[1,2,0], [3,4,1]])
                self.set_io_switch([[1,2,0]])
        """
        return self.client.adgarray.set_io_switch(io_list)

    def switch_on(self, x_num, y_num):
        """
        example:swithc_on(35, 0)
                swithc_on(1, 1)

        """
        return self.client.adgarray.switch_on(x_num, y_num)

    def switch_off(self, x_num, y_num):
        """
        example:swithc_off(35, 0)
                swithc_off(1, 1)

        """
        return self.client.adgarray.switch_off(x_num, y_num)

    def reset(self):
        """

        :return:
        """
        return self.client.adgarray.reset()


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.33:7801', 'receiver': 'tcp://169.254.1.33:17801'}
    client = RPCClientWrapper(endpoint)
    print client.adgarray.set_io_switch([[0, 0, 1]])
