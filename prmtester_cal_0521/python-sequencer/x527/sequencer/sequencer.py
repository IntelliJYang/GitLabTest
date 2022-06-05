#!/usr/bin/python
import argparse
import importlib
import os
import sys
import time
import traceback
from datetime import datetime
from threading import Thread

import zmq

from pluginserver import PluginServer
from pypudding import validate_serial_number
from sequence import TestSequence, TestGroup
from x527 import zmqports
from x527.loggers import ZmqPublisher, levels, events, reporter
from x527.rpc_client import RPCClientWrapper
from x527.rpc_server import RPCServerWrapper
from x527.tinyrpc.dispatch import public
from x527.tinyrpc.protocols.jsonrpc import *

ALLOWED_TRAVELER_KEYS = {'attributes'}  # todo: put these into config
SKIP_ITEM = 2
ENGINE_DELAY_MS = 5000
AMIOK_DELAY_S = 5

class Sequencer(object):

    def __init__(self, site, publisher, fail_limit):
        super(Sequencer, self).__init__()
        self.site = site
        self.sequence = None
        self.publisher = publisher
        self.test_engine = RPCClientWrapper(
            'tcp://localhost:' + str(zmqports.TEST_ENGINE_PORT+site),
            self.publisher
        )
        self.pc = 0
        self.stop_on_fail = False
        self.running = False
        self.run_thread = None
        self.reporter = reporter.Reporter(self.publisher)
        self.plugin = PluginServer()
        self.error_msg = ''
        self.total_pass = True
        self.fail_count = 0
        self.fail_limit = fail_limit
        self.engine_delay = ENGINE_DELAY_MS
        self.customizer = None
        self.load_config()

    def load_config(self, config_file='config.json'):
        path = os.path.join(os.path.split(__file__)[0], os.path.pardir, config_file)
        cfg = os.path.abspath(path)
        if os.path.exists(cfg):
            with open(cfg, 'rU') as f:
                config = json.load(f)
            params = config.get('sequencer')
            self.engine_delay = params.get('engine_timeout', self.engine_delay)
            self.end_test_timeout = params.get('end_test_timeout', self.engine_delay)
            lib_path = params.get('customizer')
            if lib_path:
                try:
                    self.customizer = importlib.import_module(lib_path)
                    print 'Imported customizer module from config.json'
                    self.publisher.publish('Imported customizer module from config.json')
                    return True
                except ImportError as e:
                    print 'Failed to import customizer module defined in config: '+e.message
                    self.publisher.publish('Failed to import customizer module defined in config: '+e.message)
        else:
            print 'Failed to locate config.json'
        if os.path.exists('customizer.py'):
            try:
                self.customizer = importlib.import_module('customizer')
                print 'Imported customizer module from default location'
                self.publisher.publish('Imported customizer module from default location')
                return True
            except ImportError as e:
                print 'Failed to import local customizer module: ' + e.message
                self.publisher.publish('Failed to import local customizer module: ' + e.message)
        if self.customizer is None:
            print 'No customizer module is found to import'
            self.publisher.publish('No customizer module is found to import')
            return False

    @public('connect')
    def connect(self):
        """connect sequencer to test engine"""
        self.publisher.publish('connecting to test engine...', 'initializing')
        response = self.test_engine.remote_server()._my_rpc_server_is_ready()
        if response and response.result == '--PASS--':
            self.publisher.publish('connected')
            return True
        else:
            self.publisher.publish('failed to connect to test engine')
            return False

    @public('skip')
    def skip_to_next(self):
        """return value indicates if we have wrapped around"""
        if self.sequence:
            self._inc_pc()
            item = self.sequence[self.pc]
            return [self.pc+1, str(item)]

    def _inc_pc(self):
        """return value indicates if we have wrapped around"""
        if self.sequence:
            self.pc += 1
            if self.pc == len(self.sequence):
                self.pc = 0
                return True
        return False

    @public('load')
    def load_sequence(self, sequence_db):
        self.sequence = TestSequence(sequence_db)
        self.pc = 0
        self.plugin.sequence = self.sequence
        self.reporter.report(events.SEQUENCE_LOADED, name=os.path.basename(sequence_db).split('.')[0], case_list=self.s_list('all'))
        return sequence_db + ' has been loaded'

    def jump_to_line(self, line):
        if line > len(self.sequence) or line < 1:
            raise JSONRPCInvalidParamsError('the requested line ' + str(line) + ' is beyond the end of the sequence')
        self.pc = line - 1
        item = self.sequence[self.pc]
        return [self.pc+1, str(item)]

    def jump_to_name(self, name):
        try:
            item = self.sequence[name]
            if isinstance(item, TestGroup):
                item = item[0]
                self.pc = self.sequence.get_index(item.tid, group=name)
            else:
                self.pc = self.sequence.get_index(item.tid)
            return [self.pc+1, str(item)]
        except KeyError as e:
            raise JSONRPCInvalidParamsError(e.message)

    @public('jump')
    def s_jump(self, line):
        if self.sequence is None:
            raise JSONRPCInvalidRequestError('No sequence has been loaded. Load a valid sequence first')
        try:
            line = int(line)
            return self.jump_to_line(line)
        except ValueError:
            # if it's not an integer, assume it's a TID or group name
            return self.jump_to_name(line)

    @public('list')
    def s_list(self, lines):
        if self.sequence is None:
            raise JSONRPCInvalidRequestError('Can not list. No sequence has been loaded. Load a valid sequence first')
        try:
            start = 0
            if lines.strip().lower() == 'all':
                stop = len(self.sequence)
            else:
                lines = int(lines)
                start = max(self.pc - lines/3, 0)
                stop = min(len(self.sequence), start + lines)
            reply = [[self.pc, start, stop]]
            # line is 1 based and pc is 0 based
            reply.extend([[i+1, str(self.sequence[i])] for i in range(start, stop)])
            return reply
        except ValueError as e:
            raise JSONRPCInvalidParamsError('in command list, ' + lines + ' is not an integer')

    # return True if the run timeout, return False if normal exit. If timeout is 0 then no timeout
    @public('wait')
    def wait(self, timeout):  # timeout is in seconds
        timeout = int(timeout)
        t1 = datetime.now()
        while self.running:
            if timeout != 0:
                t2 = datetime.now()
                elapsed = (t2-t1).total_seconds()
                if elapsed > timeout:
                    return True
            time.sleep(0.1)
        return False

    def run_test(self, test):

        def _run_group():
            try:
                if test.row['PARAM2'].lower() in ["yes", "true", "enable"]:
                    group_enable = True
                elif test.row["PARAM2"].lower() in ["no", "false", "disable"]:
                    group_enable = False
                else:
                    raise Exception
            except:
                return PluginServer.error_respond("invalid PARAM2, should be YES/NO/ or TRUE/FALSE or ENABLE/DISABLE")

            self.sequence.group_run_dict[test.row['PARAM1']] = group_enable
            if group_enable:
                self.sequence.group_run_mode = True
                return PluginServer.respond("ENABLE")
            else:
                return PluginServer.respond("DISABLE")

        for group in self.sequence.groups:
            if group.name == test.group:
                if group.start_time is None:
                    group.start_time = datetime.now()
                break


        if not test.should_run(self.sequence.variables, self.sequence.group_run_mode, self.sequence.group_run_dict):
            # self.reporter.report(events.ITEM_FINISH, group=test.group, tid=test.tid,
            #                      result=SKIP_ITEM, value='SKIP', to_pdca=False)
            for group in self.sequence.groups:
                if group.name == test.group:
                    group.stop_time = datetime.now()
                    break
            return None
        self.publisher.publish('running test ' + str(test))
        self.reporter.report(events.ITEM_START, to_pdca=test.report_to_pudding, **test.row)
        for arg_name in test.kwargs.keys():
            test.kwargs[arg_name] = self.sequence.variables[arg_name]

        if self.sequence.is_group_run_function(test.function):
            response = _run_group()
        elif test.call_engine:
            test_dict = test._to_dict()
            response = getattr(self.test_engine.remote_server(), test_dict['function'])(*test_dict['params'], unit=test.unit, timeout=test.timeout)
        else:
            response = self.plugin.call(test)
        if response is None:
            raise JSONRPCServerError('Timed out waiting for response from test engine in test: ' + str(test))
        if hasattr(response, 'error'):
            raise JSONRPCServerError('Test Engine error: ' + str(response._jsonrpc_error_code) + ':' + response.error)
        if not hasattr(response, 'result'):
            raise JSONRPCServerError('Received invalid response : ' + str(response))

        # handle special tags
        if isinstance(response.result, basestring):
            ret_lst = [c for c in response.result if ord(c) < 128]
            ret_conv = ''.join(ret_lst)
        else:
            ret_conv = str(response.result)
        r_str = ret_conv.upper().strip()

        if r_str == '--PASS--':
            test.report_to_pudding = True
            pass_fail = True
            val = ret_conv
        elif r_str.startswith('--FAIL--'):
            test.report_to_pudding = True
            pass_fail = False
            res = ret_conv.strip()
            val = res[8:] if len(res) > 8 else res
        else:
            pass_fail = True
            val = response.result
        if test.returned_val is not None and pass_fail is True:
            self.sequence.variables[test.returned_val] = response.result
        if test.judge_pass and pass_fail:
            pass_fail = test.judge_pass(response.result)

        if test.p_attribute is not None and pass_fail:
            self.reporter.report(events.ATTRIBUTE_FOUND, name=test.p_attribute, value=val)
            self.sequence.variables[test.p_attribute] = val
            # if 'sn' in test.p_attribute.lower() or 'serialnumber' in test.p_attribute.lower(): #-- in will casue more delay when any attribute have sn word, like gyro_sn Aaron Tong 20190415
            #                                                                                     # and no need more UOP check and delay, each TID cover it
            #     time.sleep(AMIOK_DELAY_S)  # trick to wait for implicit amIOK call returns

        self.reporter.report(events.ITEM_FINISH, group=test.group, tid=test.tid, result=pass_fail, value=val,
                             to_pdca=test.report_to_pudding)
        for group in self.sequence.groups:
            if group.name == test.group:
                group.stop_time = datetime.now()
                break
        return pass_fail

    def finish_sequence(self, result, error_msg='',logs =''):
        if result >= 1:
            ret = 1
        else:
            ret = 0
        engine_logs = logs
        try:
            response = self.test_engine.remote_server().end_test(ret, timeout=self.end_test_timeout)
            if hasattr(response, 'error'):
                # error_msg = error_msg + '; error calling end_test: ' + response.error
                raise JSONRPCServerError('Test Engine error: ' + str(response._jsonrpc_error_code) + ':' + response.error)
            elif 'logs' in response.result or 'attributes' in response.result: 
                e_traveler = json.loads(response.result)
                if e_traveler.get('logs', '') != '':
                    engine_logs = e_traveler.get('logs', '')
                if e_traveler.get('attributes',{}) != {}:
                    for attr, attr_val in e_traveler.get('attributes').iteritems():
                        self.reporter.report(events.ATTRIBUTE_FOUND, name=attr, value=attr_val)
            elif response.result and engine_logs=='':
                engine_logs = response.result
        except Exception as e:
            error = e.message
            self.publisher.publish(error)
            error_msg = error_msg + '; error calling end_test: ' + error
            if not isinstance(e, RPCError):
                error_msg = error_msg + os.linesep + traceback.format_exc()
        if result < 0:
            self.reporter.report(events.SEQUENCE_END, result=-1, error=error_msg, logs=engine_logs)
        else:
            self.reporter.report(events.SEQUENCE_END, result=result, error=error_msg, logs=engine_logs)
        self.running = False
        self.pc = 0

    def run_sequence(self, e_traveler):
        interrupted = False
        wait_for_diags = False
        self.total_pass = True
        self.sequence.variables['result'] = True
        current_test = None

        self.reporter.report(events.SEQUENCE_START, name=self.sequence.name, version=self.sequence.version)
        if e_traveler:
            for attr, attr_val in e_traveler['attributes'].iteritems():
                self.reporter.report(events.ATTRIBUTE_FOUND, name=attr, value=attr_val)
                if attr == 'MLBSN':
                    if validate_serial_number(attr_val):
                        self.sequence.variables['scanned_sn'] = attr_val
                    else:
                        continue
                # if 'sn' in attr.lower() or 'serialnumber' in attr.lower(): -- Aaron Tong, no need AMOK check covered by each TID 20190415
                #     time.sleep(AMIOK_DELAY_S)
        time.sleep(0.2) # reduce the delay time to 0.2s

        engine_logs = ''
        try:
            response = self.test_engine.remote_server().start_test(timeout=self.engine_delay)
            if hasattr(response, 'error'):
                raise JSONRPCServerError('Test Engine error: ' + str(response._jsonrpc_error_code) + ':' + response.error)
            elif response.result:
                engine_logs = response.result
            if not interrupted:
                for test in self.sequence:
                    if self.fail_count >= self.fail_limit:
                        break
                    current_test = test
                    if not self.running:
                        self.finish_sequence(result=-1, error_msg='sequence aborted',logs=engine_logs)
                        interrupted = True
                        break
                    if wait_for_diags and self.stop_on_fail:
                        # the device has failed, we continue to run until the next diags function
                        if test.function == 'diags':
                            break
                    result = self.run_test(test)
                    self._inc_pc()
                    if result is None:  # that means this test didn't run
                        continue
                    if not result:
                        self.total_pass = False
                        self.sequence.variables['result'] = False
                        self.fail_count += test.fail_count if test.fail_count else 0
                        print 'fail_count:', self.fail_count, ' fail_limit:', self.fail_limit

                        if self.fail_count >= self.fail_limit:
                            break
                        if test.function == 'detect':
                            wait_for_diags = True
                        else:
                            if self.stop_on_fail:
                                break  # stop on fail unless the function is detect
                    current_test = None
        except Exception as e:
            error_msg = e.message
            print (traceback.format_exc())
            if current_test:
                error_msg = 'error running test ' + current_test.tid + '; error message is "' + e.message + '"'
                self.reporter.report(events.ITEM_FINISH, result=-1, value='', error=error_msg,
                                     group=current_test.group, tid=current_test.tid, to_pdca=True)
                for group in self.sequence.groups:
                    if group.name == current_test.group:
                        group.stop_time = datetime.now()
                    break
            if not isinstance(e, RPCError):
                error_msg = error_msg + os.linesep + traceback.format_exc()
            self.publisher.publish(error_msg)
            self.finish_sequence(result=False, error_msg=error_msg,logs=engine_logs)
            interrupted = True
        if not interrupted:
            self.finish_sequence(result=int(self.total_pass), error_msg=self.error_msg,logs=engine_logs)
        self.report_listener.receiving = False
        print 'sequencer done', self.site

    # listen for UOP, the call back function for report listener
    def received(self, report):
        if report.event == events.REPORT_ERROR:  # handle ERROR events only
            if report.data['error_code'] == reporter.AMIOK_ERROR:  # handle UOP
                if report.data['site'] == self.site:
                    self.reporter.report(events.UOP_DETECT, result=-1, error=report.data['error_msg'])
                    self.total_pass = False
                    self.sequence.variables['result'] = False
                    self.fail_count = self.fail_limit
            elif report.data['error_code'] == reporter.IP_START_ERROR:
                 if report.data['site'] == self.site:
                    self.reporter.report(events.IP_START_FAIL_DETECT, result=-1, error=report.data['error_msg'])
                    self.total_pass = False
                    self.sequence.variables['result'] = False
                    self.fail_count = self.fail_limit               

    @public('run')
    def s_run(self, e_traveler=None):
        if self.running:
            raise JSONRPCInvalidRequestError('A sequence is already running at site ' + str(self.site))
        if self.sequence is None:
            raise JSONRPCInvalidRequestError('trying to run without any sequence loaded')
        self.running = True
        self.fail_count = 0
        self.error_msg = ''
        self.sequence.clear_variables()
        ret = False
        if hasattr(self.customizer, 'init_variables'):
            ret = self.customizer.init_variables(self)
        if not ret:
            self.publisher.publish('WARNING: Init sequence variables by plugin failed')
        if e_traveler:
            if not isinstance(e_traveler, dict):
                raise JSONRPCInvalidParamsError('etraveler must be a dictionary')
            for key in e_traveler.keys():
                if key not in ALLOWED_TRAVELER_KEYS:
                    raise JSONRPCInvalidParamsError('invalid key "' + key + '" in e_traveler')
                if not isinstance(e_traveler['attributes'], dict):
                    raise JSONRPCInvalidParamsError('in e_traveler, attributes is not a dictionary')
        self.report_listener = reporter.ReportListener(zmqports.LOGGER_PUB)
        self.report_listener.listeners.append(self)
        self.report_listener.start()
        time.sleep(0.2) # reduce the delay time to 0.2s
        self.run_thread = Thread(target=self.run_sequence, args=(e_traveler,))
        self.run_thread.start()
        return True

    @public('show')
    def show(self, var_name):
        if self.sequence is None:
            raise JSONRPCInvalidRequestError('Cannot show variable value. No sequence has been loaded. '
                                             'Load a valid sequence first')
        if var_name not in self.sequence.variables:
            raise JSONRPCInvalidParamsError('variable ' + var_name + ' does not exist')
        else:
            reply = str(self.sequence.variables[var_name])
        return reply

    @public('s_next')
    def s_next(self):
        if self.sequence is None:
            raise JSONRPCInvalidRequestError('No sequence has been loaded. Load a valid sequence first')
        return self.pc+1

    @public('step')
    def step(self):
        if self.sequence is None:
            raise JSONRPCInvalidRequestError('No sequence has been loaded. Load a valid sequence first')
        if self.running:
            raise JSONRPCInvalidRequestError('Can not single step while a test is running')
        if self.pc == len(self.sequence):
            self.pc = 0
            return None
        pass_fail = None

        while pass_fail is None:
            current_item = self.sequence[self.pc]
            self.pc += 1
            pass_fail = self.run_test(current_item)
        return [self.pc, str(current_item)]

    @public('status')
    def status(self):
        if self.running:
            return "RUNNING"
        if self.sequence:
            return 'READY'
        else:
            return 'NONLOADED'

    @public('abort')
    def abort(self):
        if self.running:
            self.running = False
            self.error_msg = 'Test is aborted by command'
            self.publisher.publish('sequence aborted', level=levels.CRITICAL)
            self.run_thread.join()
        return 'sequence is not running'  # do nothing if no tests sequence is being run


class SequencerServer(Thread):
    def __init__(self, site, fail_limit, publisher=None, stop_on_fail=False):
        super(SequencerServer, self).__init__()
        self.site = site

        if publisher:
            self.publisher = publisher
        else:
            ctx = zmq.Context()
            self.publisher = ZmqPublisher(
                ctx,
                "tcp://*:" + str(zmqports.SEQUENCER_PUB + site),
                "Sequencer_" + str(site)
            )
        self.sequencer = Sequencer(site, self.publisher, fail_limit)
        self.sequencer.stop_on_fail = stop_on_fail
        time.sleep(1)   # give the publisher sometime

        self.wrapper = RPCServerWrapper("tcp://*:" + str(zmqports.SEQUENCER_PORT + site), self.publisher)
        self.wrapper.dispatcher.register_instance(self.sequencer)

        self.rpc_server = self.wrapper.rpc_server

    def run(self):
        self.publisher.publish('Sequencer Starting...')
        print 'sequencer starting'
        try:
            # self.sequencer.connect()
            self.rpc_server.serve_forever()
            self.publisher.publish('Sequencer Stopped...')
            print 'sequencer stopped'
        except Exception as e:
            print 'error starting the sequencer: ' + e.message

def start_sequencer(site, fail_limit, stop_on_fail):
    ss = SequencerServer(site, fail_limit, stop_on_fail=stop_on_fail)
    ss.start()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--site', help='the site of the sequencer to connect to', type=int, default=0)
    parser.add_argument('-c', '--continue_on_fail', help='continue test on error', action='store_true', default=False)
    parser.add_argument('-f', '--fail_limit', help='fail count limit to stop test', type=int, default=sys.maxint)

    args = parser.parse_args()
    stop_on_fail = not args.continue_on_fail

    start_sequencer(args.site, args.fail_limit, stop_on_fail)
