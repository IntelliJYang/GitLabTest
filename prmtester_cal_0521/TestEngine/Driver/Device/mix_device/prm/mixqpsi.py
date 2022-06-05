# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class qspi(object):
    """fwdl"""

    def __init__(self, client):
        self.client = client

    def program_id(self, chip, timeout_ms=50000):
        '''
        Read chip id.

        :param chip:    str,        chip name
        :return:        str,        result of read id
        :raises FWDLException:      Raise exception when read id failed.
        :example:
                        result = fwdl.program_id("stm32l4xx")
                        print(result)
        '''
        return self.client.fwdl.program_id(chip, timeout_ms=timeout_ms)

    def program_erase(self, chip, target_addr=None, size=None, timeout_ms=50000):
        '''
        Erase dut's flash.

        :param chip:        str,        chip name
        :param target_addr: int,        Start position of Dut's flash which will be erase,
                                        if None, it will erase the whole flash.
        :param size:        int,        Data length will be erase.
        :return:            str,        result of erase
        :raises FWDLException:          Raise exception when erase failed.
        :example:
                        print fwdl.program_erase("stm32l4xx")
        '''
        return self.client.fwdl.program_erase(chip, target_addr, size, timeout_ms=timeout_ms)

    def program_auto(self, chip, firmware=None, target_addr=None, timeout_ms=50000):
        '''
        If firmware is None, the function as same as program_id.
        Otherwise the function will program dut's flash after erase. And faster than program.

        :param chip:        str,        chip name
        :param firmware:    str,        Fullname with path and firmware name.
        :param target_addr: int,        Start position of Dut's flash which will be erase and program
        :param return:      str,        result of program_auto
        :raises FWDLException:          Raise exception when firmware does not exist or failed.
        :example:
                        print fwdl.program_auto("at25s128", "/mix/out.bin", 0x1000)
        '''
        return self.client.fwdl.program_auto(chip, firmware, target_addr, timeout_ms=timeout_ms)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
