from mix.lynx.rpc.rpc_client import RPCClientWrapper
import time
import sys


if __name__ == '__main__':


    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)
    client.relay.module_init()
    client.relay_sg.reset("BASE_BOARD")
    client.psu_board.module_init()
    print client.psu_board.power_output(13000)
    time.sleep(2)
    print client.psu_board.set_current_limit(3000)
    print client.psu_board.power_control("on")
    time.sleep(1)
    print client.relay_sg.mux("POWER_SUPPLY_PATH", "PSU_TO_PPVBUS_HMD_INPUT")
    print client.relay_sg.mux("OQC_PPVBUS_HMD_TO_PPVBUS_SYS_PATH", "CONNECT")
    time.sleep(1)

    print client.relay_sg.mux("UART0_AP_PATH", "UART0_AP_CONNECT_XAVIER")
    print client.relay_sg.mux("UART1_CSOC_PATH", "UART1_CSOC_CONNECT_XAVIER")
    print client.relay_sg.mux("UART2_AOP_CAOP_PATH", "UART2_AOP_CAOP_CONNECT_XAVIER")

    write_data = "PRM0_1"
    uart_number = 1
    write_data = [ord(c) for c in write_data] + [0x0D, 0x0A]
    print client.uart.write_hex(uart_number, write_data)
    print "=====READ====="

    uart_number = 0
    read_size = 7
    ret = client.uart.read_hex(uart_number, read_size)

    print len(ret), ret
    for i in ret:
        print chr(i)
    print "=============="



    # print client.relay_sg.mux("UART0_AP_PATH", "UART0_AP_CONNECT_FTDI")
    # print client.relay_sg.mux("UART1_CSOC_PATH", "UART1_CSOC_CONNECT_FTDI")
    # print client.relay_sg.mux("UART2_AOP_CAOP_PATH", "UART2_AOP_CAOP_CONNECT_FTDI")

    

        
        
        
