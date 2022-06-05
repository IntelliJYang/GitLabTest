#!/usr/bin/python
# -*-coding:utf-8 -*-
__author__ = "JinHui Huang"
__copyright__ = "Copyright 2020, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import os
import zmq
import time
import traceback
from threading import Thread
from Configure import driver_config
from Configure import zmqports
from Configure import constant
from Common.publisher import ZmqPublisher
from Fixture.ZmqfixtureTransport import ZmqFixtureTransport
from ThirdPartyLib.libEowyn import LibEowyn, Led
from Common.BBase import Print

"""
ready_uut0 -> blue
idle -> yellow
pass  -> green
fail -> read
init -> init
"""
FIXTURE_STATUS = ['', 'IN', 'OUT', 'DOWN', 'IDLE']


class StreamServer(Thread):
    def __init__(self):
        super(StreamServer, self).__init__()
        self.serving = True
        self.allSlotReady = False
        # create zmq context, every process have a context
        ctx = zmq.Context()
        # create a ROUTER socket for receiving fixture action
        endpoint = "tcp://*:{}".format(zmqports.FIXTURE_CTRL_PORT)
        self.transport = ZmqFixtureTransport.create(ctx, endpoint)
        self.publisher = ZmqPublisher(ctx, "tcp://*:%s" % zmqports.FIXTURE_CTRL_PUB, "FIXTURE")
        self.transport.publisher = self.publisher
        time.sleep(1)
        self._stream_ip = driver_config.FIXTURE_CFG.get('stream_ip')
        os.system('ping -t 5 {}'.format(self._stream_ip))
        if not constant.SIMULATOR_FIXTURE:
            self.fixture = LibEowyn(self._stream_ip)
            self.led = Led(self.fixture.eowyn_obj)
            if not self.fixture.connected():
                self.publisher.publish('eowyn Connect Fail, 夹具连接失败')
                raise IOError("eowyn Connect Fail，夹具连接失败")
            else:
                self.led.start_state_led_blink('cypher')
                self.led.start_uut1_led_blink('cypher')
                self.led.start_uut2_led_blink('cypher')
                self.led.start_uut3_led_blink('cypher')
                self.led.start_uut4_led_blink('cypher')

    def get_fixture_config(self):
        return "ip : " + self._stream_ip + '\n'

    def run(self):
        if constant.SIMULATOR_FIXTURE:
            if not os.path.exists('/vault/simulator_fixture.txt'):
                os.system('touch /vault/simulator_fixture.txt')
        self.transport.heartbeat_at = time.time() + 5
        while self.serving:
            context, message = self.transport.receive_message()
            self.transport.check_heartbeat()
            if constant.SIMULATOR_FIXTURE:
                self.allSlotReady = True
            if not self.allSlotReady:
                iTimes = 0
                iResult = 0
                for i in range(constant.GROUPS):
                    for j in range(constant.SLOTS):
                        with open("/tmp/HeartBeat_Slot{}.txt".format(j + 1), "r") as f:
                            iTimes = iTimes + 1
                            result = f.read()
                            if result == "1":
                                iResult = iResult + 1
                if iTimes != 0 and iResult != 0 and iTimes == iResult:
                    self.led.stop_state_led_blink()
                    self.led.stop_uut1_led_blink()
                    self.led.stop_uut2_led_blink()
                    self.led.stop_uut3_led_blink()
                    self.led.stop_uut4_led_blink()
                    time.sleep(1)
                    self.led.state_led('init')
                    self.led.uut1_led('init')
                    self.led.uut2_led('init')
                    self.led.uut3_led('init')
                    self.led.uut4_led('init')
                    self.allSlotReady = True

            if message:
                ret = ' FAIL'
                result = ""
                try:
                    if not constant.SIMULATOR_FIXTURE:
                        if message == 'IN':
                            state = int(self.fixture.check_dut_sensor())
                            state = -64
                            if state == -64:
                                self.fixture.tray_in()
                                position = int(self.fixture.check_position_sensor())
                                result = FIXTURE_STATUS[position]
                            else:
                                result = 'DUT Not READY'
                        elif message == 'DOWN':
                            self.fixture.tray_down()
                            position = int(self.fixture.check_position_sensor())
                            result = self.led.state_led('green')
                            result = FIXTURE_STATUS[position]
                        elif message == 'UP':
                            self.fixture.tray_up()
                            position = int(self.fixture.check_position_sensor())
                            result = FIXTURE_STATUS[position]
                            print 'UP: ', result
                        elif message == 'OUT':
                            self.fixture.tray_out()
                            position = int(self.fixture.check_position_sensor())
                            result = FIXTURE_STATUS[position]
                        elif message == "FIXTURE_STATUS":
                            position = int(self.fixture.check_position_sensor())
                            result = FIXTURE_STATUS[position]
                        elif message == "DUT_STATUS":
                            result = self.fixture.check_dut_sensor()
                        elif "_" in message:
                            state, uutx = message.split("_")
                            if state == "blue":
                                result = self.led.state_led('blue')
                            elif state == "red" or state == "green":
                                result = self.led.state_led('init')

                            if uutx == "uut0":
                                result = self.led.uut1_led(state.lower())
                            elif uutx == "uut1":
                                result = self.led.uut2_led(state.lower())
                            elif uutx == "uut2":
                                result = self.led.uut3_led(state.lower())
                            elif uutx == "uut3":
                                result = self.led.uut4_led(state.lower())
                    else:
                        result = message
                    if result == message:
                        ret = ' SUCCESS'
                    else:
                        if message == 'UP':
                            if result == 'IN':
                                ret = ' SUCCESS'
                except Exception as e:
                    print e, traceback.format_exc()
                finally:
                    if message == "DUT_STATUS" or "_" in message:
                        ret = ' ' + str(result)
                    self.log('CONTROL FIXTURE: {}'.format(str(message + ret)))
                    Print.print_with_time(message)
                    self.transport.send_reply(context, str(message + ret))
            else:
                if not constant.SIMULATOR_FIXTURE:
                    reply = 'INTERVAL CHECK STATUS: ' + FIXTURE_STATUS[self.fixture.check_position_sensor()]
                else:
                    with open('/vault/simulator_fixture.txt', 'r+') as f:
                        reply = f.readline()
                        if reply:
                            reply = 'INTERVAL CHECK STATUS: ' + reply
                if reply:
                    self.log(reply)
        self.transport.shutdown()

    def stop_serving(self):
        self.publisher.stop()
        self.serving = False

    def log(self, msg):
        # Print.print_with_time(msg)
        if self.publisher:
            self.publisher.publish(msg)


if __name__ == '__main__':
    fs = StreamServer()
    fs.start()
