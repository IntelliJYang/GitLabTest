import re
import os
import time
import zmq
from mix.lynx.rpc.profile_client import RPCClientWrapper
from datetime import datetime
from Configure import zmqports
from Configure.driver_config import HW_CFG
from Common.Singleton import Singleton
from Common.publisher import ZmqPublisher
from Driver.Device.mix_device.mixproject import MixUseInProject
from Driver.Function.TI_Common import CallBack, General
from Driver.Function.TestItem import TestItem
from Driver.Function.TI_Relay import TI_Relay
from Driver.Function.TI_Wolverine2 import TI_Wolverine2
from Driver.Function.TI_Digitizer import TI_Digitizer
from Driver.Function.TI_Datalogger import TI_Datalogger
from Driver.Function.TI_PSU import TI_PSU
from Driver.Function.TI_VDM import TI_VDM
from Driver.Function.TI_Freq import TI_Freq
from Driver.Function.TI_AdgRelay import TI_AdgRelay
from Driver.Function.TI_UART import TI_UART
from Driver.Function.TI_DUT import TI_DUT
from Driver.Function.TI_Cal import TI_Cal
from Driver.Function.TI_Fixture import TI_Fixture
from Driver.Function.TI_OTP import TI_OTP
from Driver.Function.TI_Trinary import TI_Trinary
from TestEngine.Driver.Utility.utility import SSHConnection
from Driver.Function.TI_Calmux import TI_Calmux

pwd = os.path.dirname(__file__)
SCRIPT_PATH = '/'.join(pwd.split('/')) + '/script/'

class DriverManager(object):
    """ Singleton, only one instance """
    __metaclass__ = Singleton

    def __init__(self, site, publisher):
        self.site = site
        self.publisher = publisher
        self._drivers = {}
        self._functions = {}
        try:
            self._register_instance()
            self._register_functions()
            self._init_hardware()
        except Exception as e:
            self.publisher.publish(str(datetime.now()) + ' ' * 3 + 'TestEngine{}-ERROR:{} \n'.format(self.site, e))
            raise
        self.publisher.publish(str(datetime.now()) + ' ' * 3 + 'TestEngine{}-ALL_MODULE_INIT_SUCCESS \n'.format(self.site))

    def init_all_drivers(self):
        for name, driver in self._drivers.iteritems():
            try:
                driver.init()
            except:
                pass

    def _register_instance(self):
        try:
            if self.site in [0, 1]:
                ssh = SSHConnection("169.254.1.32")
            elif self.site in [2,3]:
                ssh = SSHConnection("169.254.1.33")
            ssh.connect()
            bin_path = "{}i2cdetect".format(SCRIPT_PATH)
            ssh.upload(bin_path, "/i2cdetect")
            ssh.cmd("chmod 777 /i2cdetect")

            self._drivers['site'] = self.site
            mix_cfg = HW_CFG['uut{}'.format(self.site)]['xavier']
            host = re.findall("\/\/(.*)\:", mix_cfg['requester'])[0]
            os.system('ping -t 5 {}'.format(host))
            
            context = zmq.Context()
            pub_endpoint = "tcp://*:{}".format(int(zmqports.ARM_PUB) + self.site)
            pub_mix = ZmqPublisher(context, pub_endpoint, "MIX_{}".format(self.site))

            client = RPCClientWrapper(mix_cfg, publisher=pub_mix)
            self._drivers["mix"] = MixUseInProject(client)
            client.datalogger.shutdown_all()        # shutdown all datalogger when launch app

            dut_put_endpoint = "tcp://*:{}".format(int(zmqports.UART2_PUB) + self.site)
            zmq_publisher = ZmqPublisher(context, dut_put_endpoint, "DUT_{}".format(self.site))
            ti_dut = TI_DUT(self._drivers, publisher=zmq_publisher)
            self._drivers["ti_dut"] = ti_dut

            os.system("ifconfig | grep -E 'inet (169.254).*' | awk -F ' ' '{print $2}' > /tmp/local_ip.txt")
            time.sleep(0.1)
            local_ip = ['*']
            with open('/tmp/local_ip.txt', 'r') as f:
                local_ip = f.readlines()
            if local_ip is None or len(local_ip) == 0:
                local_ip = ['*']
            datalogger_endpoint = {
                "downstream": "tcp://{}:{}".format(local_ip[1].strip(), int(zmqports.DATALOGGER_PUB) + self.site),
                "upstream": "tcp://{}:{}".format(local_ip[1].strip(), 10000 + int(zmqports.DATALOGGER_PUB) + self.site)
            }
            datalogger_publisher = ZmqPublisher(context, "tcp://*:{}".format(int(zmqports.DATALOGGER_PUB) + self.site), "datalogger")
            digitizer_endpoint = {
                "downstream": "tcp://{}:{}".format(local_ip[1].strip(), int(zmqports.DIGITIZER_PUB) + self.site),
                "upstream": "tcp://{}:{}".format(local_ip[1].strip(), 10000 + int(zmqports.DIGITIZER_PUB) + self.site)
            }

            self._drivers['_ssh'] = ssh

            callback = CallBack(self._drivers)
            self._drivers["callback"] = callback

            general = General(self._drivers)
            self._drivers["general"] = general

            test_item = TestItem(self._drivers)
            self._drivers["test_item"] = test_item

            ti_relay = TI_Relay(self._drivers)
            self._drivers["ti_relay"] = ti_relay

            ti_wolverine2 = TI_Wolverine2(self._drivers)
            self._drivers["ti_wolverine2"] = ti_wolverine2

            ti_datalogger = TI_Datalogger(mix_cfg, datalogger_endpoint, self._drivers, datalogger_publisher)
            self._drivers["ti_datalogger"] = ti_datalogger

            ti_digitizer = TI_Digitizer(mix_cfg, digitizer_endpoint, self._drivers)
            self._drivers["ti_digitizer"] = ti_digitizer

            ti_psu = TI_PSU(self._drivers)
            self._drivers["ti_psu"] = ti_psu

            ti_cal = TI_Cal(self._drivers)
            self._drivers["ti_cal"] = ti_cal

            ti_vdm = TI_VDM(self._drivers)
            self._drivers["ti_vdm"] = ti_vdm

            ti_freq = TI_Freq(self._drivers)
            self._drivers["ti_freq"] = ti_freq

            ti_adgrelay = TI_AdgRelay(self._drivers)
            self._drivers["ti_adgrelay"] = ti_adgrelay

            ti_uart = TI_UART(self._drivers)
            self._drivers["ti_uart"] = ti_uart

            ti_calmux = TI_Calmux(self._drivers)
            self._drivers["ti_calmux"] = ti_calmux

            ti_fixture = TI_Fixture(self._drivers)
            self._drivers["ti_fixture"] = ti_fixture

            ti_otp = TI_OTP(self._drivers)
            self._drivers["ti_otp"] = ti_otp

            ti_trinary = TI_Trinary(self._drivers)
            self._drivers["ti_trinary"] = ti_trinary
        except Exception as e:
            raise e

    def _register_functions(self):
        try:
            callback = self._drivers.get("callback")
            general = self._drivers.get("general")
            test_item = self._drivers.get("test_item")
            ti_relay = self._drivers.get("ti_relay")
            ti_wolverine2 = self._drivers.get("ti_wolverine2")
            ti_datalogger = self._drivers.get("ti_datalogger")
            ti_digitizer = self._drivers.get("ti_digitizer")
            ti_psu = self._drivers.get("ti_psu")
            ti_vdm = self._drivers.get("ti_vdm")
            ti_freq = self._drivers.get("ti_freq")
            ti_calmux = self._drivers.get("ti_calmux")
            ti_adgrelay = self._drivers.get("ti_adgrelay")
            ti_uart = self._drivers["ti_uart"]
            ti_dut = self._drivers["ti_dut"]
            ti_cal = self._drivers["ti_cal"]
            ti_fixture = self._drivers["ti_fixture"]
            ti_otp = self._drivers["ti_otp"]
            ti_trinary = self._drivers["ti_trinary"]
            _functions = {
                # callback
                "start_test": callback.start_test,
                "end_test": callback.end_test,
                "_my_rpc_server_is_ready": callback.sequencerRigister,

                # general
                "skip": general.skip,
                "vendor_id": general.vendor_id,
                'station_name': general.station_name,
                "fixture_id": general.fixture_id,
                "slot_id": general.slot_id,
                "delay": general.delay,
                'calculate': general.calculate,
                "scansn": general.scansn,

                # test_item
                'reset_board': test_item.reset_board,
                'reset_board_other': test_item.reset_board_other,
                'mix_fw_version': test_item.mix_fw_version,
                'check_ftdi': test_item.check_ftdi,
                "compare_mlbsn":test_item.compare_mlbsn,
                "aid_reset": test_item.aid_reset,
                "aid_wake_up": test_item.aid_wake_up,
                

                # ti_relay
                "relay_switch": ti_relay.relay_switch,

                # ti_wolverine2
                "measure_voltage": ti_wolverine2.measure_voltage,
                "wait_voltage_drop": ti_wolverine2.wait_voltage_drop,
                "wait_voltage_up": ti_wolverine2.wait_voltage_up,
                "read_dmm_sn": ti_wolverine2.read_dmm_sn,
                "w2_multi_sample": ti_wolverine2.w2_multi_sample,
                "w2_multi_verify": ti_wolverine2.w2_multi_verify,
                "get_duty_sample": ti_wolverine2.get_duty_sample,
                "get_toffmin_clksafety": ti_wolverine2.get_toffmin_clksafety,
                "get_ton_max_sample": ti_wolverine2.get_ton_max_sample,
                "clear_toffmin_data": ti_wolverine2.clear_toffmin_data,
                "measure_voltage_count": ti_wolverine2.measure_voltage_count,

                # ti_datalogger
                "datalogger_start": ti_datalogger.start,
                "datalogger_stop": ti_datalogger.stop,
                "read_dagger_sn": ti_datalogger.read_dagger_sn,
                "get_power_voltage": ti_datalogger.get_power_voltage,
                "get_power_current": ti_datalogger.get_power_current,
                "get_power_consumption": ti_datalogger.get_power_consumption,

                # ti_digitizer
                "digitizer_start": ti_digitizer.start,
                "digitizer_stop": ti_digitizer.stop,
                "digitizer_read_trigger_time": ti_digitizer.read_trigger_time,
                "parse_delay_time": ti_digitizer.parse_delay_time,
                "mux_measure": ti_digitizer.mux_measure,
                "parse_special_delay_time": ti_digitizer.parse_special_delay_time,
                "read_beast_sn": ti_digitizer.read_beast_sn,
                "parse_rise_first_data": ti_digitizer.parse_rise_first_data,
                "mux_tonmax_measure": ti_digitizer.mux_tonmax_measure,
                "beast_multi_sample_no_calulate": ti_digitizer.beast_multi_sample_no_calulate,
                "get_moto_data": ti_digitizer.get_moto_data,

                # ti_psu
                "psu_on": ti_psu.psu_power_on,
                "psu_off": ti_psu.psu_power_off,
                "psu_power_slower_on": ti_psu.psu_power_slower_on,

                "cal_psu_on": ti_psu.cal_psu_power_on,
                "cal_psu_off": ti_psu.cal_psu_power_off,

                # ti_cal
                "oqc_open": ti_cal.oqc_open,
                "oqc_close": ti_cal.oqc_close,
                "get_cal_voltage": ti_cal.get_cal_voltage,
                "get_cal_rigel_current": ti_cal.get_cal_rigel_current,
                "verify_rigel_current": ti_cal.verify_rigel_current,
                "verify_cal_voltage": ti_cal.verify_cal_voltage,
                "write_to_file": ti_cal.write_to_file,
                "read_cal_offset": ti_cal.read_cal_offset,
                # "get_cal_voltage_low": ti_cal.get_cal_voltage_low,
                "get_cal_dagger_current": ti_cal.get_cal_dagger_current,
                "verify_dagger_cal": ti_cal.verify_dagger_cal,
                "get_cal_beast_voltage": ti_cal.get_cal_beast_voltage,

                # ti_vdm
                "vdm_set_vdm_5v_3a": ti_vdm.set_vdm_5v_3a,
                "vdm_set_vdm_15v_5a": ti_vdm.set_vdm_15v_5a,
                "change_source_pdo_count": ti_vdm.change_source_pdo_count,
                "write_register_by_address": ti_vdm.write_register_by_address,
                "read_all_registers": ti_vdm.read_all_registers,
                

                # ti_freq
                "measure_freq": ti_freq.measure_freq,
                "beast_set_adc": ti_freq.beast_set_adc,
                "beast_measure_freq": ti_freq.beast_measure_freq,
                "vpp_measure": ti_freq.vpp_measure,
                "rms_measure": ti_freq.rms_measure,
                "pwm_out": ti_freq.pwm_out,
                "pwm_close": ti_freq.pwm_close,
                "pwm_set_freq_duty": ti_freq.pwm_set_freq_duty,

                # ti_adgrelay
                "adg_relay_switch": ti_adgrelay.adg_relay_switch,
                "reset_adg_relay": ti_adgrelay.reset_adg_relay,
                "adg_relay_with_dmm": ti_adgrelay.adg_relay_with_dmm,
                "adg_relay_with_oqc": ti_adgrelay.adg_relay_with_oqc,

                # ti_uart
                "uart_write": ti_uart.uart_write,
                "uart_read": ti_uart.uart_read,
                "uart_clear": ti_uart.uart_clear,

                # ti_calmux
                "calmux_switch": ti_calmux.calmux_switch,
                "calmux_init": ti_calmux.calmux_init,
                "calmux_relay_init": ti_calmux.calmux_relay_init,

                # ti_dut
                "detect_diags": ti_dut.detect_diags,
                "detect_recovery": ti_dut.detect_recovery,
                "diags": ti_dut.diags,
                "parse": ti_dut.parse,
                "diags_parse": ti_dut.diags_parse,
                "parse_i2c_read": ti_dut.parse_i2c_read,
                "diags_send": ti_dut.diags_send,
                "dut_communication_type": ti_dut.dut_communication_type,
                "i2c_detect": ti_dut.i2c_detect,
                "i2c_addr_detect_10times": ti_dut.i2c_addr_detect_10times,
                "open_dock_channel": ti_dut.open_dock_channel,
                "close_dock_channel": ti_dut.close_dock_channel,
                "query_dc_31336": ti_dut.query_dc_31336,
                "query_dc_41336": ti_dut.query_dc_41336,

                "parse_special": ti_dut.parse_special,
                "diags_turn_on_will_pmu": ti_dut.diags_turn_on_will_pmu,
                "diags_special": ti_dut.diags_special,
                "diags_durant_special": ti_dut.diags_durant_special,
                "diags_cio_special": ti_dut.diags_cio_special,
                "parse_audio_data": ti_dut.parse_audio_data,

                "31337.send": ti_dut.diags,
                "31336.send": ti_dut.query_dc_31336,

                "calculate_register": ti_dut.calculate_register,
                "diags_initialize_rigel": ti_dut.diags_initialize_rigel,
                "start_rigel_reg_read": ti_dut.start_rigel_reg_read,
                "stop_rigel_reg_read": ti_dut.stop_rigel_reg_read,

                "diags_silego_special": ti_dut.diags_silego_special,
                "get_silego_data": ti_dut.get_silego_data,
                "diags_for_sleep_test": ti_dut.diags_for_sleep_test,

                # ti_fixture
                "fixture_up": ti_fixture.reset_fixture,

                # ti_otp
                "read_version": ti_otp.read_version,
                "read_otp_existing_content": ti_otp.read_otp_existing_content,
                "calculate_ecc_content": ti_otp.calculate_ecc_content,
                "update_otp_header": ti_otp.update_otp_header,
                "sram_write": ti_otp.sram_write,
                "sram_verify": ti_otp.sram_verify,
                "write_reg_by_address": ti_otp.write_reg_by_address,
                "read_reg_by_address": ti_otp.read_reg_by_address,
                "efuse_pgm_mode_status_before": ti_otp.efuse_pgm_mode_status_before,
                "efuse_pgm_mode_status_after": ti_otp.efuse_pgm_mode_status_after,
                "check_otp_existing_content": ti_otp.check_otp_existing_content,



                "program_otp": ti_otp.program_otp,

                

                # ti_trinary
                "trinary_enable": ti_trinary.trinary_enable,
                "check_swire_path": ti_trinary.check_swire_path,
                "write_extend": ti_trinary.write_extend,
                "transport_commit": ti_trinary.transport_commit,
                "clear_seq_id": ti_trinary.clear_seq_id,
                "read_extend": ti_trinary.read_extend,
                "check_slave_attch_status": ti_trinary.check_slave_attch_status,



                "collect_debug_ref": self.collect_debug_ref
            }

            self._functions.update(_functions)
            self._drivers["all_function"] = self._functions
        except Exception as e:
            raise e

    def _init_hardware(self):
        try:
            pass
        except Exception as e:
            raise
    def collect_debug_ref(self, *args, **kwargs):
        _functions_dict = {"functions": self._functions.keys()}
        return _functions_dict

    @property
    def functions(self):
        return self._functions

    def get_module(self, name):
        return self._drivers.get(name)