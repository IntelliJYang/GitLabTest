from ..Function.TI_Common import RootFunction
from ..Mapping.calmux_table import MUXTable
from TI_Define import *


class TI_Calmux(RootFunction):
    def __init__(self, driver=None):
        super(TI_Calmux, self).__init__(driver)
        self.io_table = MUXTable()
        self.obj_mix = None
        self.obj_calmux = None
        self.net = None
        self.sub_net = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_calmux = self.obj_mix.objcalmux

    @handle_response
    def calmux_switch(self, *args, **kwargs):
        if len(args) == 2:
            net = args[0]
            sub_net = args[1]
            return self._relay_switch(net, sub_net)
        else:
            return "--FAIL--MISS-PARA"
    @handle_response
    def calmux_init(self, *args, **kwargs):
        return self.obj_calmux.module_init()
        

    @handle_response
    def calmux_relay_init(self, *args, **kwargs):
        return self.obj_calmux.relay_init()
        


    def _relay_switch(self, net, sub_net):
        self.net = net
        self.sub_net = sub_net
        io = self.io_table.get_by_netname(net, sub_net, "HWIO_RELAY_TABLE")
        self.obj_mix.log_hw("relay_switch", "[net]={} [sub_net]={} [io_list]={}".format(self.net, self.sub_net, io))
        if io:
            for key, io_list in io.iteritems():
                if key == 'IO':
                    ret = self.obj_calmux.set_io_switch(io_list)
                    self.obj_mix.log_hw("relay_switch", "[result]={}".format(ret))
                    if ret:
                        return "--PASS--"
                    else:
                        return "--FAIL--Switch IO fail"
        return "--FAIL--Can't find net"
