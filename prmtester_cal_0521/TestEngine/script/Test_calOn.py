from mix.lynx.rpc.rpc_client import RPCClientWrapper
import time
import sys




if __name__ == '__main__':


    endpoint = {'requester': 'tcp://169.254.1.33:7801', 'receiver': 'tcp://169.254.1.33:17801'}
    client = RPCClientWrapper(endpoint)

    client.relay.module_init()
    client.relay_sg.reset("BASE_BOARD")
    time.sleep(1)
    client.psu_board.module_init()
    client.psu_board.power_output(13000)
    client.psu_board.set_current_limit(2000)
    print client.psu_board.power_control("on")
    print client.relay_sg.mux("POWER_SUPPLY_PATH", "PSU_TO_PPVBUS_HMD_INPUT")
    # client.relay.set_io_switch([[145, 1]]) # OQC_PPVBUS_HMD_TO_PPVBUS_SYS_PATH,CONNECT
    client.adgarray.set_io_switch([[13, 3, 1]]) #DUT_Active_EN
    # print client.otp_vdd_pin.set_level(1)
    # time.sleep(1)
    # print client.otp_vdd_pin.set_level(0)
    
    client.relay.set_io_switch([[165, 1]])
    client.calmux.relay_init()
    client.calmux.module_init()
    # client.calmux.set_io_switch([[191, 1]])
    # client.calmux.set_io_switch([[191, 1]])[[[178,1],[182,1],[187,1]]
    
    # client.calmux.set_io_switch([[182,1]])
    # client.calmux.set_io_switch([[178,1],[182,1],[181,1],[187,1]])
    # client.calmux.set_io_switch([[180,1],[178,1],[187,1]])
    
    # client.calmux.set_io_switch([[178,1],[182,1],[187,1]])
    # time.sleep(100)
    
    # ##################
    client.relay_sg.mux("POWER_RAIL_PATH", "PP0V8_S1_SOC_FIXED")
    # client.relay_sg.mux("POWER_RAIL_PATH", "RIGEL_CURRENT_OPA_OUT_TO_BEAST_AND_DMM")
    ret = client.w2.read_measure_value(1000, 10)
    print ret * (5.99 / 4.99) 
    ##################    
    # client.psu_board.power_output(0)

    # client.relay.set_io_switch([[84, 1], [83, 0]])
    # client.relay.set_io_switch([[[138,1],[143,0]])

    # print client.relay.set_io_switch([[21, 1], [20, 1], [19, 0], [41, 1], [43, 1], [42, 0], [44, 0], [130, 1], [131, 0], [132, 0], [129, 1], [128, 0]])
    # print client.relay.set_io_switch([[21, 1], [20, 1], [19, 0], [41, 0], [43, 0], [42, 1], [44, 1], [130, 1], [131, 0], [132, 0], [129, 1], [128, 1]])
    # print client.relay.set_io_switch([[115, 0], [157, 0], [158, 1], [159, 1]])
    # print client.relay.set_io_switch([[153, 1], [154, 1], [155, 1]])
    # print client.adgarray.set_io_switch([[0,4,1]])
    #######################
    # client.trinary.trinary_init("S0")
    # time.sleep(2)
    # client.oqc_trinary.trinary_init("S4")
    # time.sleep(2)

    # print client.relay.set_io_switch([[84, 1], [83, 0]])
    # print client.io_exp9.get_pin(10)
    # print client.relay.set_io_switch([[138, 1], [143, 0]])
    # print client.io_exp9.get_pin(10)
    # time.sleep(2)

    #
    #
    #
    # # print client.trinary.bringup_swn_bus()
    # # print client.transport.enable_pcm_bridge()
    # print client.trinary.one_key_all(timeout_ms=4000)
    ################

    # print client.gpio_pwm_0.pwm_open(20000, 50, out_time = 1000, timeout_ms = 1000000)

        
        
