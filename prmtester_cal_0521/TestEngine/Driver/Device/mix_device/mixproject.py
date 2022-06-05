# -*-coding:utf-8 -*-
from mix.lynx.rpc.profile_client import RPCClientWrapper
from sg.mixpsmux import ps_mux
from sg.mixsgw2 import sgw2
from sg.mixsgpsu import sgpsu
from sg.mixsguart import sguart
from sg.mixvdm import vdm
from prm.mixqpsi import qspi
from prm.mixwibEEprom import wibEEprom
from prm.mixrelay import relay
from prm.mixadgarray import adgarray
from prm.mixfreq import freql
from prm.mixtrinary import trinary
from prm.mixaid import aidslave
from prm.mixotp import otpmanager
from prm.mixcalmux import calmux

class MixUseInProject:
    def __init__(self, client):
        self.client = client
        self.objps_mux = ps_mux(client)
        self.objsgw2 = sgw2(client)
        self.objsgpsu = sgpsu(client)
        self.objsguart = sguart(client)
        self.objvdm = vdm(client)
        self.objqspi = qspi(client)
        self.objwibEEprom = wibEEprom(client)
        self.objrelay = relay(client)
        self.objadgarray = adgarray(client)
        self.objfreql = freql(client)
        self.objtrinay = trinary(client)
        self.objaid = aidslave(client)
        self.objotp = otpmanager(client)
        self.logging_time = None
        self.objcalmux = calmux(client)

    def set_logging_time(self, time):
        self.logging_time = time

    def log_hw(self, title, data):
        if self.client.publisher:
            self.client.publisher.publish('[{}]:    {}\r\n'.format(title, data))

    def reset_mix(self):
        try:
            self.client.dma_ip.reset_channel(1)
            self.client.dma_ip.reset_channel(2)
            self.objsgw2.reset()
            self.objsgpsu.module_init()
            self.objps_mux.board_init()
            # self.objvdm.module_init()
            # self.objrelay.module_init()
            self.objrelay.reset_all()
            self.objadgarray.reset()    # should be the last one to reset
        except Exception as e:
            self.log_hw("reset_mix", "result=({})".format(e))
            raise e
        return True

    def get_fw_version(self):
        '''
        {
            "Addon_N301_MLB_FCT_PRM" = 1;
            "MIX_FW_PACKAGE" = 4;
            "PL_N301_MLB_FCT_PRM" = 3;
            "fwup_compatibility_v5" = "1.0.5";
            "mix_datapath_MadagascarA" = "2.0.10";
            "mix_fw_driver_sg_all_in_one" = v1108;
            "mix_kernel" = "1.0.31";
            "mix_launcher" = "0.0.64";
            "mix_lynx_core_driver_MadagascarA" = "2.0.29";
            "mix_lynx_os_MadagascarA" = "7.0.72";
            "mix_petalinux" = "1.0.90";
            "mix_rootfs_MadagascarA" = "2.0.7";
            "mix_rpc_MadagascarA" = "2.0.30";
            "mix_uboot" = "1.0.32";
        }
        '''
        return self.client.base_board.fw_version()
