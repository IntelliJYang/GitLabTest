#!/usr/bin/python
import ctypes
import os, time
import threading

current_folder = os.path.abspath(os.path.dirname(__file__))
libeowynpath = current_folder + '/libeowyn.dylib'
libPy = ctypes.cdll.LoadLibrary(libeowynpath)

# void *createEowynDev(const char * strIp)
libPy.createEowynDev.restype = ctypes.c_void_p
libPy.createEowynDev.argtypes = [ctypes.c_char_p]

# void void destroyEowynDev(void *obj)
libPy.destroyEowynDev.argtypes = [ctypes.c_void_p]

# bool connected(void *obj)
libPy.connected.argtypes = [ctypes.c_void_p]
libPy.connected.restype = ctypes.c_bool

# int checkPositionSensor(void *obj)
libPy.checkPositionSensor.argtypes = [ctypes.c_void_p]
libPy.checkPositionSensor.restype = ctypes.c_int

# int checkDUTSensor(void *obj)
libPy.checkDUTSensor.argtypes = [ctypes.c_void_p]
libPy.checkDUTSensor.restype = ctypes.c_int

# void trayUp(void *obj)
libPy.trayUp.argtypes = [ctypes.c_void_p]

# void trayDown(void *obj)
libPy.trayDown.argtypes = [ctypes.c_void_p]

# void trayIn(void *obj)
libPy.trayIn.argtypes = [ctypes.c_void_p]

# void trayOut(void *obj)
libPy.trayOut.argtypes = [ctypes.c_void_p]

# void fixtureLock(void *obj,int nFlag)
libPy.fixtureLock.argtypes = [ctypes.c_void_p, ctypes.c_int]

# void uut1Led(void *obj,const char * strMode)
libPy.uut1Led.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

# void uut2Led(void *obj,const char * strMode)
libPy.uut2Led.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

# void uut3Led(void *obj,const char * strMode)
libPy.uut3Led.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

# void uut4Led(void *obj,const char * strMode)
libPy.uut4Led.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

# void stateLed(void *obj,const char * strMode)
libPy.stateLed.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

# const char* getDuts(void *obj)
libPy.getDuts.argtypes = [ctypes.c_void_p]
libPy.getDuts.argtypes = [ctypes.c_void_p]


class LibEowyn:

    def __init__(self, fixtureip):
        self.eowyn_obj = libPy.createEowynDev(fixtureip)

    def del_obj(self):
        if self.eowyn_obj and self.connected():
            ret = libPy.destroyEowynDev(self.eowyn_obj)
        else:
            ret = -1
        return ret

    def connected(self):
        if self.eowyn_obj:
            ret = libPy.connected(self.eowyn_obj)
        else:
            ret = False
        return ret

    def check_position_sensor(self):
        if self.eowyn_obj:
            return libPy.checkPositionSensor(self.eowyn_obj)
        else:
            return -1

    def check_dut_sensor(self):
        return libPy.checkDUTSensor(self.eowyn_obj)

    def tray_up(self):
        return libPy.trayUp(self.eowyn_obj)

    def tray_down(self):
        return libPy.trayDown(self.eowyn_obj)

    def tray_in(self):
        return libPy.trayIn(self.eowyn_obj)

    def tray_out(self):
        return libPy.trayOut(self.eowyn_obj)

    def fixture_lock(self, flag):
        return libPy.fixtureLock(self.eowyn_obj, flag)

    def get_duts(self):
        return libPy.getDuts(self.eowyn_obj)


class Led(object):
    def __init__(self, dev):
        super(Led, self).__init__()
        self.dev = dev
        self.led1_thread = False
        self.led2_thread = False
        self.led3_thread = False
        self.led4_thread = False
        self.ledS_thread = False
        self.lock = threading.RLock()

    def uut1_led(self, strmode):
        self.stop_uut1_led_blink()
        return self.__uut1_led(strmode)

    def start_uut1_led_blink(self, strmode, freq=2):
        self.led1_thread = True
        thread1 = threading.Thread(target=self.blink1, args=(strmode, freq,))
        thread1.start()

    def stop_uut1_led_blink(self):
        self.led1_thread = False

    def __uut1_led(self, strmode):
        self.lock.acquire()
        ret = libPy.uut1Led(self.dev, strmode)
        self.lock.release()
        return ret

    def uut2_led(self, strmode):
        self.stop_uut2_led_blink()
        return self.__uut2_led(strmode)

    def start_uut2_led_blink(self, strmode, freq=2):
        self.led2_thread = True
        thread2 = threading.Thread(target=self.blink2, args=(strmode, freq,))
        thread2.start()

    def stop_uut2_led_blink(self):
        self.led2_thread = False

    def __uut2_led(self, strmode):
        self.lock.acquire()
        ret = libPy.uut2Led(self.dev, strmode)
        self.lock.release()
        return ret

    def uut3_led(self, strmode):
        self.stop_uut3_led_blink()
        return self.__uut3_led(strmode)

    def start_uut3_led_blink(self, strmode, freq=2):
        self.led3_thread = True
        thread3 = threading.Thread(target=self.blink3, args=(strmode, freq,))
        thread3.start()

    def stop_uut3_led_blink(self):
        self.led3_thread = False

    def __uut3_led(self, strmode):
        self.lock.acquire()
        ret = libPy.uut3Led(self.dev, strmode)
        self.lock.release()
        return ret

    def uut4_led(self, strmode):
        self.stop_uut4_led_blink()
        return self.__uut4_led(strmode)

    def start_uut4_led_blink(self, strmode, freq=2):
        self.led4_thread = True
        thread4 = threading.Thread(target=self.blink4, args=(strmode, freq,))
        thread4.start()

    def stop_uut4_led_blink(self):
        self.led4_thread = False

    def __uut4_led(self, strmode):
        self.lock.acquire()
        ret = libPy.uut4Led(self.dev, strmode)
        self.lock.release()
        return ret

    def state_led(self, strmode):
        self.stop_state_led_blink()
        return self.__state_led(strmode)

    def start_state_led_blink(self, strmode, freq=2):
        self.ledS_thread = True
        threadS = threading.Thread(target=self.blinkS, args=(strmode, freq,))
        threadS.start()

    def stop_state_led_blink(self):
        self.ledS_thread = False

    def __state_led(self, strmode):
        self.lock.acquire()
        ret = libPy.stateLed(self.dev, strmode)
        self.lock.release()
        return ret

    def blink1(self, strmode, freq):
        sleep_time = 1.0/(freq*2)
        arrmode = [strmode, 'init']
        if strmode == 'cypher':
            sleep_time = sleep_time*2
            arrmode = ['red', 'green', 'blue']  # , 'yellow']
        while(self.led1_thread):
            for mode in arrmode:
                self.__uut1_led(mode)
                time.sleep(sleep_time)

    def blink2(self, strmode, freq):
        sleep_time = 1.0/(freq*2)
        arrmode = [strmode, 'init']
        if strmode == 'cypher':
            sleep_time = sleep_time*2
            arrmode = ['red', 'green', 'blue']  # , 'yellow']
        while(self.led2_thread):
            for mode in arrmode:
                self.__uut2_led(mode)
                time.sleep(sleep_time)

    def blink3(self, strmode, freq):
        sleep_time = 1.0/(freq*2)
        arrmode = [strmode, 'init']
        if strmode == 'cypher':
            sleep_time = sleep_time*2
            arrmode = ['red', 'green', 'blue']  # , 'yellow']
        while(self.led3_thread):
            for mode in arrmode:
                self.__uut3_led(mode)
                time.sleep(sleep_time)

    def blink4(self, strmode, freq):
        sleep_time = 1.0/(freq*2)
        arrmode = [strmode, 'init']
        if strmode == 'cypher':
            sleep_time = sleep_time*2
            arrmode = ['red', 'green', 'blue']  # , 'yellow']
        while(self.led4_thread):
            for mode in arrmode:
                self.__uut4_led(mode)
                time.sleep(sleep_time)

    def blinkS(self, strmode, freq):
        sleep_time = 1.0/(freq*2)
        arrmode = [strmode, 'init']
        if strmode == 'cypher':
            sleep_time = sleep_time*2
            arrmode = ['red', 'green', 'blue']
        while(self.ledS_thread):
            for mode in arrmode:
                self.__state_led(mode)
                time.sleep(sleep_time)


if __name__ == '__main__':
    eowyn = LibEowyn('169.254.1.77')
    print("=====================")
    # print(eowyn.connected())
    print(eowyn.check_dut_sensor())

    # print("=====================")
    # print(eowyn.fixture_lock(False))
    # print("=====================")
    # print(eowyn.check_position_sensor())
    # print("=====================")
    # print(eowyn.tray_in())
    # print(eowyn.check_position_sensor())
    # print("=====================")
    # print(eowyn.tray_down())
    # print(eowyn.check_position_sensor())
    # print("=====================")
    # print(eowyn.tray_up())
    # print(eowyn.check_position_sensor())
    # print("=====================")
    # print(eowyn.tray_out())
    # print(eowyn.check_position_sensor())
    # print("=====================")

    led = Led(eowyn.eowyn_obj)
    # arrModes = ['yellow', 'blue', 'green', 'red', 'cypher']
    # # arrModes = ['cypher']X
    # for mode in arrModes:
    #     print("=====================")
    #     led = Led(eowyn.eowyn_obj)
    #     if mode != 'yellow':
    #         led.start_state_led_blink(mode)
    #     led.start_uut1_led_blink(mode)
    #     led.start_uut2_led_blink(mode)
    #     led.start_uut3_led_blink(mode)
    #     led.start_uut4_led_blink(mode)
    #     time.sleep(10)
    #     led.stop_state_led_blink()
    #     led.stop_uut1_led_blink()
    #     led.stop_uut2_led_blink()
    #     led.stop_uut3_led_blink()
    #     led.stop_uut4_led_blink()
    #     time.sleep(1)

    led.uut1_led("init")
    led.uut1_led("red")
    time.sleep(100)

    arrModes = ['yellow', 'blue', 'green', 'red', 'init']
    # arrModes = ['blue']
    # for mode in arrModes:
    #     print("=====================")
    #     if mode != 'yellow':
    #         led.state_led(mode)
    #     led.uut1_led(mode)
    #     led.uut2_led(mode)
    #     led.uut3_led(mode)
    #     led.uut4_led(mode)
    #     time.sleep(1)
