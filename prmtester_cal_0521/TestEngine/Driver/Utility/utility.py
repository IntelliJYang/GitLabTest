import os, sys
from ctypes import *
import regex as re
import struct
import subprocess
import fcntl
import paramiko

"""
Parse reply by cmd

"""

class scaleConvert(object):
    """docstring for scaleConvert"""

    def __init__(self):
        super(scaleConvert, self).__init__()
        # self.arg = arg
        self.base = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 6)]

    # bin2dec

    def bin2dec(self, string_num):
        return str(int(string_num, 2))

    # hex2dec

    def hex2dec(self, string_num):
        return str(int(string_num.upper(), 16))

    # dec2bin

    def dec2bin(self, string_num):
        num = int(string_num)
        mid = []
        while True:
            if num == 0: break
            num, rem = divmod(num, 2)
            mid.append(self.base[rem])

        return ''.join([str(x) for x in mid[::-1]])

    # dec2hex

    def dec2hex(self, string_num):
        num = int(string_num)
        mid = []
        while True:
            if num == 0: break
            num, rem = divmod(num, 16)
            mid.append(self.base[rem])

        return ''.join([str(x) for x in mid[::-1]])

    # hex2tobin

    def hex2bin(self, string_num):
        return self.dec2bin(self.hex2dec(string_num.upper()))

    # bin2hex

    def bin2hex(self, string_num):
        return self.dec2hex(self.bin2dec(string_num))

    # print hex2bin('0xFFFFFEFF')

    def hex2float(self, string_num):
        i = int(string_num, 16)
        cp = pointer(c_int(i))
        fp = cast(cp, POINTER(c_float))
        return fp.contents.value

    def float2hex(self, string_num):
        return struct.pack(">f", float(string_num)).encode('hex')

    @classmethod
    def change(self, n,base):
        s = []
        if n == 0:
            return '0'
        while n > 0:
            rest = n % base
            s.append(rest)

            n = n // base
        s.reverse()

        result_str = ''

        for i in range(len(s)):
            result_str = result_str + str(s[i])

        return result_str



class Unit(object):
    unit_exponents = {'UV': -6, 'MV': -3, 'V': 0, "NA":-9, 'UA': -6, 'MA': -3, 'A': 0, 'HZ': 0, 'KHZ': 3, 'MHZ': 6, 'GHZ': 9,
                      'OHM': 0, 'S': 0, 'MS': -3, 'US': -6, 'NS': -9, 'VPP': 0, 'MVPP': -3}

    VOLT, CURR, RES, FREQ = xrange(4)

    @staticmethod
    def convert_unit(value, from_unit, to_unit):
        if not from_unit or not to_unit:
            return False, "Units are not specified but are required."
        from_u = Unit.unit_exponents.get(from_unit.upper())
        to_u = Unit.unit_exponents.get(to_unit.upper())
        if type(value) is str:
            value = float(value)
        return value * pow(10, (from_u - to_u))

    @classmethod
    def get_mothod(self, unit):
        if unit in ["ua", "ma", "a"]:
            return Unit.CURR
        elif unit in ["uv", "mv", "v"]:
            return Unit.VOLT
        elif unit in ["ohm", "mohm", "kohm", "mohm"]:
            return Unit.RES
        elif unit in ["hz", "khz", "mhz", "ghz"]:
            return Unit.FREQ
        else:
            return None


def get_ip(start_from = "169.254"):
    ipconfig_process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
    ipstr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
    output = ipconfig_process.stdout.read()
    ip_pattern = re.compile('(inet %s)' % ipstr)
    # ip_pattern = re.compile('(inet addr:%s)' % ipstr)
    pattern = re.compile(ipstr)
    iplist = []
    for ipaddr in re.finditer(ip_pattern, str(output)):
        ip = pattern.search(ipaddr.group())
        if start_from in ip.group():
        # if ip.group() != "127.0.0.1":
            iplist.append(ip.group())
    return iplist


class PrmParse(object):

    def __init__(self):
        pass


    def replace_special_symbol(self,raw_message):
        bRet = True
        strMessage = raw_message
        try:
            char_list = ["\(", "\)", "\.", "\*", "\[", "\]"]
            char_list1 = ["(", ")", ".", "*", "[", "]"]
            for index, value in enumerate(char_list):
                strMessage = str(strMessage).replace(char_list1[index], char_list[index])

        except:
            bRet = False
        return bRet, strMessage


    def read_re_file_from_txt(self,file_path):
        with open(file_path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            context = f.read()
            # fcntl.flock(f, fcntl.LOCK_UN)
        return context


    def change_to_final_re_context(self, context):
        bRet = True
        try:
            # context = re.sub("(?<={{\S*?)\s+?(?=\S*?}})", "_", context)
            # print context
            context = re.sub("\t|\n| ", "\s*?", context)
            context = re.sub("{{any}}", "[\s\S]*?", context, re.I)
            # context = re.sub("{{([^}]*?)}}", "(?P<", context)
            context = re.sub("{{", "(?P<", context)
            context = re.sub("}}", ">.[\S ]*)", context)
        except:
            bRet = False
        return bRet, context

    def super_re(self, raw_message, re_file_path):
        try:
            if os.path.isfile(re_file_path):
                context = self.read_re_file_from_txt(re_file_path)
                bRet, strMessage = self.replace_special_symbol(context)
                if not bRet:
                    return {}
                bRet, context = self.change_to_final_re_context(strMessage)
                # print context
                if not bRet:
                    return {}
                result = re.finditer(context, raw_message)
                result_list = [m.groupdict() for m in result]
                return result_list[0]
            else:
                return {}
        except Exception as e:
            return {}

    def force_re(self, raw_message, re_file_path):
        try:
            if os.path.isfile(re_file_path):
                context = self.read_re_file_from_txt(re_file_path)
                result = re.finditer(context, raw_message, re.S)
                result_list = [m.groupdict() for m in result]
                return result_list[0]
            else:
                return {}
        except Exception as e:
            return {}


class Dut(object):
    def __init__(self):

        self.parse = PrmParse()
        self._last_diags_command = None
        self._last_diags_response = None
        self.parse_dict = dict()

    def diags(self, *args, **kwargs):
        self._last_diags_command = None
        self._last_diags_response = None
        self.parse_dict = dict()
        pass

    def parse(self, *args,**kwargs):
        if not all([self._last_diags_command, self._last_diags_response]):
            return "--FAIL--{}".format("KeyValue_Empty")

        if not self.parse_dict:
            from Configure.constant import TEMPLATE_PATH
            re_file_path = TEMPLATE_PATH + "{}.txt".format(self._last_diags_command)
            if self._last_diags_command == "special":
                self.parse_dict = self.parse.force_re(self._last_diags_response, re_file_path)
            else:
                self.parse_dict = self.parse.super_re(self._last_diags_response, re_file_path)
                self.parse_dict.setdefault("have_already_parsed", True)
        if self.parse_dict.get("have_already_parsed"):
            try:
                str_key_name = str(args[0])
                key = re.sub("{{|}}", "", str_key_name)
                result = self.parse_dict.get(key, "--FAIL--")
                return result.strip()
            except Exception as e:
                return "--FAIL--{}".format("PARSE_DICT_HAVE_NO_KEY")
        else:
            return "--FAIL--{}".format("PARSE_DICT_EMPTY")


def autoConvert(input):
    """
    :purpose: try to understand each type of input and convert them to be the real type
    :param input: any type
    :return:
    """
    if type(input) == unicode or type(input) == str or type(input) == basestring:
        if input.isalpha():
            # convert T/F to 1/0
            if len(input) == 1 and input.upper() == "T":
                ret_val = 1
            elif len(input) == 1 and input.upper() == 'F':
                ret_val = 0
            else:
                if input.upper() == "TRUE":
                    ret_val = 1
                elif input.upper() == "FALSE":
                    ret_val = 0
                else:
                    ret_val = input
        elif input.isdigit():
            # string convert to int
            ret_val = int(input)
        elif input.isalnum():
            ret_val = input
        else:
            # check if float or other
            try:
                ret_val = float(input)
            except:
                # check if list dict or set
                try:
                    ret_val = eval(input, {"__builtins__": {}}, {})
                except:
                    # after eval check,go on
                    ret_val = input
    else:
        ret_val = input

    ret_type = type(ret_val)
    return ret_val, ret_type



class SSHConnection(object):

    def __init__(self, host='169.254.1.32', port=22, username='root',pwd='123456'):
        self.host = host
        self.port = port
        self.username = username
        self.pwd = pwd
        self.__k = None

    def connect(self):
        transport = paramiko.Transport((self.host,self.port))
        transport.connect(username=self.username,password=self.pwd)
        self.__transport = transport

    def close(self):
        self.__transport.close()
        del self

    def upload(self,local_path,target_path):
        # file_name = self.create_file()
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.put(local_path, target_path)

    def download(self,remote_path,local_path):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.get(remote_path,local_path)

    def cmd(self, command):
        ssh = paramiko.SSHClient()
        ssh._transport = self.__transport
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read()
        # print result
        return result

if __name__ == '__main__':
    response = """PMU ADC test
Read all Channels
Read PMU ADC channels
vddout: 3289.6825 mV
vbat: 3826.9230 mV
brick_id: 2.7472 mV
brick_id2: 2.4420 mV
tcal: 4078.1440 Ohm
temp_buck0: 37.8994 C
temp_buck1: 37.7640 C
tdev1: 29.4592 C
tdev2: 29.3422 C
tdev3: 31.7809 C
tdev4: 27.6556 C
tdev5: -20.1221 C
tdev6: -20.0546 C
tdev7: -20.2578 C
tdev8: -20.0361 C
ibuck0: 0.0000 mA
ibuck1: 0.0000 mA
ibuck2: 0.0000 mA
ibuck3: 0.0000 mA
ibuck4: 0.0000 mA
ibuck7: 0.0000 mA
ibuck9: 0.0000 mA
ibuck11: 0.0000 mA
ibuck13: 0.0000 mA
ibat_out: 40109.5668 mA
BIST buck0: 632.5091 mV
BIST buck1: 605.8608 mV
BIST buck2: 742.9487 mV
BIST buck3: 1800.6715 mV
BIST buck4: 1056.2271 mV
BIST buck7: 1105.2197 mV
BIST buck9: 958.3333 mV
BIST buck11: 1004.4871 mV
BIST buck13: 1250.0915 mV
BIST buck3_sw1: 1800.6715 mV
BIST buck3_sw2: 1800.6715 mV
BIST buck13_sw3: 2.7472 mV
BIST ldo0: 1501.2210 mV
BIST ldo1: 2999.6947 mV
BIST ldo2: 155.3724 mV
BIST ldo3: 1207.6007 mV
BIST ldo5: 127.2893 mV
BIST ldo7: 17.3992 mV
BIST ldo8: 1205.3113 mV
BIST ldo9: 1802.1978 mV
BIST ldo10: 69.5970 mV
BIST ldo11: 887.7289 mV
BIST ldo13: 97.9853 mV
BIST ldo14: 0.7326 mV
BIST ldo16: 2.4420 mV
BIST ldo20: 1205.0366 mV
BIST ildo0: 36.5238 mA
BIST ildo1: 5.4372 mA
BIST ildo2: 1.0637 mA
BIST ildo3: 0.6936 mA
BIST ildo5: 0.9456 mA
BIST ildo7: 1.1819 mA
BIST ildo9: 0.2362 mA
BIST ildo10: 1.0637 mA
BIST ildo13: 1.0637 mA
BIST ildo14: 0.6936 mA
BIST ildo16: 1.0637 mA
BIST amuxa0: 835.7753 mV
BIST amuxa1: 309.8290 mV
BIST amuxa2: 273.1990 mV
BIST amuxa3: 282.3565 mV
BIST amuxb0: 77.8388 mV
BIST amuxb1: 3293.6507 mV
BIST amuxb2: 1051.5873 mV
BIST amuxb3: 3082.7228 mV
BIST amuxay: 2.7472 mV
BIST amuxby: 3.0525 mV
vale vbat : 2.7472 mV
vale brick_id : 2.7472 mV
vale brick_id2 : 2.7472 mV
vale adc_in7 : 881.2271 mV
vale tcal : 4047.6190 Ohm
vale temp_ldo8 : 36.2461 C
vale temp_ldo12 : 37.0775 C
vale temp_buck5 : 36.6752 C
vale temp_buck6 : 36.5411 C
vale temp_buck10 : 36.9166 C
vale temp_buck12 : 36.4070 C
vale tdev1 : -19.5377 C
vale tdev2 : -19.7106 C
vale tdev3 : 29.6380 C
vale tdev4 : 28.1522 C
vale tdev5 : -19.6732 C
vale ibuck5 : 0.0000 mA
vale ibuck6 : 0.0000 mA
vale ibuck10 : 0.0000 mA
vale ibuck12 : 0.0000 mA
vale buck5 : 853.0219 mV
vale buck6 : 789.8351 mV
vale buck8 : 667.6739 mV
vale buck10 : 577.1978 mV
vale buck12 : 881.0439 mV
vale buck14 : 1119.1391 mV
vale buck3_sw4 : 2.7472 mV
vale buck12_sw6 : 883.0891 mV
vale buck12_sw7 : 883.3943 mV
vale buck13_sw5 : 1252.1367 mV
vale ldo0 : 1503.0525 mV
vale ldo4 : 801.1904 mV
vale ldo6 : 34.7985 mV
vale ldo9 : 1800.9768 mV
vale ldo12 : 841.0256 mV
vale ldo15 : 1804.9450 mV
vale ldo17 : 3304.0293 mV
vale ldo18 : 42.4297 mV
vale ildo0 : 5.8128 mA
vale ildo4 : 17.1381 mA
vale ildo6 : 0.6919 mA
vale ildo9 : 0.0063 mA
vale ildo12 : 20.7526 mA
vale ildo15 : 0.6919 mA
vale ildo17 : 0.7612 mA
vale ildo18 : 0.7612 mA"""
    prm_re = PrmParse()
    super_folder = os.path.dirname(os.path.dirname(__file__)) + '/Regex'
    regex_path = os.path.join(super_folder, "pmuadc --read all.txt")
    ret = prm_re.super_re(response, regex_path)
    print ret
