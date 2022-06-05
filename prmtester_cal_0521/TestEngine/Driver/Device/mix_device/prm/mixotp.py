# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper

import os
import json
import sys
import csv
import traceback
import math
from time import sleep

pa = os.path.split(__file__)[0]
# reg_path = '/mix/addon/test_function/reg_info.json'
reg_path = '/Library/Station/PRM/prmtester/ThirdPartyLib/OTP/reg_info.json'

#############PRM############
class otpmanager(object):

    def __init__(self, client):
        self.client = client
        self.i2c_bus = None
        self.otp_init()


    def otp_init(self, dev_name=""):
        """

        :return: str "done"/"error";
        :example:
                
        """
        pass

    def readField(self, dev_name):
        """

        :return:
        """
        return self.client.otp_cs46l11.readField(dev_name)

    def writeRegisterByAddress(self, reg, value):
        """

        :return:
        """
        self.client.otp_cs46l11.writeRegisterByAddress(reg, value)


    def readRegisterByAddress(self, reg):
        """

        :return:
        """
        return self.client.otp_cs46l11.readRegisterByAddress(reg)

    def program_otp_internal(self, mode):
        """

        :return:
        """
        return self.client.otp_dut.otp_program(mode)

    def set_vdd_pin(self, mode):
        """

        :return:
        """
        return self.client.otp_dut.set_vdd_pin(mode)
       


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
