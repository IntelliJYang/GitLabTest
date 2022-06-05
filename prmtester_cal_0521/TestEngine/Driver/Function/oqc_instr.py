
import pyvisa as visa
import time
import serial
import telnetlib
import numpy as np


class Inst_33522A(object):
    def __init__(self):
        self.rm = None
        self.objInst = None

    def open(self, resource_name):
        try:
            self.rm = visa.ResourceManager()
            self.objInst = self.rm.open_resource(resource_name)
        except Exception as e:
            print e
            self.objInst = None
            return False
        return True

    def query(self, cmd):
        r1, r2 = self.objInst.query(cmd)
        if "{}".format(r2) == "0":
            return True
        else:
            return False

    def write(self, cmd):
        r1, r2 = self.objInst.write(cmd)
        time.sleep(0.001)
        if "{}".format(r2) == "0":
            return True
        else:
            return False

    def close(self):
        self.objInst.close()
        self.rm.close()
        return True

    def reset(self):
        return self.write("*RST")

    def set_output_load(self, channel, load):
        ret = True
        ret &= self.write("OUTP{}:LOAD {}".format(channel, load))
        return ret

    def enable_output(self, channel):
        ret = True
        ret &= self.write("OUTP{} ON".format(channel))
        return ret

    def disable_output(self, channel):
        ret = True
        ret &= self.write("OUTP{} OFF".format(channel))
        return ret

    def apply_squ(self, channel, freq, volt, offset):
        ret = True
        ret &= self.set_output_load(channel, "INF")
        ret &= self.write("SOUR{}:FUNC SQU".format(channel))
        ret &= self.write("SOUR{}:FREQ {}".format(channel, freq))
        ret &= self.write("SOUR{}:VOLT {}".format(channel, volt))
        ret &= self.write("SOUR{}:VOLT:OFFS {}".format(channel, offset))
        return ret

    def apply_sin(self, channel, freq, volt, offset, phase=0):
        ret = True
        ret &= self.set_output_load(channel, "INF")
        ret &= self.write("SOUR{}:FUNC SIN".format(channel))
        ret &= self.write("SOUR{}:FREQ {}".format(channel, freq))
        ret &= self.write("SOUR{}:VOLT {}".format(channel, volt))
        ret &= self.write("SOUR{}:VOLT:OFFS {}".format(channel, offset))
        ret &= self.write("SOUR{}:PHAS {}".format(channel, phase))
        return ret

    def sync_channel(self):
        return self.write("PHAS:SYNC")


class Inst_63600(object):
    def __init__(self):
        self.rm = None
        self.objInst = None

    def open(self, resource_name):
        try:
            self.rm = visa.ResourceManager()
            self.objInst = self.rm.open_resource(resource_name)
            self.objInst.write('LOAD ON\n')
            self.objInst.write('CHAN:ACT ON\n')
        except Exception as e:
            print e
            self.objInst = None
            return False
        return True

    def write(self, cmd):
        C = str(int(cmd)/1000.0)
        print type(C)
        self.objInst.write('CURR:STAT:L1 {}A\n'.format(C))
        time.sleep(0.1)
        


    def close(self):
        try:
            self.objInst.close()
            self.rm.close()
        except Exception as e:
            print e
            self.objInst = None
            return False
        return True

    def loadon(self):
        self.objInst.write('LOAD ON\n')

    def loadoff(self):
        self.objInst.write('LOAD OFF\n')
        


class Inst_2400(object):
    def __init__(self):
        self.objSerial = None

    def open(self, uart_path, baud_rate, timeout=0.5):
        try:
            self.objSerial = serial.Serial(uart_path, baud_rate, timeout=timeout)
        except Exception as e:
            print e
            self.objSerial = None
            return False
        return True

    def close(self):
        if self.objSerial:
            self.objSerial.close()
        return True

    def write(self, cmd, promt="\n"):
        if self.objSerial:
            self.objSerial.write(cmd+promt)

    def query(self, cmd, promt="\n"):
        result = ''
        if self.objSerial:
            print cmd+promt
            self.objSerial.write(cmd+promt)
            time.sleep(0.1)
            result = self.objSerial.readlines()
        return result

    def reset(self):
        self.write("*RST")

    def set_4_wire(self):
        self.write(":SYST:RSEN ON")

    def set_2_wire(self):
        self.write(":SYST:RSEN OFF")

    def set_output(self, mode, level, output_range):
        # mode in ["VOLT", "CURR"]
        self.write(":SOUR:FUNC {}".format(mode))
        self.write(":SOUR:{}:MODE FIXED".format(mode))
        self.write(":SOUR:{}:RANG {}".format(mode, output_range))
        self.write(":SOUR:{}:LEV {}".format(mode, level))

    def set_read(self, mode, compliance, measure_range):
        # mode in ["VOLT", "CURR"]
        self.write(":SENS:{}:PROT {}".format(mode, compliance))
        self.write(":SENS:FUNC \"{}\"".format(mode))
        self.write(":SENS:{}:RANG {}".format(mode, measure_range))

    def enable_output(self):
        self.write(":OUTP ON")

    def disable_output(self):
        self.write(":OUTP OFF")

    def read(self):
        ret = self.query(":READ?")
        if ret and len(ret) > 0 and len(ret[0].split(',')) > 2:
            return "0", ret[0].split(',')[0], ret[0].split(',')[1]
        else:
            return "1", "", ""

    def set_const_curr_mode(self, curr, prot=3.2):
        """
        set output curr level and measure one time

        :param curr: float, current level,A
        :param prot: float, voltage level,V
        :return:
        """
        try:
            self.write(":SOUR:FUNC CURR")
            self.write(":SOUR:CURR:LEV {}".format(curr))
            self.write(":SENS:VOLT:PROT {}".format(prot))
        except Exception:
            raise

    def current_period(self):
        self.write("*RST")
        self.write(":SENS:FUNC:CONC OFF")
        self.write(":SOUR:FUNC VOLT")
        self.write(":SENS:FUNC CURR:DC")
        self.write(":SENS:CURR:PROT 0.1")
        self.write(":SOUR:VOLT:MODE LIST")
        self.write(":SOUR:LIST:VOLT 3,1,3,1")
        self.write(":TRIG:COUN 50")
        self.write(":SOUR:DEL 0.125")
        self.write(":OUTP ON")
        self.write(":READ?")


class Inst_Telnet(object):
    def __init__(self):
        self.telnet = None

    def open(self, ip, port):
        try:
            self.telnet = telnetlib.Telnet(ip, port)
            print self.telnet
        except Exception as e:
            print e
            self.telnet = None
            return False
        return True

    def close(self):
        self.telnet.close()
        return True

    def write(self, cmd, promt="\r\n"):
        if self.telnet:
            self.telnet.write(cmd+promt)

    def read(self):
        if self.telnet:
            return self.telnet.read_some()

    def query(self, cmd, promt="\r\n"):
        self.telnet.write(cmd+promt)
        time.sleep(0.01)
        ret = self.telnet.read_some()
        return ret

class Inst_34461A(object):
    def __init__(self):
        self.rm = None
        self.objInst = None

    def open(self, resource_name):
        try:
            if self.rm:
                self.close()
            self.rm = visa.ResourceManager()
            self.objInst = self.rm.open_resource(resource_name)
        except Exception as e:
            print e
            self.objInst = None
            return False
        return True

    def query(self, cmd):
        return self.objInst.query(cmd)


    def write(self, cmd):
        r1, r2 = self.objInst.write(cmd)
        time.sleep(0.001)
        if "{}".format(r2) == "0":
            return True
        else:
            return False

    def close(self):
        #if self.objInst:
        #    self.objInst.close()
        self.rm.close()
        self.objInst = None
        self.rm = None
        return True

    def reset(self):
        return self.write("*RST")

    def read_voltage(self, mode, measure_range):
        self.write("CONF:VOLT:{}".format(mode))
        self.write("VOLT:{}:RANG {}".format(mode, measure_range))
        # self.write("VOLT:DC:NPLC 10")
        # self.write("VOLT:APER:ENAB ON")
        # self.write("VOLT:DC:APER 100E-03")
        return self.query("READ?")

    def read_voltage_times(self, mode, measure_range, loop_times=1, nplc=10):
        self.write("CONF:VOLT:{}".format(mode))
        self.write("VOLT:{}:RANG {}".format(mode, measure_range))
        if nplc == 1:
            self.write("VOLT:DC:NPLC 1")
        if loop_times == 1:
            return self.query("READ?")
        else:
            self.write("SAMP:COUN {}".format(loop_times))
            res = self.query("READ?")
            sum = 0
            for data in res.split(','):
                sum = sum + float(data)
            return str(sum / loop_times)

    def read_voltage_multi_times(self, mode, mes_range, loop_times, nplc): # 0.02us*1000=20ms
        self.write("CONF:VOLT:{}".format(mode))
        self.write("VOLT:{}:RANG {}".format(mode, mes_range)) # "VOLT:DC:RANG 10"
        self.write("VOLT:DC:NPLC {}".format(nplc))
        self.write("SAMP:COUN {}".format(loop_times))
        result = self.query("READ?")
        voltage_list = map(float, result.split(","))
        # max_voltage = np.max(voltage_list)
        average_voltage = np.average(voltage_list)
        return float(average_voltage), voltage_list

    def read_current(self, curr_range=1):
        self.write("CONF:CURR:{} {},0.001".format("DC", curr_range))
        self.write("CURR:DC:NPLC 10")
        return self.query("READ?")

    def read_current_times(self, curr_range=1, loop_times=1, nplc=10):
        self.write("CONF:CURR:{} {},0.001".format("DC", curr_range))
        if nplc == 1:
            self.write("VOLT:DC:NPLC 1")
        else:
            self.write("CURR:DC:NPLC 10")
        if loop_times == 1:
            return self.query("READ?")
        else:
            self.write("SAMP:COUN {}".format(loop_times))
            res = self.query("READ?")
            sum = 0
            for data in res.split(','):
                sum = sum + float(data)
            return str(sum/loop_times)

    def read_current_multi_times(self, mes_range, loop_times, nplc):
        # cmd same as "CONF:CURR:DC 1,0.001"
        self.write("CONF:CURR:{} {},0.001".format("DC", mes_range))
        time.sleep(0.02)
        self.write("CURR:DC:NPLC {}".format(nplc))
        self.write("SAMP:COUN {}".format(loop_times))
        time.sleep(0.02)
        result = self.query("READ?")
        current_list = map(float, result.split(","))
        average_curr = np.average(current_list)
        return float(average_curr), current_list



class Test_Serial(object):
    def __init__(self):
        self.objSerial = None

    def open(self, uart_path, baud_rate, timeout=0.5):
        try:
            self.objSerial = serial.Serial(uart_path, baud_rate, timeout=timeout)
        except Exception as e:
            print e
            self.objSerial = None
            return False
        return True

    def close(self):
        if self.objSerial:
            self.objSerial.close()
        return True

    def write(self, cmd, promt="\n"):
        if self.objSerial:
            self.objSerial.write(cmd+promt)

    def query(self, cmd, promt="\n"):
        result = ''
        if self.objSerial:
            self.objSerial.write(cmd+promt)
            result = self.objSerial.read(len(cmd+promt))
        return result

    def random_str(self, count):
        import random, string
        return ''.join(random.sample(string.ascii_letters + string.digits, count))

    def self_test(self, path, baud, parity="N", count=1):
        iPass = 0
        time_list = []
        self.open(path, baud, 1)
        if parity == "N":
            self.objSerial.parity = serial.PARITY_NONE
        elif parity == "O":
            self.objSerial.parity = serial.PARITY_ODD
        elif parity == "E":
            self.objSerial.parity = serial.PARITY_EVEN
        else:
            self.objSerial.parity = serial.PARITY_NONE

        from datetime import datetime
        for i in range(count):
            random_cmd = self.random_str(50) + self.random_str(50)
            eof_str = ""
            time_start = datetime.now()
            ret = self.query(random_cmd, eof_str)
            time_spend = (datetime.now() - time_start).total_seconds()
            time_list.append(time_spend)
            print ret
            if random_cmd + eof_str == ret:
                iPass += 1
        self.close()
        return iPass, time_list


if __name__ == '__main__':

    instr_63600 = Inst_63600()
    instr_63600.open("USB0::0x0A69::0x083E::636002001382::INSTR")
    time.sleep(1)
    instr_63600.loadon()
    print "load on 63600"
    instr_63600.write(0)
    time.sleep(1)
    print "instr_63600 set 0"
    instr_63600.write(10)
    time.sleep(1)
    print "instr_63600.write(10)"
    # cc = Inst_63600()
    # cc.open('USB0::0x0A69::0x083E::636002001382::INSTR')
    # cc.write(200)



    # pass
    # Inst_2400
    # import numpy as np
    # obj = Test_Serial()
    # print "921600:"
    # result, data = obj.self_test("/dev/cu.usbserial-14110", 921600, "N", 10)
    # print result
    # print np.max(data)*1000
    # print np.min(data)
    # print np.average(data)
    # print np.std(data)
    # print np.median(data)

    # print "460800:"
    # print obj.self_test("/dev/cu.usbserial-14310", 460800, "N", 10)
    # print "230400:"
    # print obj.self_test("/dev/cu.usbserial-14310", 230400, "N", 10)
    # print "115200:"
    # print obj.self_test("/dev/cu.usbserial-14310", 115200, "N", 10)
    # print "9600:"
    # print obj.self_test("/dev/cu.usbserial-14310", 9600, "N", 10)
    # print obj.self_test("/dev/cu.usbserial-14110", 9600, "O", 10)
    # print obj.self_test("/dev/cu.usbserial-14110", 9600, "E", 10)

    # # ==================================================
    # Inst_34460A
    # obj = Inst_34461A()

    # obj.open("USB0::0x2A8D::0x1301::MY59011732::INSTR")
    # obj.reset()
    # print time.time(), "=="
    # val = obj.read_voltage_times("DC", 100, 3, 10)
    # for i in range (1,3):

        #print time.time(), "=="
        # val = obj.read_voltage_times("DC", 10, 1, 10)
        # print float(val)
        # time.sleep(0.1)

    # val1 = obj.read_current_times(1)
    # print float(val1)
    # obj.close()

    # # ==================================================
    # # Inst_33522A
    # obj = Inst_33522A()
    # obj.open("USB0::0x0957::0x2307::MY50003291::INSTR")
    # obj.reset()
    # obj.apply_sin(1, 100, 1.600, 0, 0)
    # obj.enable_output(1)
    # obj.apply_sin(2, 100, 1.600, 0, 180)
    # obj.enable_output(2)
    # obj.sync_channel()
    # time.sleep(200)
    # obj.disable_output(1)
    # obj.disable_output(2)
    # obj.close()

    # # ==================================================
    # Inst_2400
    # obj = Inst_2400()
    # obj.open("/dev/cu.usbserial", 9600, 0.2)
    # obj.current_period()
    #
    # # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # # set CV, read current
    # obj.reset()
    # obj.set_output("VOLT", 20, 10)
    # obj.set_read("CURR", 0.01, 0.01)
    # obj.enable_output()
    # time.sleep(1)
    # result, volt, curr = obj.read()
    # if result == "0":
    #     print "volt={}. curr={}".format(float(volt), float(curr))
    # else:
    #     print "read fail"
    # obj.disable_output()

    # # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # # set CC, read voltage
    # obj.reset()
    # obj.set_output("CURR", -0.000001, -0.001)
    # obj.set_read("VOLT", 5, 20)
    # obj.enable_output()
    # time.sleep(1)
    # result, volt, curr = obj.read()
    # if result == "0":
    #     print "volt={}. curr={}".format(float(volt), float(curr))
    # else:
    #     print "read fail"
    # # obj.disable_output()

    # # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # # DMM directly
    # result, volt, curr = obj.read()
    # if result == "0":
    #     print "volt={}. curr={}".format(float(volt), float(curr))
    # else:
    #     print "read fail"
    # obj.close()

    # # ==================================================
    # # OQC_Board
    # obj = Inst_Telnet()
    # obj.open("169.254.1.67", 7600)
    # res =  obj.query(">FPC_ANALOG_MANDO_CIN3(off)")
    # print res
    # print obj.query(">QSPI_SOC_BI_FLASH_DQ1(on)")
    # time.sleep(0.5)
    # print obj.query(">QSPI_SOC_BI_FLASH_DQ1(off)")
    # obj.close()
