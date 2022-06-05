# -*-coding:utf-8 -*-
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


#############PRM############
class wibEEprom(object):
    """wib_eeprom"""

    def __init__(self, client):
        self.client = client

    def log(self, title, msg):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r'.format(title, msg))

    def write_id(self, device_id, timeout_ms=1000):
        '''
        EEProm write device id to eeprom

        :param      device_id: string, Max length is 16 character,'\0' do not contain and not write to eeprom.
        :example:
                    board.write_device_id("000")
        '''
        self.log("wibEEprom", "write_id({})".format(device_id))
        r = self.client.wib_eeprom.write_id(device_id, timeout_ms=timeout_ms)
        self.log("wibEEprom", "write_id ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_id", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_id", r))
        return r

    def read_id(self, timeout_ms=1000):
        '''
        EEProm read device id to eeprom

        :example:
                        board.read_device_id()
        '''
        self.log("wibEEprom", "read_id()")
        r = self.client.wib_eeprom.read_id(timeout_ms=timeout_ms)
        self.log("wibEEprom", "read_id ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_id", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_id", r))
        return r

    def write_vendor_id(self, vendor_id, timeout_ms=1000):
        '''
        MIXBoard write vendor id to eeprom

        :param         vendor_id: string, Max length is 16 character,'\0' do not contain and not write to eeprom.
        :example:
                        board.write_vendor_id("PRM")
        '''
        self.log("wibEEprom", "write_vendor_id({})".format(vendor_id))
        r = self.client.wib_eeprom.write_vendor_id(vendor_id, timeout_ms=timeout_ms)
        self.log("wibEEprom", "write_vendor_id ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_vendor_id", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_vendor_id", r))
        return r
        

    def read_vendor_id(self, timeout_ms=1000):
        '''
        MIXBoard read vendor id to eeprom

        :example:
                        board.read_vendor_id()
        '''
        self.log("wibEEprom", "read_vendor_id()")
        r = self.client.wib_eeprom.read_vendor_id(timeout_ms=timeout_ms)
        self.log("wibEEprom", "read_vendor_id ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_vendor_id", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_vendor_id", r))
        return r
       

    def write_hardware_version(self, hardware_version, timeout_ms=1000):
        '''
        MIXBoard write hardware version to eeprom

        :param         hardware_version: string, Max length is 16 character,'\0' do not contain and not write to eeprom.
        :example:
                        board.write_hardware_version("v0.1")
        '''
        self.log("wibEEprom", "write_hardware_version({})".format(hardware_version))
        r = self.client.wib_eeprom.write_hardware_version(hardware_version, timeout_ms=timeout_ms)
        self.log("wibEEprom", "write_hardware_version ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_hardware_version", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_hardware_version", r))
        return r
       

    def read_hardware_version(self, timeout_ms=1000):
        '''
        MIXBoard read hardware version from eeprom

        :example:
                            version = board.read_hardware_version()
                            print(version)
        '''
        self.log("wibEEprom", "read_hardware_version()")
        r = self.client.wib_eeprom.read_hardware_version(timeout_ms=timeout_ms)
        self.log("wibEEprom", "read_hardware_version ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_hardware_version", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_hardware_version", r))
        return r

    def read_serialnumber(self, timeout_ms=1000):
        '''
        MIXBoard read board serial-number: (247,59)

        :example:
                            sn = board.read_serialnumber()
                            print(sn)
        '''
        self.log("wibEEprom", "read_serialnumber()")
        r = self.client.wib_eeprom.read_serialnumber(timeout_ms=timeout_ms)
        self.log("wibEEprom", "read_serialnumber ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_serialnumber", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_serialnumber", r))
        return r


    def write_serialnumber(self, serialnumber, timeout_ms=1000):
        '''
        MIXBoard write serial-number to board, only use for smartgiant
        :param       serialnumber:         string, max length is 32 character,
                                                   '\0' do not contain and not write to eeprom.
        :example:
                            board.write_serialnumber("20180101")
        '''
        self.log("wibEEprom", "write_serialnumber({})".format(serialnumber))
        r = self.client.wib_eeprom.write_serialnumber(serialnumber, timeout_ms=timeout_ms)
        self.log("wibEEprom", "write_serialnumber ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_serialnumber", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_serialnumber", r))
        return r
        

    def write_calibration_date(self, date, timeout_ms=1000):
        '''
        MIXBoard write calibration data write date time

        :param         date: string, max length is 16 character,'\0' do not contain and not write to eeprom.
        :example:
                        board.write_calibration_date("C8425")
        '''
        self.log("wibEEprom", "write_calibration_date({})".format(date))
        r = self.client.wib_eeprom.write_calibration_date(date, timeout_ms=timeout_ms)
        self.log("wibEEprom", "write_calibration_date ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_calibration_date", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_calibration_date", r))
        return r
       

    def read_calibration_date(self, timeout_ms=1000):
        '''
        MIXBoard read calibration data write date time

        :example:
                            result = board.read_calibration_date()
                            print(result)
        '''
        self.log("wibEEprom", "read_calibration_date()")
        r = self.client.wib_eeprom.read_calibration_date(timeout_ms=timeout_ms)
        self.log("wibEEprom", "read_calibration_date ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_calibration_date", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_calibration_date", r))
        return r
        

    def write_calibration_cell(self, unit_index, gain, offset, threshold, timeout_ms=1000):
        '''
        MIXBoard calibration data write

        :param       unit_index:   int,    calibration unit index
        :param       gain:         float,  calibration gain
        :param       offset:       float,  calibration offset
        :param       threshold:    float,  if value < threshold, use this calibration unit data
        :example:
                            board.write_calibration_cel(0, 1.1, 0.1, 100)

        :calibration unit format:
                            Meaning:    Gain,     Offset,   threshold value, Use flag
                            Mem size:   4Bytes,   4Bytes,   4Bytes,            Byte
                            Data type:  float,    float,    float,            uint8_t
                            Formula:    Y = Gain * X  + Offset
        '''
        self.log("wibEEprom", "write_calibration_cell({})".format([unit_index, gain, offset, threshold]))
        r = self.client.wib_eeprom.write_calibration_cell(unit_index, gain, offset, threshold, timeout_ms=timeout_ms)
        self.log("wibEEprom", "write_calibration_cell ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_calibration_cell", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "write_calibration_cell", r))
        return r

    def read_calibration_cell(self, unit_index, timeout_ms=1000):
        '''
        MIXBoard read calibration data

        :param             unit_index: int, calibration unit index
        :example:
                            data = board.read_calibration_cel(0)
                            print(data)

        :calibration unit format:
                            Meaning:    Gain,     Offset,   threshold value, Use flag
                            Mem size:   4Bytes,   4Bytes,   4Bytes,            Byte
                            Data type:  float,    float,    float,            uint8_t
                            Formula:    Y = Gain * X  + Offset
        '''
        self.log("wibEEprom", "read_calibration_cell({})".format(unit_index))
        r = self.client.wib_eeprom.read_calibration_cell(unit_index, timeout_ms=timeout_ms)
        self.log("wibEEprom", "read_calibration_cell ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_calibration_cell", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "read_calibration_cell", r))
        return r
       

    def erase_calibration_cell(self, unit_index, timeout_ms=1000):
        '''
        MIXBoard erase calibration unit

        :example:
                            board.erase_calibration_cell(0)
        '''
        self.log("wibEEprom", "erase_calibration_cell({})".format(unit_index))
        r = self.client.wib_eeprom.erase_calibration_cell(unit_index, timeout_ms=timeout_ms)
        self.log("wibEEprom", "erase_calibration_cell ret={}".format(r))
        if not r:
            self.log("wibEEprom", "--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "erase_calibration_cell", r))
            raise Exception("--FAIL--_{}.{}_Response is {}".format("wib_eeprom", "erase_calibration_cell", r))
        return r
        


    def do_system_cal(self, index, value):
        if value == 0:
            return value
        if index:
            cal_info = self.read_calibration_cell(index)
            isUsed = cal_info.get("is_use")
            if isUsed:
                offset = cal_info.get("offset")
                gain = cal_info.get("gain")
                ret_vol = value*gain + offset
                self.log("calibration", "offset={}, gain={}, orignal_value={}, calibration_vaule={}".format(offset, gain, value, ret_vol))
                return ret_vol
            else:
                return value
        else:
            return value


if __name__ == '__main__':
    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    rpc_endpoint = {"requester": "tcp://169.254.1.32:7801", "receiver": "tcp://169.254.1.32:17801"}
    streaming_endpoint = {"downstream": "tcp://169.254.1.238:5555", "upstream": "tcp://169.254.1.238:15555"}
