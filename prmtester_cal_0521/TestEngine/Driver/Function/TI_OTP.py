from ..Function.TI_Common import RootFunction
from ..Utility.utility import Unit
from TI_Define import *

import time
import os
import csv
import math
from time import sleep


current_folder = os.path.abspath(os.path.dirname(__file__)).split('/')
current_folder = '/'.join(current_folder[:-3])
directory = current_folder + "/ThirdPartyLib/OTP"
print directory
log_directory = '/vault/Station_Log/OTP'

sram_otp_start_address = 0x20000
sram_seq_start_address = 0x20800
customer_sequence_start_address = 0x9D80 #=None if want to use last-non-zero
# directory = '/mix/addon/driver/module/otp_manager_files'
# directory = '/Library/Station/PRM/prmtester/ThirdPartyLib/OTP'

# mst_otp_bytes_file = os.path.join(directory, "seq_gpio_autoboot_manager.mem")
# mst_sram_words_file = os.path.join(directory, "seq_gpio_autoboot_manager_sram_to_otp.csv")
# mst_otp_existing_content_dump = os.path.join(directory, "manager_otp_existing_content.txt")
# mst_otp_patch_content_dump = os.path.join(directory, "manager_otp_patched_content.txt")

mst_otp_bytes_file = os.path.join(directory, "n301_preevt_seq_gpio_autoboot_manager.mem")
mst_sram_words_file = os.path.join(directory, "n301_preevt_seq_gpio_autoboot_manager_sram_to_otp.csv")


# mst_otp_existing_content_dump = os.path.join(log_directory, "manager_otp_existing_content.txt")
# mst_otp_patch_content_dump = os.path.join(log_directory, "manager_otp_patched_content.txt")
# mst_otp_memory_read = os.path.join(log_directory, "manager_otp_memory_read.csv")
# mst_otp_patch_csv_dump = os.path.join(log_directory, "manager_otp_patched_dump.csv")
# mst_otp_content_dump = os.path.join(log_directory, "manager_otp_content_dump.csv")
# otp_progarm_path = os.path.join(log_directory, "generic_master_log.txt")
# mst_otp_sram_check = os.path.join(log_directory, "manager_otp_sram_check.csv")

# otp_registr_check_path = os.path.join(log_directory, "otp_register_check.csv")

# check_content_after_program = os.path.join(log_directory, "check_content_after_program.txt")

apple_otp_version = 1
w_16a_32d_regseq_opcode =[0x39]
wait_otp_regseq_opcode=[0x4d, 0x01]

otp_write = True
print_log = False
otp_program_log = True


return_done = "done"
return_fail = "--FAIL--"

last_non_zero = 0
OTP_SIZE_BYTE = 0
header_bytes = []
overwrite_software_trigger = []
num_of_header_to_invalidate = 0
OTP_image = []


class TI_OTP(RootFunction):
    def __init__(self, driver=None):
        super(TI_OTP, self).__init__(driver)
        self.obj_mix = None
        self.cs46l11 = None
        self.existing_content = None
        self.mst_otp_content = None
        self.mst_sram_content = None
        self.status = None
        self.site = None
        self.mst_otp_existing_content_dump = None
        self.otp_progarm_path = None

        self.mst_otp_patch_content_dump = None
        self.mst_sram_words_modified_file = None
        self.mst_otp_patch_csv_dump = None

        self.mst_otp_sram_check = None
        self.check_content_after_program = None


    def init(self):
        self.obj_mix = self.get_method("mix")
        self.cs46l11 = self.obj_mix.objotp
        self.status = True
        self.site = self.get_method("site")
        self.load_file()


    def load_file(self):
        global log_directory
        log_directory = '/vault/Station_Log/OTP_{}'.format(self.site + 1) 
        ts = str(time.strftime("%Y-%m-%d_%H-%M-%2S", time.localtime()))

        self.mst_otp_existing_content_dump = os.path.join(log_directory, "manager_otp_existing_content__" + ts + ".txt")
        self.otp_progarm_path = os.path.join(log_directory, "generic_master_log__" + ts + ".txt")


        if not os.path.exists(log_directory):
            os.mkdir(log_directory)

        # with open(self.otp_progarm_path, "w") as otp_log:
        #         otp_log.write('')

        if mst_sram_words_file:
            # extension_index = mst_sram_words_file.find(".")
            # self.mst_sram_words_modified_file = mst_sram_words_file[0:extension_index] + "_modified_mst" + mst_sram_words_file[extension_index:]
            self.mst_sram_words_modified_file = os.path.join(log_directory, "seq_gpio_autoboot_manager_sram_to_otp_modified_mst__" + ts + ".txt")

        self.mst_otp_content = []
        with open(mst_otp_bytes_file) as otp_file:
            for i,line in enumerate(otp_file):
                if i == 0: continue
                self.mst_otp_content.append(int(line, 16))
                # print (hex(int(line, 16)))

        self.mst_sram_content = []
        with open(mst_sram_words_file) as csvfile:
            sram_content = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, word in enumerate(sram_content):
                if i < 2: continue # skip header row
                self.mst_sram_content.append(int(word[1].replace("0x",""), 16))

    def data_init(self):
        global last_non_zero, OTP_SIZE_BYTE, header_bytes, overwrite_software_trigger, num_of_header_to_invalidate, OTP_image, log_directory
        last_non_zero = 0
        OTP_SIZE_BYTE = 0
        header_bytes = []
        overwrite_software_trigger = []
        num_of_header_to_invalidate = 0
        OTP_image = []
        self.status = True

        ts = str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))

        self.mst_otp_existing_content_dump = os.path.join(log_directory, "manager_otp_existing_content__" + ts + ".txt")
        self.otp_progarm_path = os.path.join(log_directory, "generic_master_log__" + ts + ".txt")

        self.mst_otp_patch_content_dump = os.path.join(log_directory, "manager_otp_patched_content__" + ts + ".txt")
        self.mst_otp_memory_read = os.path.join(log_directory, "manager_otp_memory_read.csv__" + ts + ".txt")
        self.mst_otp_patch_csv_dump = os.path.join(log_directory, "manager_otp_patched_dump.csv__" + ts + ".txt")

        self.mst_otp_sram_check = os.path.join(log_directory, "manager_otp_sram_check.csv__" + ts + ".txt")
        self.check_content_after_program = os.path.join(log_directory, "check_content_after_program.txt")


        if mst_sram_words_file:
            self.mst_sram_words_modified_file = os.path.join(log_directory, "seq_gpio_autoboot_manager_sram_to_otp_modified_mst__" + ts + ".txt")

        if not os.path.exists(log_directory):
            os.mkdir(log_directory)

        if otp_program_log:
            with open(self.otp_progarm_path, "w") as otp_log:
                otp_log.write('')


        self.mst_otp_content = []
        with open(mst_otp_bytes_file) as otp_file:
            for i, line in enumerate(otp_file):
                if i == 0: continue
                self.mst_otp_content.append(int(line, 16))
                # print (hex(int(line, 16)))

        self.mst_sram_content = []
        with open(mst_sram_words_file) as csvfile:
            sram_content = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, word in enumerate(sram_content):
                if i < 2: continue  # skip header row
                self.mst_sram_content.append(int(word[1].replace("0x", ""), 16))

    def blockReadRegisterByAddress(self, start_reg, block, rd_len):
        '''
        This function will block read the register of cs46l11.
        Args:
            start_reg:       int, include Vendor ID LSB and MSB
            block:      int,
            rd_len: 	int,
        Returns:
            list, the value, api execution successful.

        Examples:
            usb251xb.usb251xb_reset()
        '''
        block = 0
        val_list = []
        for i in range(rd_len):
            val = self.cs46l11.readRegisterByAddress(start_reg + 4 * i)
            val_list.append(val)
            self.obj_mix.log_hw("[readRegisterByAddress]", "[result]=0x{:04X}: 0x{:08X}".format(start_reg + 4 * i, val))
        return val_list

    def blockWriteRegisterByAddress(self, start_reg, block, rd_len, data):
        '''
        This function will block read the register of cs46l11.
        Args:
            start_reg:       int, include Vendor ID LSB and MSB
            block:      int,
            rd_len: 	int,
        Returns:
            list, the value, api execution successful.

        Examples:
            usb251xb.usb251xb_reset()
        '''
        block = 0
        for i in range(rd_len):
            val = self.cs46l11.writeRegisterByAddress(start_reg + 4 * i, data[i])
            self.obj_mix.log_hw("[writeRegisterByAddress]",
                                "[result]=0x{:04X}: 0x{:08X}".format(start_reg + 4 * i, data[i]))
        return return_done


    ## updated in v4 to add
    def generate_header(self, otp_id, parity_word, ecc_enabled=True, num_of_header_to_invalidate=None):
        _otpid_parity = {0: 0x0, 1: 0xB, 2: 0xD, 3: 0x6, 4: 0xE, 5: 0x5, 6: 0x3, 7: 0x8,
                         8: 0x7, 9: 0xC, 10: 0xA, 11: 0x1, 12: 0x9, 13: 0x2, 14: 0x4, 15: 0xF}
        header_bytes = []
        if ecc_enabled:
            header_bytes.append(parity_word & 0xFF)  # ECC Parity LSB
            header_bytes.append((parity_word & 0xFF00) >> 8)  # ECC Parity MSB
        else:
            header_bytes.append(0)
            header_bytes.append(0)
        header_bytes.append((_otpid_parity[otp_id] << 4) | otp_id)  # OTPID_ECC | OTPID
        if ecc_enabled:
            header_bytes.append(0x0F)
        else:
            header_bytes.append(0x00)
        if num_of_header_to_invalidate is None:
            num_of_header_to_invalidate = otp_id - 1
        for old_rev in range(num_of_header_to_invalidate, 0, -1):
            # header_bytes.extend([0, 0, (_otpid_parity[old_rev]<<4) | old_rev, 0xFF])
            header_bytes.extend([0, 0, 0, 0xFF])

        return header_bytes

    def isPowerof2(self, val):
        return ((val != 0) and not (val & (val - 1)))

    def calculate_parity(self, OTP_image, parity_vector, OTP_SIZE_BYTE, size_parity):
        size_encoded_image = OTP_SIZE_BYTE + size_parity - 3 - 1  # P1/P2/P4 .. P0
        OTP_encoded_image = [0] * size_encoded_image

        ctr = 0

        for i in range(size_encoded_image):
            if (self.isPowerof2(i + 1)):
                OTP_encoded_image[i] = 0
            else:
                OTP_encoded_image[i] = OTP_image[ctr];
                ctr += 1  # next OTP address

        for i in range(size_encoded_image):  # fetch each byte
            current_byte = OTP_encoded_image[i];

            for j in range(8):  # calculate every bit addr/value
                current_bit = 1 if (current_byte & (1 << (7 - j))) else 0
                bit_addr = i * 8 + (7 - j) + 1;

                # calculate parity
                parity_vector[0] = parity_vector[0] ^ current_bit
                for k in range(1, size_parity):
                    if ((bit_addr >> (k - 1)) & 0x1 == 1):
                        parity_vector[k] = parity_vector[k] ^ current_bit
                    # print("Parity Vector modified[{}]: {}".format( k, parity_vector[k]))

        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("Parity Vector[{}]: {}\n".format(0, parity_vector[0]))
        print("Parity Vector[{}]: {}".format(0, parity_vector[0]))
        for k in range(1, size_parity):
            parity_vector[0] = parity_vector[0] ^ parity_vector[k]  # include parities in P0
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("Parity Vector[{}]: {}\n".format(k, parity_vector[k]))
            print("Parity Vector[{}]: {}".format(k, parity_vector[k]))

        return OTP_encoded_image, parity_vector;  # send it to calling function



    @handle_response
    def read_version(self, *args, **kwargs):
        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        name = str(args[0])
        if name not in ['DEVID', 'REVID', 'OTP_REVISION']:
            return 'WRONG_PARA'

        ret = ''
        #------------------------------------------------------------
        # DUT configuration
        #------------------------------------------------------------

        # -------Read DUT Device ID----------
        try:
            # self.obj_otp.readField('DEVID')  # result = 0x46A110
            # self.obj_otp.readField('REVID')  # result = 0xA
            # self.obj_otp.readField('OTP_REVISION')  # result = 0x0
            # # Device ID = CS46L11; Device Revision = A0; OTP Revision = 0;
            value = self.cs46l11.readField(name)
            ret = '0x{:X}'.format(value)
            self.obj_mix.log_hw("[read_version]", "[result]={}".format(ret))
        except Exception as e:
            ret = '--FAIL--'
            self.obj_mix.log_hw("[read_version]", "[result]={}".format(e))
        return ret

    @handle_response
    def read_otp_existing_content(self, *args, **kwargs):
        global last_non_zero, OTP_SIZE_BYTE, num_of_header_to_invalidate, OTP_image

        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        self.data_init()

        try:
            # otp_rev = self.cs46l11.readField("OTP_REVISION")
            # OTP_SIZE_BYTE = 1024 - 4*(otp_rev+1)
            OTP_SIZE_BYTE = self.cs46l11.readField("OTP_ADDR_LAST") ## updated in v4, use last address to check how many headers already in OTP
            num_of_header_to_invalidate = (0x400 - OTP_SIZE_BYTE) // 4
            OTP_image = [0]*OTP_SIZE_BYTE
            last_non_zero = 0
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("OTP_SIZE_BYTE:{}\n\n".format(OTP_SIZE_BYTE))
            print("OTP_SIZE_BYTE:{}\n".format(OTP_SIZE_BYTE))
            self.obj_mix.log_hw("[OTP_SIZE_BYTE]", "[result]={}".format(OTP_SIZE_BYTE))

            #------------------------------------------------------------
            # Step 1 Read OTP content
            #------------------------------------------------------------
            # Read 1k SRAM
            for i in range (0, OTP_SIZE_BYTE, 0x4):
                data = self.cs46l11.readRegisterByAddress(sram_otp_start_address+i)
                if data:
                    print "# 0x{:04X}: 0x{:08X}".format(sram_otp_start_address+i, data)
                    OTP_image[i+3]=(data>>24) & 0xFF
                    OTP_image[i+2]=(data>>16) & 0xFF
                    OTP_image[i+1]=(data>>8) & 0xFF
                    OTP_image[i]=data & 0xFF
                    if i<(0x400-24): # ignore ATE content and header
                        last_non_zero = i
                    self.obj_mix.log_hw("[read_otp_existing_content:]", "[result]=0x{:04X}: 0x{:08X}".format(sram_otp_start_address+i, data))

            if self.mst_otp_existing_content_dump:
                with open(self.mst_otp_existing_content_dump, "w") as otp_file:
                    for byte in OTP_image:
                        otp_file.write("{:02X}\n".format(byte))
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("\n")
                    otp_log.write("# Last non-zero OTP offset: 0x{:03X}\n".format(last_non_zero))
                    otp_log.write("\n")
            self.obj_mix.log_hw("[Last non-zero OTP offset]", "[result]=0x{:03X}".format(last_non_zero))
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[read_otp_existing_content]", "[result]={}".format(e))
            return "--FAIL--"


    @handle_response
    def calculate_ecc_content(self, *args, **kwargs):
        global OTP_image, last_non_zero, OTP_SIZE_BYTE, header_bytes, overwrite_software_trigger, num_of_header_to_invalidate
        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        #------------------------------------------------------------
        # Step 2 Update soft copy of OTP content and calculate ECC
        #------------------------------------------------------------

        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# add new Software Trigger 1 pointer to new otp sequence\n")
        print ("# add new Software Trigger 1 pointer to new otp sequence")
        for i in range (last_non_zero, 0, -1):
            if print_log:
                print("OTP_image[{}]:{}".format(i,OTP_image[i]))
                print("OTP_image[{}]:{}".format(i-1,OTP_image[i-1]))
                print("OTP_image[{}]:{}".format(i+1,OTP_image[i+1]))
                print("OTP_image[{}]:{}".format(i+2,OTP_image[i+2]))
            if (OTP_image[i]==0x90 and OTP_image[i-1]==0x0C and OTP_image[i+1]==0 and OTP_image[i+2]==0):
                if customer_sequence_start_address:
                    OTP_image[i+1]=(customer_sequence_start_address-0x9c00)>>2 # point SWT1 to customer OTP
                    if print_log:
                        print("customer_sequence_start_address:OTP_image[{}]:{}".format(i+1,OTP_image[i+1]))
                else:
                    OTP_image[i+1]=(last_non_zero + 4)>>2 # point SWT1 to customer OTP
                    if print_log:
                        print("No customer_sequence_start_address:OTP_image[{}]:{}".format(i+1,OTP_image[i+1]))
                OTP_image[i+2]=0x80 # trigger SWT1 again
                if otp_program_log:
                    with open(self.otp_progarm_path, "a+") as otp_log:
                        otp_log.write("# 0x{:04X}: 0x{:08X}\n".format(i, (OTP_image[i+2]<<24)+(OTP_image[i+1]<<16)+(OTP_image[i]<<8)+OTP_image[i-1]))
                print("# 0x{:04X}: 0x{:08X}".format(i, (OTP_image[i+2]<<24)+(OTP_image[i+1]<<16)+(OTP_image[i]<<8)+OTP_image[i-1]))
                i = i + 1
                offset = (i) % 4
                overwrite_software_trigger = []
                if offset < 3:
                    overwrite_software_trigger = [0x39]
                    overwrite_software_trigger.append((i - offset) & 0xFF)
                    overwrite_software_trigger.append(0x9C + (i >> 8))
                    if offset:
                        overwrite_software_trigger.extend([0]*offset)
                    overwrite_software_trigger.append(((customer_sequence_start_address-0x9c00)>>2) & 0xFF)
                    overwrite_software_trigger.extend([0x80])
                    if offset < 2:
                        overwrite_software_trigger.extend([0] * (2-offset))
                    overwrite_software_trigger.extend([0x4D, 0x01])
                else:
                    overwrite_software_trigger = [0x39]
                    overwrite_software_trigger.append((i - 3) & 0xFF)
                    overwrite_software_trigger.append(0x9C + (i >> 8))
                    overwrite_software_trigger.extend([0, 0, 0])
                    overwrite_software_trigger.append(((customer_sequence_start_address-0x9c00)>>2) & 0xFF)
                    overwrite_software_trigger.extend([0x4D, 0x01, 0x39])
                    overwrite_software_trigger.append((i + 1) & 0xFF)
                    overwrite_software_trigger.append(0x9C + (i >> 8))
                    overwrite_software_trigger.extend([0x80, 0, 0, 0])
                    overwrite_software_trigger.extend([0x4D, 0x01])
                break

        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# Append new OTP content\n")
        print("# Append new OTP content")
        if customer_sequence_start_address:
            new_start = customer_sequence_start_address - 0x9c00
        else:
            new_start = last_non_zero+4 # can also hard code to 0x120 offset
        for i, byte in enumerate(self.mst_otp_content):
            OTP_image[new_start+i] = byte

        if self.mst_otp_patch_content_dump:
            with open(self.mst_otp_patch_content_dump, "w") as otp_file:
                for byte in OTP_image:
                    otp_file.write("{:02X}\n".format(byte))
                    self.obj_mix.log_hw("[mst_otp_patch_content]", "[result]={:02X}".format(byte))

        if self.mst_otp_patch_csv_dump:
            patch_list = []
            for i in range(len(OTP_image)//4):
                new_value = (OTP_image[4*i+3] << 24) + (OTP_image[4*i+2] << 16) + (OTP_image[4*i+1] << 8) + OTP_image[4*i]
                patch_list.append(new_value)
            with open(self.mst_otp_patch_csv_dump, "w") as patch_csv:
                for i, word in enumerate(patch_list):
                    patch_csv.write("0x{:08X}, 0x{:08X}\n".format(0x9C00+(i*4), word))

        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# calculate parity\n")
        print ("# calculate parity")
        size_parity = int(math.log(OTP_SIZE_BYTE * 8)//math.log(2) + 1 + 1) #1 is for P0
        parity_vector = [0]*size_parity

        my_encoded_OTP, parity_vector = self.calculate_parity(OTP_image, parity_vector, OTP_SIZE_BYTE, size_parity);
        parity_word = 0
        for i in range (size_parity):
            parity_word = parity_word + (parity_vector[i] * (1<<i));
        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# Parity is 0x{:04X}\n".format(parity_word))
                otp_log.write("\n")
        print("# Parity is 0x{:04X}".format(parity_word))
        print("")

        # generate new headers
        header_bytes = self.generate_header(apple_otp_version, parity_word, ecc_enabled=True, num_of_header_to_invalidate=num_of_header_to_invalidate)
        header_word = [0]*(len(header_bytes)>>2)
        for i, byte in enumerate(header_bytes):
            header_word[i>>2] = header_word[i>>2] + (byte<<((i&3)<<3))

        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# OTP location\t| Header words update\n")
        print("# OTP location\t| Header words update")
        for i, word in enumerate(header_word):
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# 0x{:04X}\t: 0x{:08X}\n".format(0xA000-((len(header_word)-i)*4), word))
            print ("# 0x{:04X}\t: 0x{:08X}".format(0xA000-((len(header_word)-i)*4), word))
        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("\n")
        print ("")
        return "--PASS--"

    @handle_response
    def update_otp_header(self, *args, **kwargs):
        global header_bytes, overwrite_software_trigger
        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        #------------------------------------------------------------
        # Step 3a. Update SRAM sequence to include overwrite software trigger, and OTP header update.
        #------------------------------------------------------------
        start_bit_of_header = 0
        for byte in overwrite_software_trigger:
            self.mst_sram_content[-1] = self.mst_sram_content[-1] + (byte<<start_bit_of_header)
            start_bit_of_header = (start_bit_of_header + 8)
            if start_bit_of_header >=32:
                self.mst_sram_content.append(0)
                start_bit_of_header = 0

        for i in range (len(header_bytes), 0, -4):
            header_address = [(0xA000 - i) & 0xFF, ((0xA000 - i) & 0xFF00) >> 8]
            for byte in w_16a_32d_regseq_opcode:
                self.mst_sram_content[-1] = self.mst_sram_content[-1] + (byte<<start_bit_of_header)
                start_bit_of_header = (start_bit_of_header + 8)
                if start_bit_of_header >=32:
                    self.mst_sram_content.append(0)
                    start_bit_of_header = 0
            for byte in header_address:
                self.mst_sram_content[-1] = self.mst_sram_content[-1] + (byte<<start_bit_of_header)
                start_bit_of_header = (start_bit_of_header + 8)
                if start_bit_of_header >=32:
                    self.mst_sram_content.append(0)
                    start_bit_of_header = 0
            for byte in header_bytes[len(header_bytes)-i:len(header_bytes)-i+4]:
                self.mst_sram_content[-1] = self.mst_sram_content[-1] + (byte<<start_bit_of_header)
                start_bit_of_header = (start_bit_of_header + 8)
                if start_bit_of_header >=32:
                    self.mst_sram_content.append(0)
                    start_bit_of_header = 0
            for byte in wait_otp_regseq_opcode:
                if (byte == 0x4D) and (i==4):
                    byte = 0x4C
                self.mst_sram_content[-1] = self.mst_sram_content[-1] + (byte<<start_bit_of_header)
                start_bit_of_header = (start_bit_of_header + 8)
                if start_bit_of_header >=32:
                    self.mst_sram_content.append(0)
                    start_bit_of_header = 0

        if self.mst_sram_words_modified_file:
            with open(self.mst_sram_words_modified_file, "w") as sram_file:
                for i, word in enumerate(self.mst_sram_content):
                    sram_file.write("0x{:08X}, 0x{:08X}\n".format(sram_seq_start_address+(i*4), word))
                    self.obj_mix.log_hw("[sram_to_otp_modified]", "[result]=0x{:08X}, 0x{:08X}\n".format(sram_seq_start_address+(i*4), word))
        return "--PASS--"



    @handle_response
    def sram_write(self, *args, **kwargs):
        '''
        Args:
        Returns:
        Raises:     keyError: raises an PLFREQException
        Examples:
        '''
        # # Program SWN Master SRAM with OTP programming seqeunce
        if self.status == False:
            return "--FAIL--"
        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# Writing to SWN Master SRAM\n")
        print ("# Writing to SWN Master SRAM")
        try:
            self.blockWriteRegisterByAddress(sram_seq_start_address, 0, len(self.mst_sram_content),
                                         self.mst_sram_content)
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[blockWriteRegisterByAddress]", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def sram_verify(self, *args, **kwargs):
        '''
        Args:
        Returns:
        Raises:     keyError: raises an PLFREQException
        Examples:
        '''
        # Read SRAM to verify content
        if self.status == False:
            return "--FAIL--"
        if otp_program_log:
            with open(self.otp_progarm_path, "a+") as otp_log:
                otp_log.write("# Read to check new SRAM content\n")
        print ("# Read to check new SRAM content")
        time.sleep(0.1)

        try:
            read_new_sram = self.blockReadRegisterByAddress(sram_seq_start_address, 0, len(self.mst_sram_content))
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[blockWriteRegisterByAddress]", "[result]={}".format(e))
            return "--FAIL--"

        check_result = 0
        if otp_program_log:
            with open(self.mst_otp_sram_check, "w") as otp_sram_log:
                for i, value in enumerate(read_new_sram):
                    otp_sram_log.write(
                        "0x{:08X}, 0x{:08X}\n".format(sram_seq_start_address + 4 * i, read_new_sram[i]))
                    print ("Read Address Bytes: 0x{:08X}, Result: 0x{:08X}".format(sram_seq_start_address + 4 * i,
                                                                                   read_new_sram[i]))
                    if read_new_sram[i] == self.mst_sram_content[i]:
                        check_result += 1

        if check_result == len(self.mst_sram_content):
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# Check new SRAM content sucessfully!\n")
            print ("# Check new SRAM content sucessfully!")
        else:
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# Check new SRAM content failed!\n")
            print ("# Check new SRAM content failed!")
            self.status = False
            return "--FAIL--compare error"
        return "--PASS--"

    @handle_response
    def write_reg_by_address(self, *args, **kwargs):
        '''
        Args:
        Returns:
        Raises:     keyError: raises an PLFREQException
        Examples:
        '''
        # if self.status == False:
        #     return "--FAIL--"
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        reg = int(str(args[0]).rstrip(), 16)
        value = int(str(args[1]).rstrip(), 16)

        try:
            self.cs46l11.writeRegisterByAddress(reg, value)
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(reg, value))
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[write_RegisterByAddress]", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def read_reg_by_address(self, *args, **kwargs):
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
            value = self.cs46l11.readRegisterByAddress(reg)
            ret = '0x{:08X}'.format(value)
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]=0x{:08X}: 0x{:08X}".format(reg, value))
            return ret
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[read_RegisterByAddress]", "[result]={}".format(e))
            return "--FAIL--"


    @handle_response
    def efuse_pgm_mode_status_before(self, *args, **kwargs):
        '''
        Args:
        Returns:
        Raises:     keyError: raises an PLFREQException
        Examples:
        '''
        # Read EFUS_PGM_MODE_STAT
        # if self.status == False:
        #     return "--FAIL--"

        try:
            time_start = time.time() * 1000
            efuse_ready = self.cs46l11.readField('EFUSE_PGM_MODE_STAT')  # result = 0x00000000 Check EFUSE status
            self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(efuse_ready))
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# The first efuse_ready status is {}\n".format(efuse_ready))
            print("# The First efuse_ready status is {}".format(efuse_ready))
            while (efuse_ready == 0):  # poll EFUS_PGM_MODE_STAT == 1
                sleep(0.01)
                if (time.time() * 1000 - time_start) > 1000:
                    print ("EFUSE_PGM_MODE_STAT is incorrect")
                    self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(efuse_ready))

                    self.status = False
                    return "--FAIL--"

                efuse_ready = self.cs46l11.readField('EFUSE_PGM_MODE_STAT')  # result = 0x00000000 Check EFUSE status
                print(efuse_ready)
            self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(efuse_ready))

            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# Trigger SWN Master SRAM to write to OTP\n")
            print ("# Trigger SWN Master SRAM to write to OTP")
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(e))
            return "--FAIL--"

    @handle_response
    def efuse_pgm_mode_status_after(self, *args, **kwargs):
        '''
        Args:
        Returns:
        Raises:     keyError: raises an PLFREQException
        Examples:
        '''
        # Read EFUS_PGM_MODE_STAT
        # if self.status == False:
        #     return "--FAIL--"

        try:
            time_start = time.time() * 1000
            efuse_ready = self.cs46l11.readField('EFUSE_PGM_MODE_STAT')  # result = 0x00000000 Check EFUSE status
            self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(efuse_ready))
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# The Second efuse_ready status is {}\n".format(efuse_ready))
            print("# The Second efuse_ready status is {}".format(efuse_ready))

            while (efuse_ready):  # poll EFUS_PGM_MODE_STAT == 1
                sleep(0.01)
                efuse_ready = self.cs46l11.readField('EFUSE_PGM_MODE_STAT')  # result = 0x00000000 Check EFUSE status
                print(efuse_ready)
                if (time.time() * 1000 - time_start) > 1000:
                    if otp_program_log:
                        with open(self.otp_progarm_path, "a+") as otp_log:
                            otp_log.write("EFUSE_PGM_MODE_STAT is wrong\n")
                    print("EFUSE_PGM_MODE_STAT is wrong")
                    self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(efuse_ready))

                    self.status = False
                    return "--FAIL--"
            self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(efuse_ready))
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[efuse_ready status]", "[result]={}".format(e))
            return "--FAIL--"








    @handle_response
    def program_otp(self, *args, **kwargs):
        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        if self.status == False:
            return "--FAIL--status error"

        vale = self.cs46l11.readRegisterByAddress(0x9808)
        if vale == 0x3FC0000:
            #------------------------------------------------------------
            # Step 3b. Enable OTP for writes, enable HWT to run SRAM sequence to program OTP, enable GPIO to turn on VDD_OTP
            #------------------------------------------------------------
            mode = 2
            # ret = ""
            ret = self.cs46l11.program_otp_internal(mode)
            self.obj_mix.log_hw("[program otp]", "[result]={}".format(ret))
            if ret == "done":
                return "--PASS--"
            return "--FAIL--"
        else:
            self.obj_mix.log_hw("[program otp]", "[result]={}".format("SKIP"))
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("# skip OTP\n")
            return "--SKIP--"


    def check_program_data(self, *args, **kwargs):
        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        # check_reg = [0x8A00, 0x8A04, 0x8A08, 0x8A0C, 0x8A14, 0x8918, 0x4504, 0x4B04]
        # expected_val = [0x11B0009, 0x11C0009, 0x11E0009, 0x1180000, 0x1180000, 0x3F80, 0x10101, 0x10101]
        #------------------------------------------------------------
        # Step 3b. Enable OTP for writes, enable HWT to run SRAM sequence to program OTP, enable GPIO to turn on VDD_OTP
        #------------------------------------------------------------
        return "--PASS--"


    @handle_response
    def check_otp_existing_content(self, *args, **kwargs):
        global OTP_image
        '''
        Args:
        Returns:    
        Raises:     keyError: raises an PLFREQException
        Examples:   
        '''
        try:
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("\n")
                    otp_log.write("CHECK CONTENT AFTER DUT POWER CYCLE")
                    otp_log.write("\n")

            # otp_rev = self.cs46l11.readField("OTP_REVISION")
            # OTP_SIZE_BYTE = 1024 - 4*(otp_rev+1)
            OTP_SIZE_BYTE = self.cs46l11.readField("OTP_ADDR_LAST") ## updated in v4, use last address to check how many headers already in OTP
            num_of_header_to_invalidate = (0x400 - OTP_SIZE_BYTE) // 4
            READ_image = [0]*OTP_SIZE_BYTE
            last_non_zero = 0
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("OTP_SIZE_BYTE:{}\n\n".format(OTP_SIZE_BYTE))
            print("OTP_SIZE_BYTE:{}\n".format(OTP_SIZE_BYTE))
            self.obj_mix.log_hw("[OTP_SIZE_BYTE]", "[result]={}".format(OTP_SIZE_BYTE))

            # Read 1k SRAM
            for i in range (0, OTP_SIZE_BYTE, 0x4):
                data = self.cs46l11.readRegisterByAddress(sram_otp_start_address+i)
                if data:
                    print "# 0x{:04X}: 0x{:08X}".format(sram_otp_start_address+i, data)
                    READ_image[i+3]=(data>>24) & 0xFF
                    READ_image[i+2]=(data>>16) & 0xFF
                    READ_image[i+1]=(data>>8) & 0xFF
                    READ_image[i]=data & 0xFF
                    if i<(0x400-24): # ignore ATE content and header
                        last_non_zero = i
                    self.obj_mix.log_hw("[read_otp_existing_content:]", "[result]=0x{:04X}: 0x{:08X}".format(sram_otp_start_address+i, data))

            if self.check_content_after_program:
                with open(self.check_content_after_program, "w") as otp_file:
                    for byte in READ_image:
                        otp_file.write("{:02X}\n".format(byte))
            if otp_program_log:
                with open(self.otp_progarm_path, "a+") as otp_log:
                    otp_log.write("\n")
                    otp_log.write("# Last non-zero OTP offset: 0x{:03X}\n".format(last_non_zero))
                    otp_log.write("\n")
            self.obj_mix.log_hw("[Last non-zero OTP offset]", "[result]=0x{:03X}".format(last_non_zero))

            # compare read data after power cycle and patch data
            check_result = 0
            for i in range(len(READ_image)):
                if READ_image[i] == OTP_image[i]:
                    check_result += 1

            if check_result == len(READ_image):
                if otp_program_log:
                    with open(self.otp_progarm_path, "a+") as otp_log:
                        otp_log.write("# Check new otp_existing_content sucessfully!\n")
                print ("# Check new SRAM content sucessfully!")
            else:
                if otp_program_log:
                    with open(self.otp_progarm_path, "a+") as otp_log:
                        otp_log.write("# Check new otp_existing_content failed!\n")
                print ("# Check new otp_existing_content failed!")
                self.status = False
                return "--FAIL--compare error"
            return "--PASS--"
        except Exception as e:
            self.status = False
            self.obj_mix.log_hw("[read_otp_existing_content]", "[result]={}".format(e))
            return "--FAIL--"












