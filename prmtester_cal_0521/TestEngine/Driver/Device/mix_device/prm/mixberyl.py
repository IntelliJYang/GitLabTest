# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class beryl(object):

    def __init__(self, client):
        self.client = client

    def read(self, reg, n=1):
        '''
        reg: uint16 register
        n: uint16 number of registers to read
        '''
        return self.client.beryl.read(reg, n)

    def write(self, reg, data):
        '''
        reg: uint16 register
        data: 1x byte data to the register
        '''
        return self.client.beryl.write(reg, data)

    def dump(self, reg1=0x1200, reg2=0x120A):  # dump beryl syscfg by default
        '''
        reg1: uint16, start register
        reg2: uint16, end register
        '''
        return self.client.beryl.dump(reg1, reg2)

    def powerMode(self, mode='ACT3'):
        '''
        mode: enum 'ACT0'|'ACT1'|'ACT2'|'HOSTOFF'|'SYSOFF'|'SHIP'
        '''
        return self.client.beryl.powerMode(mode)

    def hostReset(self, switch):
        '''
        switch: enum 'on'|'off'
        '''
        return self.client.beryl.hostReset(switch)

    def forceDfu(self, switch):
        '''
        switch: enum 'on'|'off'
        '''
        return self.client.beryl.forceDfu(switch)

    def configCcadc(self, switch):
        '''
        switch: enum 'on'|'off'|'pause'
        '''
        return self.client.beryl.configCcadc(switch)

    def timestampCcadc(self):
        return self.client.beryl.timestampCcadc()

    def mfioSetConfig(self, pin, mode):
        '''
        pin: uint8<1:13>
        mode: uint16
        '''
        return self.client.beryl.mfioSetConfig(pin, mode)

    def mfioGetConfig(self, pin):
        '''
        pin: uint8<1:13>
        '''
        return self.client.beryl.mfioGetConfig(pin)

    def gpioSetConfig(self, pin, mode):
        '''
        pin: uint8<1:13>
        mode: uint16
        '''
        return self.client.beryl.gpioSetConfig(pin, mode)

    def gpioGetConfig(self, pin):
        '''
        pin: uint8<1:13>
        '''
        return self.client.beryl.gpioGetConfig(pin)

    def gpioSet(self, pin, state):
        '''
        pin: uint8<1:13>, mfio
        state:enum<0|1>
        '''
        return self.client.beryl.gpioSet(pin, state)

    def gpioGet(self, pin):
        '''
        pin: uint8<1:13>
        '''
        return self.client.beryl.gpioGet(pin)

    def readResetcode(self):
        return self.client.beryl.readResetcode()

    def testMode(self, switch):
        '''
        switch: enum 'on'|'off'
        '''
        return self.client.beryl.testMode(switch)

    def gpadcReadValue(self, agent, channel):
        '''
        agent: enum 'a0'|'a1'
        channel: int8 <1-128>
                 1: VCHG
                 2: VMID
                 3: VDD_MAIN
                 5: VBAT
                 10: VBUCK0
                 11: VBUCK1
                 12: VBUCK2
                 13: VBUCK3
                 20: VLDO0
                 21: VLDO1
                 22: VLDO2
                 23: VLDO3
                 65: TCAL
                 69: NTC_BATT
                 90: AMUXIN0
                 91: AMUXIN1
                 92: AMUXIN2
                 93: AMUXIN3
                 94: AMUXIN4
                 95: AMUXIN5
                 96: AMUXIN6
                 97: AMUXIN7
        '''
        return self.client.beryl.gpadcReadValue(agent, channel)

    def gpadcReadValueSS(self, agent, channel, n=30):
        '''
        Generate statistical results like mean and std
        agent: enum 'a0'|'a1'
        channel: int8 <1-128>
                 1: VCHG
                 2: VMID
                 3: VDD_MAIN
                 5: VBAT
                 10: VBUCK0
                 11: VBUCK1
                 12: VBUCK2
                 13: VBUCK3
                 20: VLDO0
                 21: VLDO1
                 22: VLDO2
                 23: VLDO3
                 65: TCAL
                 69: NTC_BATT
                 90: AMUXIN0
                 91: AMUXIN1
                 92: AMUXIN2
                 93: AMUXIN3
                 94: AMUXIN4
                 95: AMUXIN5
                 96: AMUXIN6
                 97: AMUXIN7
        n: int8 <1-128>
        '''
        return self.client.beryl.gpadcReadValueSS(agent, channel, n)

    def chargerMode(self, mode):
        '''
        mode: enum 'disabled'|'fast'|'slow'|'auto'
        '''
        return self.client.beryl.chargerMode(mode)

    def readOtp(self):
        '''

        :return:
        '''
        return self.client.beryl.readOtp()


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
