# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class sgpsu(object):
    """
    class PSU
    """

    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def module_init(self):
        '''
        SG2251PW01PCA module init.

        Returns:
            string, "done", api execution successful.

        Raise:
            SG2251PW01PCAException:  If volt is invalid, exception will be raised.

        Examples:
            sg2251pw01pca.reset()
        '''
        self.log('sgpsu', "module_init")
        ret = self.client.psu_board.module_init()
        self.log('sgpsu_module_init', ret)
        return ret

    def power_output(self, volt):
        '''
        SG2251PW01PCA set volt

        Args:
            volt: float, [0-20000] Set specific volt value.

        Returns:
            string, "done", api execution successful.

        Raise:
            SG2251PW01PCAException:  If volt is invalid, exception will be raised.

        Examples:
            sg2251pw01pca.power_output(10000)
        '''
        self.log('sgpsu', "power_output({})".format(volt))
        ret = self.client.psu_board.power_output(volt)
        self.log("sgpsu power_output" , ret)
        return ret

    def current_limit(self, curr):
        '''
        SG2251PW01PCA set current limit value

        Args:
            curr: float, [0-5500] Set specific current limit value.

        Returns:
            string, "done", api execution successful.

        Raise:
            SG2251PW01PCAException:  If curr is invalid, exception will be raised.

        Examples:
            sg2251pw01pca.set_current_limit(4000)
        '''
        self.log('sgpsu', "current_limit({})".format(curr))
        ret = self.client.psu_board.set_current_limit(curr)
        self.log("sgpsu current_limit" , ret)
        return ret

    def power_control(self, status):
        '''
        SG2251PW01PCA on/off power board output

        Args:
            channel: string, ['on','off'], Select specific state.

        Returns:
            string, "done", api execution successful.

        Raise:
            SG2251PW01PCAException:  If state is invalid, exception will be raised.

        Examples:
            sg2251pw01pca.power_control('on')
        '''
        self.log('sgpsu', "power_control({})".format(status))
        ret = self.client.psu_board.power_control(status)
        self.log("sgpsu power_control" , ret)
        return ret


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
