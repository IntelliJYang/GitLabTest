# -*-coding:utf-8 -*-
import sys
sys.path.append("/Library/Python/2.7/site-packages")

import time
import re
from datetime import datetime
from Configure.driver_config import HW_CFG
from ..Function.TI_Common import RootFunction
from ..Utility.utility import PrmParse, scaleConvert
from TI_Define import *
from ..Library.dock_channel import DockChannel

import threading
from threading import Thread

class TI_DUT(RootFunction):
    def __init__(self, driver=None, publisher=None):
        super(TI_DUT, self).__init__(driver)
        self.isUseDockChannel = False
        self.scale = scaleConvert()
        self.prmparse = PrmParse()
        self.obj_dc_31336 = None
        self.obj_dc_31337 = None
        self.obj_dc_41336 = None
        self.obj_dc_41337 = None
        self._last_diags_command = None
        self._last_diags_response = None
        self.publisher = publisher
        self.obj_mix = None
        self.obj_uart = None
        self.site = None
        self.status = None
        self.runFlag = False
        self.silego_data = []
        self._lock = threading.Lock()

    def init(self):
        self.ssh = self.get_method("_ssh")
        self.obj_mix = self.get_method("mix")
        self.site = self.get_method("site")
        self.obj_uart = self.obj_mix.objsguart

    def log(self, title, data):
        if not data:
            return
        if self.publisher:
            self.publisher.publish('[' + str(datetime.now()) + ']-[{}]:{}'.format(title, data))

    def _uart_read(self, length):
        return self.obj_uart.uart_read(0, length)

    def _uart_write(self, data):
        return self.obj_uart.uart_write(0, data)

    def _diags_clear(self):
        if self.isUseDockChannel:
            clear_data = self.obj_dc_31337.dc_read()
        else:
            clear_data = self._uart_read(4096)
        if clear_data:
            self.log("CLEAR=READ", clear_data)
        return True

    def _diags_send(self, data):
        if self.isUseDockChannel:
            self.obj_dc_31337.dc_send(data)
        else:
            self._uart_write(data)
        self.log("SEND", data)
        # print "_diags_send: {}".format(data)
        return True

    def _diags_read(self, terminator=":-)", timeout=15.0, is_match=False):
        ret = ''
        result = False
        date_start = datetime.now()
        data_buf = ''
        while (datetime.now() - date_start).total_seconds() < timeout:
            if self.isUseDockChannel:
                data_once = self.obj_dc_31337.dc_read()
            else:
                data_once = self._uart_read(1024)
            if data_once:
                data_buf += data_once
                # self.log("READ", data_once)
            # print "_diags_read: {}".format(data_once)
            if is_match:
                ret = data_buf.strip()
                if terminator==":-)" and terminator in ret:
                    result = True
                    break

                elif ret and len(ret) > 0 and ret[-1] == terminator:
                    result = True
                    break
            else:
                if data_buf and len(data_buf) > 0:
                    ret = "{}{}".format(ret, data_buf)
                    if terminator in ret:
                        result = True
                        break
            time.sleep(0.1)
        self.log("READ", data_buf)
        try:
            ret = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+", u"", ret)
        except:
            pass
        # print "_diags_read: {}".format(ret)
        return result, ret


    @handle_response
    def i2c_detect(self, *args, **kwargs):
        try:
            if len(args) != 2:
                return "--FAIL--MISS-PARA"
            loop_times = args[0]
            i2c_add = str(args[1])
            # i2c-3 -> i2c mux and ioexp 21 22 70
            # i2c-4 -> psu 53
            # i2c-5: dut i2c0
            # i2c-6: dut i2c4
            # i2c = 7 if self.site % 2 == 0 else 16
            iPass = 0
            for i in range(int(loop_times)):
                response = self.ssh.cmd("/i2cdetect -y -r {}".format(i2c_add))
                print response
                check_data = "50"
                if i2c_add in ["5", "6"]:
                    check_data = "54"
                    patt = re.compile("50\s*:\s*\S*\S*\s*\S*\S*\s*\S*\S*\s*\S*\S*\s*(\d+)")
                else:
                    if i2c_add in ["3", "6"]:
                        check_data = "22"
                        patt = re.compile("20\s*:\s*\S*\S*\s*\s*(\d+)\s*(\d+)")
                        print patt
                    else:
                        if i2c_add in ["4", "6"]:
                            check_data = "53"
                            patt = re.compile("50\s*:\s*\S*\S*\s*\S*\S*\s*\S*\S*\s*\s*(\d+)")
                            print patt
                        else:
                            patt = re.compile("50\s*:\s*(\d+)")
                            print patt
                result = patt.findall(response)
                if len(result) < 1:
                    continue
                time.sleep(0.01)
                if check_data in "{}".format(result[0]):
                    iPass += 1
                    print("=====================")
            return iPass
        except:
            return '--FAIL--'

    def i2c_addr_detect_10times(self, *args, **kwargs):
        # args[0]: i2c_Xavier_bus
        # args[1]: i2c_addr
        #         
            # i2c-1 -> gpio array 70 71 72
            # i2c-1 -> moto eeprom 51.   57 5f if fail 
            # i2c-3 -> i2c mux and ioexp 21 22 70
            # i2c-4 -> psu 53
            # i2c-5: dut i2c0
            # i2c-6: dut i2c4
            # i2c = 7 if self.site % 2 == 0 else 16
        try:
            if len(args) != 2:
                return "--FAIL--MISS-PARA"
            loop_times = 10
            i2c_Xavier_bus = str(args[0])
            i2c_addr_list = str(args[1]).split('_')
            addr_len = len(i2c_addr_list)
            iPass = 0
            for i in range(int(loop_times)):
                # self.log('loop_times:({})'.format(loop_times), "i:({})".format(i))
                response = self.ssh.cmd("/i2cdetect -y -r {}".format(i2c_Xavier_bus))
                self.log('i2c_Xavier_bus:({})'.format(i2c_Xavier_bus), "response:({})".format(response))
               # print response
                addr_i = 0
                addr_pass_len = addr_len
                for addr in i2c_addr_list:
                    # self.log('addr:({})'.format(addr), "addr_i:({})".format(addr_i))
                    if '!' in addr:
                        addr_pass_len -= 1
                        self.log('i2c_Xavier_bus:({})'.format(i2c_Xavier_bus), "addr_pass_len:({})".format(addr_pass_len))
                        addr_fail = addr.split('!')
                        # print ("!!!!", addr,addr_fail)
                        if addr_fail[1] in response:
                            self.log('addr_fail:({})'.format(addr_fail), "addr_i:({})".format(addr))
                            return "--FAIL--pls remove i2c addr 0x" + addr_fail[1]
                    addr_pass = ' ' + addr
                    self.log('addr_pass:({})'.format(addr_pass), "i2c_addr_list:({})".format(i2c_addr_list))
                    if addr_pass in response:
                        addr_i += 1
                        self.log('addr_pass:({})'.format(addr_pass), "addr_i:({})".format(addr_i))
                if addr_pass_len == addr_i:
                    iPass += 1
                    self.log('addr_pass_len:({})'.format(addr_pass_len), "iPass:({})".format(iPass))
                else:
                    self.log('addr_pass_len:({})'.format(addr_pass_len), "iPass:({})".format(iPass))

            return iPass
        except:
            return '--FAIL--'

    @handle_response
    def dut_communication_type(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        if args[0] == "dock_channel":
            self.isUseDockChannel = True
        else:
            self.isUseDockChannel = False
        return args[0]

    @handle_response
    def open_dock_channel(self, *args, **kwargs):
        if not self.isUseDockChannel:
            return "--SKIP--"
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        port = int(args[0])
        tcp_ip = HW_CFG['uut{}'.format(self.site)]['xavier']['requester']
        host = re.findall("\/\/(.*)\:", tcp_ip)[0]
        if tcp_ip and port == 31336:
            self.obj_dc_31336 = DockChannel(self.publisher)
            self.obj_dc_31336.dc_open(host, port)
            return "--PASS--"
        elif tcp_ip and port == 31337:
            self.obj_dc_31337 = DockChannel(self.publisher)
            self.obj_dc_31337.dc_open(host, port)
            return "--PASS--"
        elif tcp_ip and port == 41336:
            self.obj_dc_41336 = DockChannel(self.publisher)
            self.obj_dc_41336.dc_open(host, port)
            return "--PASS--"
        elif tcp_ip and port == 41337:
            self.obj_dc_41337 = DockChannel(self.publisher)
            self.obj_dc_41337.dc_open(host, port)
            return "--PASS--"
        else:
            return "--FAIL--Host or Port error"

    @handle_response
    def close_dock_channel(self, *args, **kwargs):
        if not self.isUseDockChannel:
            return "--SKIP--"
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        port = int(args[0])
        if port == 31336 and self.obj_dc_31336:
            self.obj_dc_31336.dc_close()
            return "--PASS--"
        elif port == 31337 and self.obj_dc_31337:
            self.obj_dc_31337.dc_close()
            return "--PASS--"
        elif port == 41336 and self.obj_dc_41336:
            self.obj_dc_41336.dc_close()
            return "--PASS--"
        elif port == 41337 and self.obj_dc_41337:
            self.obj_dc_41337.dc_close()
            return "--PASS--"
        else:
            return "--FAIL--Port error"

    @handle_response
    def query_dc_31336(self, *args, **kwargs):
        if not self.isUseDockChannel:
            return "--SKIP--"
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        cmd = args[0]
        self.log("31336 --> ", cmd)
        ret = self.obj_dc_31336.dc_query(cmd)
        self.log("31336 <-- ", ret)
        if ret and len(ret) > 0:
            return "--PASS--"
        else:
            return "--FAIL--DC 31336 no response"

    @handle_response
    def query_dc_41336(self, *args, **kwargs):
        if not self.isUseDockChannel:
            return "--SKIP--"
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        cmd = args[0]
        self.log("41336 --> ", cmd)
        ret = self.obj_dc_41336.dc_query(cmd)
        self.log("41336 <-- ", ret)
        if ret and len(ret) > 0:
            return "--PASS--"
        else:
            return "--FAIL--DC 41336 no response"

    @handle_response
    def detect_diags(self, *args, **kwargs):
        try:
            if len(args) != 1:
                return MISSING_ENOUGH_PARA
            timeout = float(args[0])
            date_start = datetime.now()
            result_recovery = False
            result_diags = False
            while (datetime.now() - date_start).total_seconds() < timeout:
                if result_recovery:
                    print "detect: start enter diags"
                    self._diags_send('diags')
                    time.sleep(0.5)
                    result_diags, data_diags = self._diags_read("] :-)", timeout=25)
                    if result_diags:
                        print "detect: already entered diags"
                        # clear buffer and make it ready for test
                        time.sleep(0.5)
                        self._diags_clear()
                        break
                else:
                    print "detect: start enter recovery"
                    self._diags_send('')
                    time.sleep(0.1)
                    result_recovery, data_recovery = self._diags_read("]", timeout=0.5, is_match=True)
            if result_diags:
                return "--PASS--"
        except Exception as e:
            return "--FAIL--{}".format(e)

    @handle_response
    def detect_recovery(self, *args, **kwargs):
        try:
            self.parse_dict = dict()
            self._last_diags_response = ""
            self._last_diags_command = "recovery"
            if len(args) != 1:
                return MISSING_ENOUGH_PARA
            timeout = float(args[0])
            date_start = datetime.now()
            result_recovery = False
            while (datetime.now() - date_start).total_seconds() < timeout:
                print "detect: start enter recovery"
                self._diags_send('')
                time.sleep(0.1)
                result_recovery, data_recovery = self._diags_read("]", timeout=0.5, is_match=True)
                self._last_diags_response = self._last_diags_response + str(data_recovery)
                if result_recovery and "ECID" in self._last_diags_response:
                    print "detect: already entered recovery"
                    break
            if result_recovery:
                return "--PASS--"
        except Exception as e:
            return "--FAIL--{}".format(e)

    @handle_response
    def parse(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        str_key_name = str(args[0])
        return self._parse(str_key_name)

    def _parse_temperature_all(self, data, key=None):
        title_1 = ''
        title_2 = ''
        title_3 = ''
        dic_ret = {}
        arr_data = data.split('\n')
        for item in arr_data:
            if "Device: " in item:
                title_1 = item.split(':')[-1].strip()
            if "THERMAL" in item or "TCAL" in item or "TDEV" in item:
                title_2 = item.strip()
            if "Tp0" in item or "Te0" in item or "Ts0" in item:
                temp = item.strip()
                name = temp.split(' ')
                title_2 = name[0]
            else:
                arr_tmp = item.split(':')
                if arr_tmp and len(arr_tmp) >= 2:
                    title_3 = arr_tmp[0].strip()
                    val = arr_tmp[-1].replace('deg C', '').strip()
                    title = '{}_{}_{}'.format(title_1, title_2, title_3).lower()
                    dic_ret[title] = val
                    if key and key == title:
                        return dic_ret
        return dic_ret

    @handle_response
    def parse_special(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        parse_key = args[0]
        key = re.sub("{{|}}", "", parse_key)
        parse_special_cmd = ["pmuadc --sel cpmu2 --read all", "pmuadc --sel cpmu4 --read all", "pmuadc --sel vale --read all", "pmuadc --sel stowe --read all"]
        if self._last_diags_command == "temperature --all":
            try:
                result = self._parse_temperature_all(self._last_diags_response, key)
                if key in result:
                    return result[key]
                else:
                    return "--FAIL--No parse key"
            except Exception as e:
                print e
                return  "--FAIL--Parse Fail"
        elif self._last_diags_command == "pmuadc --sel rpmu --read" or self._last_diags_command == "pmuadc --read all":
            try:
                result = self._parse_special_data(self._last_diags_response, key)
                if key in result:
                    return result[key]
                else:
                    return "--FAIL--No parse key"
            except Exception as e:
                print e
                return  "--FAIL--Parse Fail"
        elif self._last_diags_command in parse_special_cmd:
            try:
                result = self._parse_special_data(self._last_diags_response, key)
                if key in result:
                    return result[key]
                else:
                    return "--FAIL--No parse key"
            except Exception as e:
                print e
                return  "--FAIL--Parse Fail"
        else:
            return "--FAIL--Incorrect parse type"

    def parse_i2c_read(self, *args, **kwargs):
        if self._last_diags_response and len(self._last_diags_response) > 0:
            pattern = re.compile("0000000: \s*([0-9|a-z|A-Z| ]+)")
            arr_result = pattern.findall(self._last_diags_response)
            if arr_result and len(self._last_diags_response) > 0:
                str_result = arr_result[0].strip()
                return str_result
            else:
                return "--FAIL--Parse fail"
        else:
            return "--FAIL--Empty response"

    def _parse(self, parse_key):
        if not all([self._last_diags_command, self._last_diags_response]):
            return "--FAIL--{}".format("KeyValue_Empty")
        if not self.parse_dict:                
            from Configure.constant import TEMPLATE_PATH
            re_file_path = TEMPLATE_PATH + "{}.txt".format(self._last_diags_command)
            if 'upy nandfs' in self._last_diags_command:
                re_file_path = TEMPLATE_PATH + "{}.txt".format('upy nandfs')
            if self._last_diags_command == "special":
                self.parse_dict = self.prmparse.force_re(self._last_diags_response, re_file_path)
            else:
                self.parse_dict = self.prmparse.super_re(self._last_diags_response, re_file_path)
                
                    
                self.parse_dict.setdefault("have_already_parsed", True)
        if self.parse_dict.get("have_already_parsed"):
            try:
                key = re.sub("{{|}}", "", parse_key)
                if 'upy nandfs' in self._last_diags_command:
                    print key , '  ', '-' * 10
                result = self.parse_dict.get(key, "--FAIL--No parse key")
                result = result.replace("\\r", "").replace("\r", "")
                result = result.replace("\\n", "").replace("\n", "")
                result = result.replace("\\t", "").replace("\t", "")
                result = result.strip()
                print "parse result = {}".format(result)
                if result and len(result) > 0:
                    if "Not Found!" in result:
                        return "--FAIL--'Not Found!' in response"
                    else:
                        return result
                else:
                    return "--FAIL--Value is empty"
            except Exception as e:
                return "--FAIL--{}".format("PARSE_DICT_HAVE_NO_KEY")
        else:
            return "--FAIL--{}".format("PARSE_DICT_EMPTY")

    @handle_response
    def diags(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs.get('timeout', 10000))
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        check_str = None
        if len(args) > 1:
            check_str = args[1]
        ret = self._diags(cmd, check_str=check_str, timeout=timeout/1000.0 - 5.0)
        if check_str and len(check_str) > 1 and ret == "--PASS--":
            return check_str
        else:
            return ret

    @handle_response
    def upy_parse(self, *args, **kwargs):
        self.dic_data = {}
        key = args[0]
        reply = self._last_diags_response
        if reply and len(reply) > 0:
            arr_tmp = reply.split("\n")
            print arr_tmp
            for line in arr_tmp:
                if len(line) > 0 and ("-" in line):
                    line = line.strip()
                    arr_data = line.split('-')
                    if arr_data and len(arr_data) >= 2:
                        self.dic_data[arr_data[0].strip().replace(": ", " ").replace(" ", "_")] = arr_data[1]
        print self.dic_data
        if key in self.dic_data:
            if key == "INFO_COIL_DRIVE_TEST" or key == "INFO_BB_TEST":
                if self.dic_data[key].strip() == "FAIL":
                    return "PASS"
            else:
                result = self.dic_data[key].strip()
                return result



    @handle_response
    def diags_send(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        diags_cmd = args[0]
        mode = None
        if len(args) > 1:
            mode = args[1]
        self._diags_clear()
        self._last_diags_command = re.sub('\[|\]', '', diags_cmd)
        if diags_cmd != "":
            self._diags_send(diags_cmd)
#            time.sleep(0.1)
            if mode == "free_read":
                self._diags_clear()
            return "--PASS--"
        else:
            return "--FAIL--MISS_DIAGS_CMD"

    @handle_response
    def diags_parse(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs['timeout'])
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        parse_key = None
        if len(args) > 1:
            parse_key = args[1]
        return self._diags(cmd, parse_key=parse_key, timeout=timeout/1000.0 - 5.0)

    def _diags(self, diags_cmd, check_str=None, parse_key=None, timeout=30.0):
        self._last_diags_command = None
        self._last_diags_response = None
        self.parse_dict = dict()
        try:
            self._diags_clear()
            self._last_diags_command = re.sub('\[|\]', '', diags_cmd)
            if diags_cmd != "":
                self._diags_send(diags_cmd)
                time.sleep(0.01)
                tmp_result, tmp_ret = self._diags_read(":-)", timeout=timeout,is_match=True)
                self._last_diags_response = "{}".format(tmp_ret)
                if self._last_diags_response and len(self._last_diags_response) > 0:
                    if ":-)" not in self._last_diags_response:
                        return "--FAIL--Diags can not detect ':-)'"
                    if "Error" in self._last_diags_response or "Failed" in self._last_diags_response:
                        if self._last_diags_command not in ["csi on", "device -k usbphy -e enable ciodp", "nand --get Identify"]:
                            return "--FAIL--Diags error"
                else:
                    return "--FAIL--Read timeout"
            else:
                return "--FAIL--MISS_DIAGS_CMD"
            if check_str and len(check_str) > 1:
                if check_str in self._last_diags_response:
                    return "--PASS--"
                else:
                    return "--FAIL--'{}' not in response".format(check_str)
            if parse_key and len(parse_key) > 1:
                return self._parse(parse_key)
            else:
                return "--PASS--"
        except Exception as e:
            return "--FAIL--{}".format(e)


    @handle_response
    def diags_turn_on_will_pmu(self, *args, **kwargs):
        # if len(args) <= 0:
        #     return MISSING_ENOUGH_PARA
        # diags_cmd = args[0]
        # mode = None
        # if len(args) > 1:
        #     mode = args[1]
        timeout = kwargs.get("timeout")
        self._diags_clear()

        current_folder = os.path.abspath(os.path.dirname(__file__)).split('/')
        current_folder = '/'.join(current_folder[:-3])
        directory = current_folder + "/ThirdPartyLib"

        filepath = directory + '/turn_on_will_PMU_New.txt'
        try:
            date_start = datetime.now()
            with open(filepath) as f:
                data = f.readlines()
                for diags_cmd in data:
                    if (datetime.now() - date_start).total_seconds() > (timeout / 1000.0 - 10.0):
                        return "--FAIL--"
                    self._diags_send(diags_cmd)
                    print diags_cmd
                    time.sleep(0.1)
                    result_diags, data_diags = self._diags_read(":-)", timeout=3,is_match=True)
                    print result_diags, data_diags 
                    self._diags_clear()
            return "--PASS--"
        except Exception as e:
            self.log("turn_on_will_pmu", "[result]={}".format(e))
            return "--FAIL--"


    def _parse_special_data(self, data, key=None):
        dic_ret = {}
        arr_data = data.split('\n')
        for item in arr_data:
              # print item
              arr_tmp = item.split(':')
              if arr_tmp and len(arr_tmp) >= 2:
                    name = arr_tmp[0].strip()
                    title = name.replace(' ', '_')
                    title = title.lower()
                    full_data = arr_tmp[1].strip()
                    data = full_data.split(' ')
                    val = data[0]
                    dic_ret[title] = val
                    if key and key == title:
                        return dic_ret
        return dic_ret

    @handle_response
    def diags_special(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs['timeout'])
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        parse_key = None
        if len(args) > 1:
            parse_key = args[1]

        if cmd != "i2c -d 12 0x08 0xCB 1":
            if self.status:
                return "--SKIP--"

        val = self._diags(cmd, parse_key=parse_key, timeout=timeout/1000.0 - 5.0)
        if cmd == "i2c -d 12 0x08 0xCB 1":
            if val == "0x07":
                self.status = True
            else:
                self.status = False

        if cmd == "i2c -d 12 0x0A 0xC0 16":
            data = self._parse_i2c_data()
            # self.log("debug:", "[result]={}:{}".format(len(data), data))
            if data == "0x00  0x3C  0x00  0x00  0x02  0x00  0x01  0x00  0x00  0x00  0x01  0x07  0x00  0x00  0x0E  0x00":
                return "--PASS--"
            else:
                return "--FAIL--"
        if cmd == "i2c -d 12 0x0A 0xB0 16":
            data = self._parse_i2c_data()
            if data == "0x02  0x00  0x56  0x11  0x10  0x00  0x46  0x00  0xFA  0x02  0x00  0x56  0x46  0x10  0x00  0x02":
                return "--PASS--"
            else:
                return "--FAIL--"
        return val


    def _parse_i2c_data(self):
        if self._last_diags_response and len(self._last_diags_response) > 0:
            pattern = re.compile("Data: \s*([0-9|a-z|A-Z| ]+)")
            arr_result = pattern.findall(self._last_diags_response)
            if arr_result and len(self._last_diags_response) > 0:
                str_result = arr_result[0].strip()
                return str_result
            else:
                return "--FAIL--Parse fail"
        else:
            return "--FAIL--Empty response"


    @handle_response
    def diags_durant_special(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs['timeout'])
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        check_str = None
        if len(args) > 1:
            check_str = args[1]

        repeat = 3
        for i in range(repeat):
            ret = self._diags(cmd, check_str=check_str, timeout=3)
            if check_str and len(check_str) > 1 and ret == "--PASS--":
                return check_str
            else:
                time.sleep(1.5)
                self._diags_send("device -k durant -e power_off")
                time.sleep(0.5)

        if check_str and len(check_str) > 1 and ret == "--PASS--":
            return check_str
        else:
            return ret


    @handle_response
    def diags_cio_special(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs['timeout'])
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        check_str = None
        if len(args) > 1:
            check_str = str(args[1]).strip()

        ret = self._diags(cmd, check_str=check_str, timeout=3)
        if self._last_diags_response and len(self._last_diags_response) > 0:
            pattern = re.compile("000 => (.*)\r")
            arr_result = pattern.findall(self._last_diags_response)
            if arr_result and len(self._last_diags_response) > 0:
                str_result = arr_result.count(check_str)
                return str_result
            else:
                return "--FAIL--Parse fail"
        else:
            return "--FAIL--Empty response"

    @handle_response
    def diags_silego_special(self, *args, **kwargs):
        self.silego_data = []
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs['timeout'])
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        if len(args) > 1:
            check_str = str(args[1]).strip()
        check_str1 = "0x00C44B81"
        check_str2 = "0x00C44B80"

        ret = self._diags(cmd, check_str=check_str, timeout=40)
        if self._last_diags_response and len(self._last_diags_response) > 0:
            pattern = re.compile("0x23C10001C => (.*)\r")
            arr_result = pattern.findall(self._last_diags_response)
            self.log("diags_silego_special", "[result]={}".format(arr_result))
            self.silego_data = arr_result
            if len(arr_result) == 30 and len(self._last_diags_response) > 0:
                # check_result1 = arr_result[0:18].count(check_str1)
                # check_result2 = arr_result[20:].count(check_str2)
                # self.log("diags_silego_special", "[0x00C44B81]={} [0x00C44B80]={}".format(check_result1, check_result2))
                # if check_result1 == 18 and check_result2 == 10:
                return "--PASS--"
            else:
                return "--FAIL--Parse fail"
        else:
            return "--FAIL--Empty response"

    @handle_response
    def get_silego_data(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs['timeout'])
        index = int(args[0]) - 1
        if len(self.silego_data) == 30:
            value = self.silego_data[index]
            self.log("get_silego_data", "[result]={}".format(value))
            return value
        else:
            return "--FAIL--"


    @handle_response
    def parse_audio_data(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        channel = int(args[0])
        query_name = str(args[1])

        if query_name == "frequency":
            total_num = 40
            channel = channel * 5
            pattern = re.compile("Frequency: \s*(\d+.\d+)")
        elif query_name == "dc_magnitude":
            total_num = 8
            pattern = re.compile("DC Magnitude=(\d.\d+)")
        elif query_name == "peak_magnitude":
            total_num = 40
            channel = channel * 5
            pattern = re.compile("Peak Magnitude=(\d+.\d+)")
        else:
            return "--FAIL--Para fail"

        if self._last_diags_response and len(self._last_diags_response) > 0:
            try:
                arr_result = pattern.findall(self._last_diags_response)
                if arr_result and len(self._last_diags_response) > 0:
                    if len(arr_result) < channel or len(arr_result) < total_num:
                        return "--FAIL--Parse fail"
                    str_result = arr_result[channel].strip()
                    return float(str_result)
                else:
                    return "--FAIL--Parse fail"
            except Exception as e:
                self.log("parse_audio_data", "[result]={}".format(e))
                return "--FAIL--"
        else:
            return "--FAIL--Empty response"


    @handle_response
    def calculate_register(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        register = str(args[0]).split('@')
        step = str(args[1]).split('_')
        if len(step) != 4:
            return MISSING_ENOUGH_PARA
        self.obj_mix.log_hw("calculate_register", "[result]={}, {}".format(register, step))

        reg1 = register[0]
        reg2 = None
        if len(register) > 1:
            reg2 = register[1]
        reg1_start = 7 - int(step[0])
        reg1_stop = 8 - int(step[1])
        reg2_start =7 - int(step[2])
        reg2_stop = 8 - int(step[3])

        data_1 = ''
        data_2 = ''
        if reg1:
            data_1 = self.get_reg_data(reg1, reg1_start, reg1_stop)
        if reg2:
            data_2 = self.get_reg_data(reg2, reg2_start, reg2_stop)

        self.obj_mix.log_hw("calculate_register2", "[result]={}, {}".format(data_1, data_2))

        value = int((data_1 + data_2), 2)


        # data_h = get_mask_data(reg1, mask1, shift1)
        # data_l = get_mask_data(reg2, mask2, shift2)
        # value = self.get_reg_data(reg1, reg1_start, reg1_stop) + self.get_reg_data(reg2, reg2_start, reg2_stop)

        return value

    def get_reg_data(self, reg, start, stop):
        temp =  self.scale.hex2bin(reg)
        # temp2 = '0'*(8 - len(temp)) + temp
        temp2 = temp.rjust(8, '0')
        self.obj_mix.log_hw("calculate_register", "[result]={}".format(temp2))
        return temp2[start:stop]




    def get_mask_data(self, reg, mask, shift):
        # reg = int('00001100', 2)  #'00001100'
        # shift = 2
        # mask = 3
        mask_value = (2 ** mask - 1) << shift
        reg = (reg & mask_value) >> shift
        return reg

    @handle_response
    def diags_initialize_rigel(self, *args, **kwargs):
        # if len(args) <= 0:
        #     return MISSING_ENOUGH_PARA
        # diags_cmd = args[0]
        # mode = None
        # if len(args) > 1:
        #     mode = args[1]
        timeout = kwargs.get("timeout")
        cmd_file = str(args[0])
        self._diags_clear()

        current_folder = os.path.abspath(os.path.dirname(__file__)).split('/')
        current_folder = '/'.join(current_folder[:-3])
        directory = current_folder + "/ThirdPartyLib"
        filepath = directory + '/' + cmd_file + '.txt'

        try:
            date_start = datetime.now()
            with open(filepath) as f:
                data = f.readlines()
                for diags_cmd in data:
                    if (datetime.now() - date_start).total_seconds() > (timeout / 1000.0 - 10.0):
                        return "--FAIL--"
                    self._diags_send(diags_cmd)
                    # print diags_cmd
                    time.sleep(0.005)
                    result_diags, data_diags = self._diags_read(":-)", timeout=3,is_match=True)
                    # print result_diags, data_diags 
                    self._diags_clear()
                time.sleep(0.1)
                self._diags_clear()
            return "--PASS--"
        except Exception as e:
            self.log("diags_initialize_rigel", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def start_rigel_reg_read(self, *args, **kwargs):
        try:
            self.thread = Thread(target=self._start_read_data, name='rigel')
            self.thread.setDaemon(True)
            self.thread.start()
            # thread.start_new_thread(self._start_read_data,())
            time.sleep(0.2) 
        except Exception as e:
            self.log("start_rigel_reg_read", "[result]={}".format(e))
            return "--FAIL--"
        return "--PASS--"

    def _start_read_data(self):
        # import os
        diags_cmd = "camisp --i2cread 0 0x55 0x84 1 1"
        self.runFlag = True
        while self.runFlag:
            self._lock.acquire(True)
            self._diags_send(diags_cmd)
            # print diags_cmd
            time.sleep(0.005)
            self._diags_read(":-)", timeout=1,is_match=True)
            # print result_diags, data_diags 
            self._diags_clear()
            self._lock.release()
            time.sleep(0.9)

    @handle_response
    def stop_rigel_reg_read(self, *args, **kwargs):
        time.sleep(0.01)
        try:
            self.runFlag = False
            self.thread.join()
        except Exception as e:
            self.log("stop_rigel_reg_read", "[result]={}".format(e))
            return "--FAIL--"
        return "--PASS--"

    def _send_rigel_cmd(self, diags_cmd):
        try:
            self._lock.acquire(True)
            self._diags_send(diags_cmd)
            time.sleep(0.005)
            self._diags_read(":-)", timeout=1,is_match=True) 
            self._diags_clear()
            self._lock.release()
        except Exception as e:
            self.log("_send_rigel_cmd", "[result]={}".format(e))
            return "--FAIL--"
        return "--PASS--"

    @handle_response
    def diags_for_sleep_test(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        timeout = float(kwargs.get('timeout', 10000))
        if timeout <= 0:
            timeout = 30.0
        cmd = args[0]
        cmd = cmd.replace("@", ".")
        check_str = None
        if len(args) > 1:
            check_str = args[1]
        ret = self._diags(cmd, check_str=check_str, timeout=timeout/1000.0 - 5.0)
        if check_str and len(check_str) > 1 and ret == "--PASS--":
            return check_str
        else:
            return ret






