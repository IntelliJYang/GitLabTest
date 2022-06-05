from ..Function.TI_Common import RootFunction
from TI_Define import *


class TI_VDM(RootFunction):
    def __init__(self, driver=None):
        super(TI_VDM, self).__init__(driver)
        self.obj_mix = None
        self.obj_vdm = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_vdm = self.obj_mix.objvdm

    @handle_response
    def set_vdm_5v_3a(self, *args, **kwargs):
        self.obj_vdm.set_source_capabilities(1, 'PP_HVE', 5000, 3000)
        self.obj_vdm.set_source_capabilities(2, 'PP_HVE', 5000, 3000)
        self.obj_vdm.set_source_capabilities(3, 'PP_HVE', 5000, 3000)
        self.obj_vdm.set_source_capabilities(4, 'PP_HVE', 5000, 3000)
        self.obj_vdm.set_source_capabilities(5, 'PP_HVE', 5000, 3000)
        return "--PASS--"

    @handle_response
    def set_vdm_15v_5a(self, *args, **kwargs):
        self.obj_vdm.set_source_capabilities(1, 'PP_5V', 5000, 3000)
        self.obj_vdm.set_source_capabilities(2, 'PP_HVE', 15000, 5000)
        self.obj_vdm.set_source_capabilities(3, 'PP_HVE', 15000, 5000)
        self.obj_vdm.set_source_capabilities(4, 'PP_HVE', 15000, 5000)
        self.obj_vdm.set_source_capabilities(5, 'PP_HVE', 15000, 5000)
        return "--PASS--"

    @handle_response
    def change_source_pdo_count(self, *args, **kwargs):
        if len(args) <= 0:
            return MISSING_ENOUGH_PARA
        pdo_count = int(args[0])
        self.obj_vdm.change_source_pdo_count(pdo_count)
        return "--PASS--"

    @handle_response
    def write_register_by_address(self, *args, **kwargs):
        self.obj_vdm.write_register_by_address(0x28, 'ReceptacleType', 3)
        self.obj_vdm.write_register_by_address(0x47, 'Num Valid SOP Prime IDOs', 4)
        self.obj_vdm.write_register_by_address(0x47, 'VBUS Through Cable', 1)
        self.obj_vdm.write_register_by_address(0x47, 'VBUS Current Capability', 2)
        return "--PASS--"       

    @handle_response
    def read_all_registers(self, *args, **kwargs):
        self.obj_vdm.read_all_registers()
        return "--PASS--"       

