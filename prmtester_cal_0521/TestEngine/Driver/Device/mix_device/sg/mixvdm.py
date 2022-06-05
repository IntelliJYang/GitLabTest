# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class vdm(object):
    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def module_init(self):
        self.log('vmd', "module_init")
        ret = self.client.vdm_board.module_init()
        self.log('vmd_module_init', ret)

    def set_source_capabilities(self, pdo, source, voltage, current_limit):
        self.log('vmd', "set_source_capabilities({} {} {} {})".format(pdo, source, voltage, current_limit))
        ret = self.client.vdm_board.set_source_capabilities(pdo, source, voltage, current_limit)
        self.log('vmd set_source_capabilities', ret)

    def change_source_pdo_count(self, pdo_count):
        self.log('vmd', "change_source_pdo_count({})".format(pdo_count))
        ret = self.client.vdm_board.change_source_pdo_count(pdo_count)
        self.log("vmd change_source_pdo_count" , ret)

    def write_register_by_address(self, register_address, field_name, value):
        self.log('vmd', "write_register_by_address({} {} {})".format(register_address,field_name, value ))
        ret = self.client.vdm_board.write_register_by_address(register_address, field_name, value)
        self.log('vmd write_register_by_address', ret)

    def read_all_registers(self):
        self.log('vmd', "read_all_registers")
        ret = self.client.vdm_board.read_all_registers()
        self.log('vmd read_all_registers', ret)
        return ret

if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}

