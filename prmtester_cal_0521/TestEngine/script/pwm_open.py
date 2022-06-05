from mix.lynx.rpc.rpc_client import RPCClientWrapper

import threading
from threading import Thread


if __name__ == '__main__':


    endpoint = {'requester': 'tcp://169.254.1.32:7801', 'receiver': 'tcp://169.254.1.32:17801'}
    client = RPCClientWrapper(endpoint)
    print "pwm start"
    # t = Thread(target=client.gpio_pwm_0.pwm_open, args=(20000, 50, 20, 100000), name='pwm_open')
    # t.setDaemon(True)
    # t.start()
    # 
    print client.gpio_pwm_0.pwm_open(20000, 50, out_time = 150, timeout_ms = 100000)
    # print client.gpio_pwm_0.pwm_thread()
    print "pwm end"

        
        
        
