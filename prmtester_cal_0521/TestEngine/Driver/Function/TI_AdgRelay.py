from ..Function.TI_Common import RootFunction
from ..Mapping.io_table import IOTable
from TI_Define import *


class TI_AdgRelay(RootFunction):
    def __init__(self, driver=None):
        super(TI_AdgRelay, self).__init__(driver)
        self.io_table = IOTable()
        self.obj_mix = None
        self.obj_adg_relay = None
        self.net = None
        self.sub_net = None
        self.temp_arrx = 0

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_adg_relay = self.obj_mix.objadgarray

    @handle_response
    def adg_relay_switch(self, *args, **kwargs):
        if len(args) == 2:
            net = args[0]
            sub_net = args[1]
        else:
            return "--FAIL--MISS-PARA"
        self.net = net
        self.sub_net = sub_net
        io = self.io_table.get_by_netname(net, sub_net, "ARRAY_RELAY_TABLE")
        self.obj_mix.log_hw("adg_relay_switch", "[net]={} [sub_net]={} [io_list]={}".format(net, sub_net, io))
        if io:
            for key, io_list in io.iteritems():
                if key == 'IO':
                    ret = self.obj_adg_relay.set_io_switch(io_list)
                    if ret:
                        self.obj_mix.log_hw("adg_relay_switch", "[result]={}".format(ret))
                        return "--PASS--"
                    else:
                        return "--FAIL--Switch IO fail"
        return "--FAIL--Can't find net"

    @handle_response
    def adg_relay_with_oqc(self, *args, **kwargs):
        if len(args) == 2:
            net = args[0]
            arrx = int(args[1])
        else:
            return "--FAIL--MISS-PARA"
        sub_net = "TO_DMM"
        if self.temp_arrx < 36:
            io_list = [[self.temp_arrx, 7, 0]]
            self.obj_mix.log_hw("adg_relay_with_oqc", "[io_list]={}".format(io_list))
            ret = self.obj_adg_relay.set_io_switch(io_list)
            self.temp_arrx = arrx
            if ret:
                self.obj_mix.log_hw("adg_relay_with_oqc", "[result]={}".format(ret))
            else:
                return "--FAIL--Switch IO fail"
        io = self.io_table.get_by_netname(net, sub_net, "ARRAY_RELAY_TABLE")
        self.obj_mix.log_hw("adg_relay_with_oqc", "[net]={} [sub_net]={} [io_list]={}".format(net, sub_net, io))
        if io:
            for key, io_list in io.iteritems():
                if key == 'IO':
                    ret = self.obj_adg_relay.set_io_switch(io_list)
                    if ret:
                        self.obj_mix.log_hw("adg_relay_with_oqc", "[result]={}".format(ret))
                        return "--PASS--"
                    else:
                        return "--FAIL--Switch IO fail"
        return "--FAIL--Can't find net"

 # connetor All GPIO to Y7DMM/GND/PP1V2/PP1V8/PP3V3(!IO_ASB)
    @handle_response
    def adg_relay_with_dmm(self, *args, **kwargs):
        if len(args) == 2:
            net = args[0]
            arrx = int(args[1])
        else:
            return "--FAIL--MISS-PARA"
        if net == "adg_array_reset":
            self.temp_arrx = 0
            self.obj_mix.log_hw("adg_relay_with_dmm", "[reset]={}".format(""))
            ret = self.obj_adg_relay.reset()
        else:
            if self.temp_arrx < 36:
                io_list = [[self.temp_arrx, 0, 0], [self.temp_arrx, 1, 0], [self.temp_arrx, 2, 0],
                           [self.temp_arrx, 3, 0], [self.temp_arrx, 7, 0]]
                self.obj_mix.log_hw("adg_relay_with_dmm", "[io_list]={}".format(io_list))
                ret = self.obj_adg_relay.set_io_switch(io_list)
                self.temp_arrx = arrx
                if ret:
                    self.obj_mix.log_hw("adg_relay_with_dmm 0", "[result]={}".format(ret))
                else:
                    ret = self.obj_adg_relay.set_io_switch(io_list)
                    if ret:
                        self.obj_mix.log_hw("adg_relay_with_dmm 0 try2", "[result]={}".format(ret))
                    else:
                        self.obj_mix.log_hw("adg_relay_with_dmm 0 FAIL", "[result]={}".format(ret))
                        return "--FAIL--Switch IO fail"
            if arrx < 36:
                io_list = [[arrx, 0, 1], [arrx, 1, 1], [arrx, 2, 1], [arrx, 3, 1], [arrx, 4, 0], [arrx, 5, 0],
                           [arrx, 6, 0], [arrx, 7, 1]]
                if "_IO_ASB" in net:  # Trinary_IO_ASB Change to _IO_ASB 20210617
                    io_list = [[arrx, 0, 1], [arrx, 1, 1], [arrx, 2, 0], [arrx, 3, 1], [arrx, 4, 0], [arrx, 5, 0],
                               [arrx, 6, 0], [arrx, 7, 1]]
                self.obj_mix.log_hw("adg_relay_with_dmm", "[io_list]={}".format(io_list))
                ret = self.obj_adg_relay.set_io_switch(io_list)

        if ret:
            self.obj_mix.log_hw("adg_relay_with_dmm", "[result]={}".format(ret))
            return "--PASS--"
        else:
            ret = self.obj_adg_relay.set_io_switch(io_list)
            if ret:
                self.obj_mix.log_hw("adg_relay_with_dmm try2", "[result]={}".format(ret))
                return "--PASS--"
            self.obj_mix.log_hw("adg_relay_with_dmm FAIL", "[result]={}".format(ret))
            return "--FAIL--Switch IO fail"

    @handle_response
    def adg_relay_with_dmm_bk(self, *args, **kwargs):
        if len(args) == 2:
            net = args[0]
            sub_net = args[1]
        else:
            return "--FAIL--MISS-PARA"
        io = self.io_table.get_by_netname(net, sub_net, "ARRAY_RELAY_TABLE")
        # self.obj_mix.log_hw("adg_relay_switch", "[net]={} [sub_net]={} [io_list]={}".format(net, sub_net, io))
        if io:
            for key, io_list in io.iteritems():
                if key == 'IO':
                    io_list[len(io_list) - 1][2] = 1
                    self.obj_mix.log_hw("adg_relay_with_dmm", "[io_list]={}".format(io_list))
                    ret = self.obj_adg_relay.set_io_switch(io_list)
                    if ret:
                        self.obj_mix.log_hw("adg_relay_switch", "[result]={}".format(ret))
                        return "--PASS--"
                    else:
                        return "--FAIL--Switch IO fail"
        return "--FAIL--Can't find net"
    @handle_response
    def reset_adg_relay(self, *args, **kwargs):
        self.obj_mix.log_hw("reset adg_relay_switch", "start")
        if self.obj_adg_relay:
            ret = self.obj_adg_relay.reset()
            self.obj_mix.log_hw("reset adg_relay_switch", "[result]={}".format(ret))
        return "--PASS--"



