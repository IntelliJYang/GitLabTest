from ..Function.TI_Common import RootFunction
from ..Utility.utility import Unit
from TI_Define import *


class TI_Freq(RootFunction):
    def __init__(self, driver=None):
        super(TI_Freq, self).__init__(driver)
        self.obj_mix = None
        self.obj_freq = None

    def init(self):
        self.obj_mix = self.get_method("mix")
        self.obj_freq = self.obj_mix.objfreql

    @handle_response
    def measure_freq(self, *args, **kwargs):
        '''
        measure frequency of signal
        Args:       measure_time:   int, unit ms.
        Returns:    dict,   style is {str:(int,str)}
        Raises:     keyError: raises an PLFREQException
        Examples:   freq.measure_frequency(1500)
        '''
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        measure_time = int(args[0])
        ret = ''
        try:
            tmp_dict = self.obj_freq.measure_frequency(measure_time)
            tmp = tmp_dict.get("freq")
            duty = tmp_dict.get("duty")
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(tmp, "HZ", str(unit))
            self.obj_mix.log_hw("measure_freq", "[freq]={} {}".format(ret, unit))
            self.obj_mix.log_hw("measure_freq", "[duty]={}".format(duty))
        except Exception as e:
            ret = '--FAIL--'
            self.obj_mix.log_hw("measure_freq", "[freq]={}".format(e))
        return ret

    @handle_response
    def beast_set_adc(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        set_adc = str(args[0]).lower()
        ret = ''
        try:
            if 'enable' == set_adc:
                result = self.obj_freq.beast_adc_enable()
            elif 'disable' == set_adc:
                result = self.obj_freq.beast_adc_disable()
            else:
                result = self.obj_freq.beast_adc_reset()
            if 'done' == result:
                ret = '--PASS--'
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret

    @handle_response
    def beast_measure_freq(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        duration = int(args[0])
        ret = ''
        try:

            result = self.obj_freq.beast_measure_freq(duration)
            print result
            self.obj_mix.log_hw("beast_measure_freq", "[result]={}".format(result))
            tmp = result[0]
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(tmp, "HZ", str(unit))
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret

    @handle_response
    def vpp_measure(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        duration = int(args[0])
        ret = ''
        try:
            print "#" * 10
            result = self.obj_freq.vpp_measure(duration)
            print result
            tmp = result[0]
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(tmp, "mV", str(unit))
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret


    @handle_response
    def rms_measure(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        duration = int(args[0])
        ret = ''
        try:
            
            result = self.obj_freq.rms_measure(duration)
            print result
            tmp = result[0]
            unit = kwargs.get("unit")
            ret = Unit.convert_unit(tmp, "mV", str(unit))
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret

    @handle_response
    def pwm_out(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        freq = float(args[0])
        temp = args[1].split('_')
        duty = float(temp[0])
        channel = temp[1]
        self.obj_mix.log_hw("pwm_out", "[result]={} {}".format(freq, duty))
        ret = ''
        try:
            if channel == '0':
                ret = self.obj_freq.pwm_out_0(freq, duty, "square")
            elif channel == '1':
                ret = self.obj_freq.pwm_out_1(freq, duty, "square")
            elif channel == '2':
                ret = self.obj_freq.pwm_out_2(freq, duty, "square")
            elif channel == '3':
                ret = self.obj_freq.pwm_out_3(freq, duty, "square")
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret

    @handle_response
    def pwm_close(self, *args, **kwargs):
        if len(args) != 1:
            return MISSING_ENOUGH_PARA
        channel = int(args[0])
        try:
            ret = self.obj_freq.pwm_close(channel)
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret

    @handle_response
    def pwm_set_freq_duty(self, *args, **kwargs):
        if len(args) != 2:
            return MISSING_ENOUGH_PARA
        channel = str(args[0])
        temp = args[1].split('_')
        t_on = float(temp[0])
        t_off = float(temp[1])
        freq = 1000/(t_on + t_off)
        duty = t_on / (t_on + t_off) *100
        self.obj_mix.log_hw("pwm_out", "[result]={} {}".format(freq, duty))
        ret = ''
        try:
            # ret = self.obj_freq.pwm_set_freq_duty(freq, duty, "square", channel)
            if channel == '0':
                ret = self.obj_freq.pwm_out_0(freq, duty, "square")
            elif channel == '1':
                ret = self.obj_freq.pwm_out_1(freq, duty, "square")
            elif channel == '2':
                ret = self.obj_freq.pwm_out_2(freq, duty, "square")
            elif channel == '3':
                ret = self.obj_freq.pwm_out_3(freq, duty, "square")
        except Exception as e:
            ret = '--FAIL--{}'.format(e)
        return ret




        