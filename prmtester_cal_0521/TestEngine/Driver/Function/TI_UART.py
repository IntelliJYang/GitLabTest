from ..Function.TI_Common import RootFunction
from TI_Define import *


class TI_UART(RootFunction):
    def __init__(self, driver=None):
        super(TI_UART, self).__init__(driver)
        self.obj_mix = None
        self.obj_uart = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_uart = self.obj_mix.objsguart

    @handle_response
    def uart_write(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        uart_number = int(args[0])
        write_data = args[1]
        self.obj_uart.uart_write(uart_number, write_data)
        return "--PASS--"

    @handle_response
    def uart_read(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        uart_number = int(args[0])
        read_len = int(args[1])
        ret = self.obj_uart.uart_read(uart_number, read_len)
        if ret and len(ret) > 0:
            return ret
        else:
            return "--FAIL--No uart Data"

    @handle_response
    def uart_clear(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        uart_number = int(args[0])
        read_len = int(args[1])
        ret = self.obj_uart.uart_read(uart_number, read_len)
        return "--PASS--"
