from ..Function.TI_Common import RootFunction
from ..Utility.utility import Unit
from TI_Define import *

import time
from time import sleep
from datetime import datetime

class TI_Trinary(RootFunction):
    def __init__(self, driver=None):
        super(TI_Trinary, self).__init__(driver)
        self.obj_mix = None
        self.obj_trinary = None
        self.swn_master = None
        self._seq_id = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_trinary = self.obj_mix.objtrinay
        self.swn_master = self.obj_mix.objotp
        self._seq_id = 0

    @handle_response
    def clear_seq_id(self, *args, **kwargs):
        self._seq_id = 0
        return "--PASS--"

    def wait_fifo_sufficient_space(self, reg, timeout_ms=1000):
        date_start = datetime.now()
        while True:
            val = self.swn_master.readRegisterByAddress(reg)
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(reg, val))
            if val > 0x2:
                return True
            if (datetime.now() - date_start).total_seconds() > (timeout_ms / 1000.0):
                return False
            sleep(0.1)

    def wait_fifo_not_full(self, reg, timeout_ms=1000):
        date_start = datetime.now()
        while True:
            val = self.swn_master.readRegisterByAddress(reg)
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(reg, val))
            if val > 0:
                return True
            if (datetime.now() - date_start).total_seconds() > (timeout_ms / 1000.0):
                return False
            sleep(0.1)
        
    def wait_fifo_not_empty(self, reg, timeout_ms=1000):
        date_start = datetime.now()
        while True:
            val = self.swn_master.readRegisterByAddress(reg)
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(reg, val))
            if val > 0:
                return True
            if (datetime.now() - date_start).total_seconds() > (timeout_ms / 1000.0):
                return False
            sleep(0.1)

    def _write_data_by_address(self, reg, value):
        self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(reg, value))
        self.swn_master.writeRegisterByAddress(reg, value)

    @handle_response
    def write_extend(self, *args, **kwargs): #attempted comments
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        reg = int(str(args[0]).rstrip(), 16)
        value = int(str(args[1]).rstrip(), 16)
        try:
            info_data_word = []
            word1 = (0x33 << 24) + (self._seq_id << 16) + (0<<11) + (0<<10) + (2<<8) + (0<<0) # 0x33010200
            self.obj_mix.log_hw("[seq_id]", "[result]=0x{:02X}".format(self._seq_id))
            self._seq_id = (self._seq_id + 1) & 0xFF

            if not self.wait_fifo_sufficient_space(0x630C):
                return "--FAIL--"
            

            info_data_word.append(word1)
            info_data_word.append(reg)
            info_data_word.append(value)
            for word in info_data_word:
                self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(0x6308, word))
                self.swn_master.writeRegisterByAddress(0x6308, word)
            if not self.wait_fifo_not_full(0x6304):
                return "--FAIL--"
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(0x6300, 0x16002))
            self.swn_master.writeRegisterByAddress(0x6300, 0x16002)
            if not self.wait_fifo_not_empty(0x6314):
                return "--FAIL--"
            val = self.swn_master.readRegisterByAddress(0x6310) # result = 0x0000064B
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(0x6310, val))
            if val == 0x64B:
                return "--PASS--"
            else:
                return "--FAIL--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[write_extended]", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def transport_commit(self, *args, **kwargs):

        try:
            transport_commit_word = (0x32 << 24) + (self._seq_id << 16) + (1 << 8)  # 0x32020100
            self.obj_mix.log_hw("[seq_id]", "[result]=0x{:02X}".format(self._seq_id))
            self._seq_id = (self._seq_id + 1) & 0xFF

            if not self.wait_fifo_sufficient_space(0x630C):
                return "--FAIL--"
            
            
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(0x6308, transport_commit_word))
            self.swn_master.writeRegisterByAddress(0x6308, transport_commit_word)
            if not self.wait_fifo_not_full(0x6304):
                return "--FAIL--"
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(0x6300, 0x8025))
            self.swn_master.writeRegisterByAddress(0x6300, 0x8025)
            if not self.wait_fifo_not_empty(0x6314):
                return "--FAIL--"
            val = self.swn_master.readRegisterByAddress(0x6310) # result = 0x000004FF
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(0x6310, val))
            if val == 0x4FF:
                return "--PASS--"
            else:
                return "--FAIL--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[transport_commit]", "[result]={}".format(e))
            return "--FAIL--"


    @handle_response
    def read_extend(self, *args, **kwargs): #attempted comments
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        reg = int(str(args[0]).rstrip(), 16)

        try:
            info_data_word = []
            word1 = (0x21 << 24) + (self._seq_id << 16) + (0 << 11) + (0 << 10) + (2 << 8) + (0 << 0)  # 0x21000200
            self.obj_mix.log_hw("[seq_id]", "[result]=0x{:02X}".format(self._seq_id))
            self._seq_id = (self._seq_id + 1) & 0xFF

            if not self.wait_fifo_sufficient_space(0x630C):
                return "--FAIL--"
            

            info_data_word.append(word1)
            info_data_word.append(reg)

            for word in info_data_word:
                self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(0x6308, word))
                self.swn_master.writeRegisterByAddress(0x6308, word)
            if not self.wait_fifo_not_full(0x6304):
                return "--FAIL--"
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(0x6300, 0x20E003))
            self.swn_master.writeRegisterByAddress(0x6300, 0x20E003)
            if not self.wait_fifo_not_empty(0x6314):
                return "--FAIL--"

            val = self.swn_master.readRegisterByAddress(0x6310) # result = 0x000002C6
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(0x6310, val))
            if val == 0x2C6:
                if not self.wait_fifo_not_empty(0x631C):
                    return "--FAIL--"
                val = self.swn_master.readRegisterByAddress(0x6318)
                ret = '0x{:08X}'.format(val)
                return ret
            else:
                return "--FAIL--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[write_extended]", "[result]={}".format(e))
            return "--FAIL--"


    @handle_response
    def check_slave_attch_status(self, *args, **kwargs):
        '''
        Args:
        Returns:
        Raises:     keyError: raises an PLFREQException
        Examples:
        '''
        # if self.status == False:
        #     return "--FAIL--"
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        reg = int(str(args[0]).rstrip(), 16)

        try:
            for i in range(3):
                value = self.swn_master.readRegisterByAddress(reg)
                ret = '0x{:08X}'.format(value)
                self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(reg, value))
                if value == 0x000000FF:
                    break
                else:
                    self.obj_mix.log_hw("[set_force_commit]", "[result]={}".format(i))
                    self.set_force_commit()
                sleep(1)
            return ret
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]={}".format(e))
            return "--FAIL--"

    def set_force_commit(self, *args, **kwargs):
        try:
            self._write_data_by_address(0x00006004, 0x00000004)
            self._write_data_by_address(0x0000600C, 0x00000003)
            self._write_data_by_address(0x00006014, 0x00000004)
            self._write_data_by_address(0x00006030, 0x0000000F)
            self._write_data_by_address(0x00006038, 0x00000001)
            self._write_data_by_address(0x00004504, 0x00010100)
            self._write_data_by_address(0x00004B04, 0x00010100)

            self._write_data_by_address(0x00006374, 0x00000001) # Force Commit
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]={}".format(e))
            return "--FAIL--"


    @handle_response
    def trinary_enable(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        device = str(args[0])
        mode = str(args[1])
        ret = self.obj_trinary.trinary_init(device, mode)
        if "done" in ret:
            return "--PASS--"
        else:
            return "--FAIL--"

    @handle_response
    def check_swire_path(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        device = str(args[0])
        ret = self.obj_trinary.check_swire_path(device)
        if "done" in ret:
            return "--PASS--"
        else:
            return "--FAIL--"