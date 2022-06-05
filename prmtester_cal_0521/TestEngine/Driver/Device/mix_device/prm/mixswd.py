# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class swd(object):
    """swd"""

    def __init__(self, client):
        self.client = client

    def program_mcu(self, target_device, fw_binary, md5, offset, verify=True, timeout_ms=50000):
        """
        program the mcu using the apple SWD programmer.

        :param target_device    str,    Device family for the chip
        :param fw_binary        str,    Firmware to download to the chip
        :param md5              str,    MD5 of the programming file.  If MD5 does not match, programming
                                        will not proceed.
        :param offset           int,    Device address offset to place firmware
        :param verify           bool,   (Optional) whether to perform verify after programming.  Default=True.
        :param timeout_ms       int,    (Required if call through RPC).  Milliseconds for RPC to wait before
                                        declaring call timeout.

        :return output          str,    The stdout of the programming process.
        :
        :example:   program_mcu("ccg2", "test_fw.bin", "d21127d234b5d22231d80e99b355248a", 0x00000000, timeout_ms=20000)
        More info: https://confluence.sd.apple.com/display/SMT/SWD+Programmer
        """
        return self.client.swd.program_mcu(target_device, fw_binary, md5, offset, verify, timeout_ms=timeout_ms)

    def mass_erase(self, target_device, banks, timeout_ms=50000):
        """
        Perform mass erase to the given 'banks' list.
        :param target_device   str,        Device family for the chip
        :param banks           list[int],  Bank indexes to be mass-erased.

        :example:   mass_erase("stm32f4x", [0,1])
        """
        return self.client.swd.mass_erase(target_device, banks, timeout_ms=timeout_ms)

    def verify(self, target_device, fw_binary, md5, offset, timeout_ms=50000):
        """
        Verify checksum or binary compare with a given image.
        The image itself will be first md5 verified before verifying against the device.
        This will first attempt a comparison using a CRC checksum, if this fails it will try a binary compare.

        :param target_device    str,    Device family for the chip
        :param fw_binary        str,    Firmware to download to the chip
        :param md5              str,    MD5 of the programming file.  If MD5 does not match, programming
                                        will not proceed.
        :param offset           int,    Device address offset to start.
        :param timeout_ms       int,    (Required if call through RPC).  Milliseconds for RPC to wait before
                                        declaring call timeout.

        :return output          str,    The stdout of the programming process.
        :
        :example:   verify("ccg2", "test_fw.bin", "d21127d234b5d22231d80e99b355248a", 0x00000000, timeout_ms=20000)
        """
        return self.client.swd.verify(target_device, fw_binary, md5, offset, timeout_ms=timeout_ms)


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
