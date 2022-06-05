from TI_Define import *
from datetime import datetime
from ..Function.TI_Common import RootFunction
import serial
import time
from mix.lynx.rpc.profile_client import RPCClientWrapper


class TestItem(RootFunction):
    def __init__(self, driver=None, publisher=None):
        super(TestItem, self).__init__(driver)
        self.publisher = publisher
        self.site = 0
        self.obj_mix = None
        self.other_site = []
        self.obj_aid  = None
        self.rpc_client = None

    def init(self):
        self.site = self.driver.get('site')
        self.obj_mix = self.driver.get('mix')
        self.obj_aid = self.obj_mix.objaid

    def log(self, send, result):
        if self.publisher:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + '{}:{} -]\n'.format(send, result))

    @handle_response
    def reset_board(self, *args, **kwargs):
        try:
            self.obj_mix.reset_mix()
            return "--PASS--"
        except:
            return "--FAIL--"

    @handle_response
    def reset_board_other(self, *args, **kwargs):
        slot_id = str(self.site + 1)
        ip_data = {"1" : "33", "2": "32", "3": "35", "4": "34"}
        reset_board_ip = ip_data.get(slot_id)
        endpoint = {'requester': 'tcp://169.254.1.{}:7801'.format(reset_board_ip), 'receiver': 'tcp://169.254.1.{}:17801'.format(reset_board_ip)}
        self.obj_mix.log_hw("endpoint", "[endpoint]={}".format(endpoint))
        self.rpc_client = RPCClientWrapper(endpoint)
        try:
            self.rpc_client.dma_ip.reset_channel(1)
            self.rpc_client.dma_ip.reset_channel(2)
            self.rpc_client.w2.reset()
            self.rpc_client.psu_board.module_init()
            self.rpc_client.ps_mux.board_init()
            self.rpc_client.relay_sg.reset('BASE_BOARD')
            self.rpc_client.adgarray.reset()
            return '--PASS--'
        except Exception as e:
            self.log("ERROR", e)
            return "--FAIL--"


    @handle_response
    def mix_fw_version(self, *args, **kwargs):
        try:
            key = 'MIX_FW_PACKAGE'
            dic_ret = self.obj_mix.get_fw_version()
            if key in dic_ret:
                return dic_ret[key]
        except:
            return "--FAIL--"

    @handle_response
    def compare_mlbsn(self, *args, **kwargs):
        if len(args) != 1:
            return "--FAIL--"
        localsn = self._get_mlbsn(self.site).strip()
        print "*"*100
        print localsn, args[0]
        print "*"*100
        if localsn != args[0]:
            return "--FAIL--"
        else:
            return "--PASS--"

    def _get_mlbsn(self, uut_num):
        sns = None
        with open('/vault/sn.txt', 'r') as f:
            sns = f.readlines()
        return dict([s.split(':') for s in sns]).get(str('mlbsn{}'.format(uut_num)))

    @handle_response
    def get_cu_usbserial_channel(*args, **kwargs):
        ls_dev_prm_os = os.popen("ls /dev | grep cu.usbserial-").read()
        result_list = ls_dev_prm_os.split('cu.usbserial-')
        if len(result_list) > 6:
            serial_name = "USBserial Slot > 2"
            serial_num = 'num_null'
            return serial_name, serial_num
        for x in result_list:
            if 'PRMU' in x:
                serial_name = 'PRMU'
                num = x.split('PRMU')
                serial_num_list = num[1].split('\n')
                serial_num = str(int(serial_num_list[0])//10)
                return serial_name, serial_num
            elif '14' in x:
                serial_name = x.split('\n')[0]
                serial_name = str(int(serial_name) // 100)
                serial_num = '0'
                # serial_name = '1433'
                # num = x.split('1433')
                # serial_num_list = num[1].split('\n')
                # serial_num = str(int(serial_num_list[0])//10)
                return serial_name, serial_num
            else:
                serial_name = 'USB_Null'
                serial_num = 'num_null'
        return serial_name, serial_num

    @handle_response
    def check_ftdi(self, *args, **kwargs):
        serl_name, slot = self.get_cu_usbserial_channel()
        if serl_name == "USB_Null":
            return "--FAIL--No find FTDI USBserial"
        if serl_name == "USBserial Slot > 2":
            serl_name = "PRMU"
            slot = self.site
        write_data = "GAN!"
        result1 = False
        result2 = False
        port0 = "/dev/cu.usbserial-{}{}0".format(serl_name, slot)
        port1 = "/dev/cu.usbserial-{}{}1".format(serl_name, slot)
        port2 = "/dev/cu.usbserial-{}{}2".format(serl_name, slot)
        port3 = "/dev/cu.usbserial-{}{}3".format(serl_name, slot)

        ser0 = serial.Serial(port0, 115200, timeout=0.5)
        ser1 = serial.Serial(port1, 115200, timeout=0.5)
        ser2 = serial.Serial(port2, 115200, timeout=0.5)
        ser3 = serial.Serial(port3, 115200, timeout=0.5)

        ser0.write(write_data)
        s1 = ser1.read(len(write_data))
        s2 = ser2.read(len(write_data))
        if s1 == s2 and s1 == write_data:
            print "0 send, 1,2 read OK!"
            result1 = True

        ser1.write(write_data)
        s0 = ser0.read(len(write_data))
        s3 = ser3.read(len(write_data))
        if s0 == s3 and s0 == write_data:
            print "1 send, 0,3 read OK!"
            result2 = True

        if result1 and result2:
            return "--PASS--"
        if not result1 and not result2:
            return "--FAIL--Both 0->1, 1->0 fail"
        if not result1:
            return "--FAIL--Only 0->1 fail"
        else:
            return "--FAIL--Only 1->0 fail"

    @handle_response
    def aid_reset(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        dev_name = str(args[0])
        try:
            result = self.obj_aid.aid_reset(dev_name)
            time.sleep(0.1)
            self.obj_mix.log_hw("aid_reset", "[result]={}".format(result))
            if result == 'done':
                return "--PASS--"
            return "--FAIL--"
        except Exception as e:
            self.log("ERROR", e)
            return "--FAIL--"

    @handle_response
    def aid_wake_up(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        dev_name = str(args[0])
        try:
            result = self.obj_aid.aid_reset(dev_name)
            time.sleep(1)
            result = self.obj_aid.aid_set_response(dev_name)
            time.sleep(0.1)
            self.obj_mix.log_hw("aid_set_response", "[result]={}".format(result))
            if str(result) == "0":
                # result = self.obj_aid.aid_handle_command(dev_name)
                # self.obj_mix.log_hw("aid_handle_command", "[result]={}".format(result))
                # if result == 'done':
                return "--PASS--"
            return "--FAIL--"
        except Exception as e:
            self.log("ERROR", e)
            return "--FAIL--"

    








