# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############SG############
class sguart(object):
    def __init__(self, client):
        self.client = client

    def log(self,title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def uart_write(self, uart_number, write_data):
        '''
        uart 115200 boardrate write string.
        :param uart_num: int, the uart number.
        :param data: string, write data string.
        :returns: string,"done"
        :example: uart.write(1,"[SV]")
        '''
        self.log('sguart', "uart_write({} {})".format(uart_number, write_data))
        write_data = [ord(c) for c in write_data] + [0x0D, 0x0A]
        ret = self.client.uart.write_hex(uart_number, write_data)
        self.log('sguart_uart_write', ret)

    def uart_read(self, uart_number, read_size):
        '''
        uart 115200 read data.
        :param uart_num: int, the uart number.
        :param size:    int, read data size.
        :returns:       string data.
        :example:       uart.read(1,10)
        '''
        self.log('sguart', "uart_read({} {})".format(uart_number, read_size))
        data = self.client.uart.read_hex(uart_number, read_size)
        try:
            ret = ''.join([chr(c) for c in data])
            self.log('uart_read', ret)

        except Exception as e:
            print e
        return ret


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}

