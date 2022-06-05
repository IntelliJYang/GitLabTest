from mix.lynx.rpc.rpc_client import RPCClientWrapper
import time
import sys


if __name__ == '__main__':


    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)

    ##################
    for i in range(10000):
        client.relay_sg.mux("POWER_RAIL_PATH", "PP1V2_NAND")
        time.sleep(0.2)
        ret = client.w2.read_measure_value(1000, 10)
        print ("1 PP1V2_NAND", ret * (5.99 / 4.99) )

        client.relay_sg.mux("POWER_RAIL_PATH", "PP1V8_LDO15_TO_MBNRT")
        time.sleep(0.2)
        ret = client.w2.read_measure_value(1000, 10)
        print ("2 PP1V8_LDO15_TO_MBNRT", ret * (5.99 / 4.99) )
             
        client.relay_sg.mux("POWER_RAIL_PATH", "PP0V88_NAND")
        time.sleep(0.2)
        ret = client.w2.read_measure_value(1000, 10)
        print ("3 PP0V88_NAND", ret * (5.99 / 4.99) )

        client.relay_sg.mux("POWER_RAIL_PATH", "PP0V72_S2_VDDLOW")
        time.sleep(0.2)
        ret = client.w2.read_measure_value(1000, 10)
        print ("4 PP0V72_S2_VDDLOW", ret * (5.99 / 4.99) )

        time.sleep(0.5)      
        print                                                      
    ##################    

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

        
        
