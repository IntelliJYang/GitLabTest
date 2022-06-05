#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasure Inc."
__email__ = "jinhui.huang@prmeasure.com"

import json
import os
import re
import sys
import time
import signal
import traceback
import multiprocessing
from Configure import constant
from Configure import zmqports
from threading import Thread
from Configure import levels
from Configure import events
from subprocess import Popen
from subscriber import SequencerSubscriberProcess
from PyQt5.QtCore import QObject, pyqtSignal
from Common.BBase import cSearchFile
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from Common.rpc_client import RPCClientWrapper
from GUI.controller.loop import LoopController
from GUI.controller.login import LoginController
from GUI.controller.snscan import SnScanController
from Fixture.fixture_server import FixtureServer
from GUI.controller.container import ContainerController
from GUI.controller.mainwindow import MainWindow
from prmStatemachine.auto_start import AutoStart
from prmStatemachine.smrpcserver import StateMachineProxy
from GUI.controller.sn_slot import SnSlotController
import fcntl
from Fixture.fixture_client import FixtureClient

pwd = os.path.dirname(__file__)
seqDir = '/'.join(pwd.split('/')[:-2]) + '/python-sequencer'
prmDir = '/'.join(pwd.split('/')[:-2])
TEMP_PATH = seqDir + ':' + prmDir
os.putenv("PYTHONPATH",
          TEMP_PATH + ':/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC')
pwd = os.path.dirname(__file__)
PROFILE = '/'.join(pwd.split('/')[:-2]) + '/Profile'
SITE_PATTERN = re.compile(r'Sequencer_(\d+)')


class Application(QApplication):
    # header timer control signal
    header_timer_signal = pyqtSignal(bool, name='header_timer')
    # statistic control signal (site, start, result)
    slots_timer_signal = pyqtSignal(int, bool, bool, name='slot_timer')
    # scan sn done
    scan_done_signal = pyqtSignal(list, name='scan_done')
    # loop state
    loop_signal = pyqtSignal(str, name='loop_signal')
    # fixture action
    auto_start_signal = pyqtSignal(str, name='auto_start')
    main_window_signal = pyqtSignal(str, name='main_window')
    uop_error_signal = pyqtSignal(str, name='uop_error')
    _list_result = [True for i in xrange(constant.SLOTS)]

    def __init__(self, *args):
        super(Application, self).__init__(*args)
        self.OK = True
        self._queue = multiprocessing.Queue()
        self._current_group_index = 0
        self._looping = False
        self._running = False
        self._group_sn_list_buffer = []
        self._group_sn_list = []
        self._fixture_server = None
        self._auto_start = None
        # loop gui exist flag
        self._looping_exist = False
        self.level = levels.REPORTER
        # current selected slots travelers
        self._current_e_travelers = {}
        # whether hand click start test
        self._hand_start = False
        # whether selected's slot is end or not
        self._selected_slot_end = {}
        # flag of whether receive message
        self._receiving = True
        self._ending = False
        self._audit_mode = constant.AUDIT
        self._pdca_mode = constant.PDCA
        self.fix_client = FixtureClient()

        try:
            self._pm = ProcessManage()
            if constant.FIXTURE_TYPE == "PRM":
                self.start_PRM_fixture_server()
            time.sleep(1)
            self.container_c = ContainerController()
            self.window = MainWindow(self.main_window_signal)
            self.window.setCentralWidget(self.container_c.view)
            self.window.set_window_center()
            self.create_action_connect()
            state_machine = RPCClientWrapper("tcp://" + '127.0.0.1' + ':' + str(zmqports.SM_PORT), None).remote_server()

            self._sm_proxy = StateMachineProxy(state_machine)
            self.load_test_plan()
            self._loop_c = LoopController(self.loop_signal)
            self.add_subscribers_of_sequencers_for_app()
            self._snscan_c = SnScanController(self.scan_done_signal)
            self.window.change_run_tool_state(False)
            self.create_auto_start()
            self.window.show()
        except Exception as e:
            print e, traceback.format_exc()
            sys.exit(self.exec_())

    def create_action_connect(self):
        self.window.open_action.triggered.connect(self.open_file_dialog)
        self.window.start_action.triggered.connect(self.app_start_clicked_action)
        self.window.stop_action.triggered.connect(self.app_stop_clicked_action)
        self.main_window_signal.connect(self.main_window_action)

        self.window.open_pdca_action.triggered.connect(self.app_open_pdca)
        self.window.close_pdca_action.triggered.connect(self.app_close_pdca)
        self.window.open_audit_action.triggered.connect(self.app_open_audit)
        self.window.close_audit_action.triggered.connect(self.app_close_audit)
        self.window.open_debug_action.triggered.connect(self.app_open_debug)
        # self.window.close_debug_action.triggered.connect(self.app_close_debug)
        if constant.TP_ALL_SHOW and constant.OVER_ALL_SHOW:
            self.window.overview_action.triggered.connect(self.display_overview)
            self.window.groupview_action.triggered.connect(self.display_groupview)

        self.header_timer_signal.connect(self.container_c.header_c.header_control_timer)
        self.slots_timer_signal.connect(self.container_c.content_c.statistic_c.statistic_sequence_control)
        self.window.loop_action.triggered.connect(self.create_loop_action)
        self.loop_signal.connect(self.loop_control)

        self.scan_done_signal.connect(self.scan_sn_done_action)
        self.auto_start_signal.connect(self.auto_start_action)
        self.uop_error_signal.connect(self.uopError)

    def main_window_action(self, event):
        if event == 'exit':
            self._receiving = False
            # self._fixture_server.stop_serving()
            self._auto_start.stop_serving()
            self.quit()
            os.system("pkill -9 python")
            os.system("pkill -9 Python")
            self._pm.killPid(os.getpid())

    def load_test_plan(self):
        try:
            if self._audit_mode:
                path = constant.AUDIT_PATH
            else:
                path = PROFILE
            filename, abs_file_path = cSearchFile.get_fist_filename(path, '.csv')
            if abs_file_path:
                self.open_file_dialog(abs_file_path)
        except Exception as e:
            QMessageBox.warning(QMessageBox(), "ERROR", "TestPlan_Name is {}".format(e))

    def open_file_dialog(self, tp_path):
        """
        if tp_path is empty , use filedialog for user to select testplan
        :param tp_path:
        :return:
        """
        abs_filename = tp_path
        try:
            if not abs_filename:
                abs_filename, _ = QFileDialog.getOpenFileName(QFileDialog(), 'Select test plan',
                                                              PROFILE,
                                                              "*.csv",
                                                              options=QFileDialog.DontUseNativeDialog)

            # check if the file exist
            if os.path.exists(abs_filename):
                # check if all sequencers loaded
                ret, msg = self._sm_proxy.load(abs_filename)
                if ret:
                    self._sm_proxy.list()
                    split_text = os.path.splitext(abs_filename)
                    if split_text[1].lower() == '.csv':
                        file_name = os.path.split(split_text[0])[-1]
                        if file_name:
                            self.container_c.header_c.display_tp_info(file_name)
                            self.container_c.content_c.tp_c.load_test_plan(abs_filename)
                            self.container_c.content_c.debug_c.load_test_plan(abs_filename)
                            self.container_c.content_c.over_c.set_row_count(
                                self.container_c.content_c.tp_c.get_row_count())
                else:
                    QMessageBox.warning(QMessageBox(), "ERROR", "Load Testplan Error {}".format(msg))
        except Exception as e:
            QMessageBox.warning(QMessageBox(), "ERROR", "TestPlan Name is Wrong")
            print e, traceback.format_exc()

    def app_start_clicked_action(self):
        self._running = True
        self._hand_start = True

        if self._looping:
            self.group_start(self._group_sn_list_buffer)
            self._looping = False
            return
        if constant.NO_NEED_SCAN_SN:
            self.header_timer_signal.emit(True)  # start header's timer
            self.no_need_scan_sn_start()
        else:
            if constant.GROUPS == 1:
                self._snscan_c.clear_all_info()
                _selected_slots = self.container_c.content_c.statistic_c.group_c.get_enable_slots_e_travelers()
                # self._snscan_c.set_selected_slots(_selected_slots
                self._snscan_c.view.check_all.setChecked(True)
                self._snscan_c.select_all_slots(True)
                self._snscan_c.view.show()
            elif constant.GROUPS > 1:
                self._snscan_c.view.show()
            else:
                pass

    def no_need_scan_sn_start(self):
        _e_travelers = []
        for i in range(constant.GROUPS):
            _e_travelers.append(dict())
            for j in range(constant.SLOTS):
                # if SnSlotController(j).check_slot():
                if self.container_c.content_c.statistic_c.group_c.statistic_list[j].slot_sn_c.check_slot():
                    _e_travelers[i][str(j)] = {"attributes": {"MLBSN": "", "cfg": ""}}
        self.group_start(_e_travelers)

    def app_stop_clicked_action(self):

        self._running = False
        self._hand_start = False
        # self._looping = False
        self._selected_slot_end = {}
        self.window.change_run_tool_state(False)
        for i in range(constant.SLOTS):
            self._sm_proxy.abort(i)
        self.container_c.header_c.header_control_timer(False)

    def add_subscribers_of_sequencers_for_app(self):
        self._subscriber = SequencerSubscriberProcess(self._queue)
        self._subscriber.daemon = True
        self._subscriber.start()

        t = Thread(target=self.queue_get, name='application_queue_get')
        t.setDaemon(True)
        t.start()

    def queue_get(self):
        while self._receiving:
            try:
                if self._queue.empty():
                    time.sleep(0.1)
                    continue
                else:
                    site, message = self._queue.get()
                    if constant.TP_ALL_SHOW:
                        self.container_c.content_c.tp_c.parse_sequencer_message(site, message)
                    if constant.OVER_ALL_SHOW:
                        self.container_c.content_c.over_c.parse_sequencer_message(site, message)
                    self.parse_sequencer_message(site, message)
            finally:
                pass

    def parse_sequencer_message(self, site, message):
        try:
            if message.event == events.SEQUENCE_START:
                self.sequence_start(site)
            elif message.event == events.SEQUENCE_END:
                result = message.data.get('result', 0)
                self.sequence_end(site, result)
            elif message.event == events.ITEM_START:
                pass
            elif message.event == events.ITEM_FINISH:
                self.item_finish(site, message)
            elif message.event == events.SEQUENCE_LOADED:
                pass
            elif message.event == events.LIST_ALL:
                pass
            elif message.event == events.UOP_DETECT:
                self.uop_error_signal.emit(str(message))
        except TypeError:
            print traceback.format_exc()

    def uopError(self, data):
        QMessageBox.critical(QMessageBox(), "UOP Error", data,
                             buttons=QMessageBox.Yes | QMessageBox.No)

    def sequence_start(self, site):
        """
        deal with sequence_start message from sequencer
        :param site:
        :return:
        """
        # current slot sequence start
        if not constant.SIMULATOR_FIXTURE:
            self.fix_client.send('blue_uut{}'.format(site))
        self._selected_slot_end[str(site)] = False

        # emit current timer to start counting
        self.slots_timer_signal.emit(site, True, False)

        self._list_result = [True for i in xrange(constant.SLOTS)]

    def sequence_end(self, site, result):
        # current slot sequence done
        self._selected_slot_end[str(site)] = True
        self.slots_timer_signal.emit(site, False, True if result > 0 else False)
        # if selected slots are all done, means current group is done
        if not constant.SIMULATOR_FIXTURE:
            self.fix_client.send('green_uut{}'.format(site) if result > 0 else 'red_uut{}'.format(site))
        self._list_result[int(site)] = True if result == 1 else False
        if all(self._selected_slot_end.values()):
            if all(self._list_result):
                self.container_c.header_c.stop_header_timer(["PASS"])
            else:
                self.container_c.header_c.stop_header_timer(["FAIL"])
            self.sequences_finish()

    def sequences_finish(self):
        self._selected_slot_end = {}
        # ent counting
        # self.header_timer_signal.emit(False)
        # self.container_c.header_c.stop_header_timer(self.test_result)
        self._sm_proxy.finish()
        self._sm_proxy.will_unload()
        self._sm_proxy.dut_removed()
        # test next group
        if self._running:
            time.sleep(1)
            for i in range(constant.SLOTS - self._current_group_index):
                if self.group_test():
                    break
                else:
                    continue

    def item_start(self, site):
        pass

    def item_finish(self, site, message):
        try:
            # if test item has get_mlbsn update result to gui
            if 'Parse MLB SN' in message.data.get('tid'):
                if message.data.get('value') == "--FAIL--":
                    pass
                else:
                    self.container_c.content_c.statistic_c.group_c.set_slot_sn(site, message.data.get('value'))
        except Exception as e:
            print e, traceback.format_exc()

    def create_loop_action(self):
        """
        display loop dialog
        :return:
        """
        self._looping_exist = True
        size = self.window.geometry()
        self._loop_c.view.move((size.width() / 2), size.top())
        self._loop_c.view.show()

    def loop_control(self, flag):
        """
        for loop controller to control test, emit by LoopController from loop.py
        :param flag:
        :return:
        """
        if self._looping_exist and self._loop_c.looping:
            if flag == 'start':
                self.app_start_clicked_action()
                self._looping = True

            elif flag == 'abort':
                self.app_stop_clicked_action()
            elif flag == 'hide':
                self._looping = False
                self._looping_exist = False
        else:
            self._looping = False

    def scan_sn_done_action(self, e_travelers_list):
        """
        this function emit by class SnScanController from snscan.py
        :param e_travelers_list:
        :return:
        """
        if e_travelers_list:
            # update groups info
            self.group_start(e_travelers_list)
        else:
            self.cancel_test()

    def cancel_test(self):
        self._loop_c.set_loop_out()

    def group_start(self, e_travelers_list):
        """
        update group info,
        :return:
        """
        self.window.change_run_tool_state(True)
        self.container_c.content_c.statistic_c.group_c.enable_selected(False)
        self._current_group_index = -1
        self._running = True
        self._hand_start = True
        self.update_group_info_to_ui(e_travelers_list)
        self._group_sn_list = e_travelers_list
        self._group_sn_list_buffer = e_travelers_list[:]

        for i in range(constant.GROUPS):
            if self.group_test():
                break
            else:
                continue

    def group_test(self):
        self._current_group_index += 1

        if len(self._group_sn_list) > 0:
            constant.GROUPS - len(self._group_sn_list)
            self._current_e_travelers = self._group_sn_list.pop(0)

            self._selected_slot_end = {}
            # if e_travelers is not empty, it means, at least one slot selected.
            if self._current_e_travelers:
                _slots_checked = self.container_c.content_c.over_c.get_all_slots_selected_state()[
                    self._current_group_index]

                # _slots_checked = self.container_c.content_c.statistic_c.group_c.get_slots_info()

                if any(_slots_checked):
                    # Gordon mark
                    if not constant.SIMULATOR_FIXTURE:
                        b_ret, str_ret = self._sm_proxy.fixture_in()
                        if not b_ret:
                            QMessageBox.warning(QMessageBox(), "ERROR", str_ret)
                            self.window.change_run_tool_state(False)
                            # self.container_c.content_c.statistic_c.change_state(False)
                            # self.container_c.content_c.statistic_c.group_c.enable_selected(True)
                            self._running = False
                            self._hand_start = False
                            return True
                    # self._sm_proxy.ready()  # Gordon mark
                    self.container_c.content_c.tp_c.reset_result_column()
                    self.container_c.content_c.over_c.set_current_group_index(self._current_group_index)
                    for k in self._current_e_travelers.keys():
                        if not _slots_checked[int(k)]:
                            self._current_e_travelers.pop(k)
                        else:
                            self._selected_slot_end[k] = False
                    # update current group slots info to ui
                    self.container_c.content_c.statistic_c.group_c.set_slots_info(self._current_e_travelers)
                    self.header_timer_signal.emit(True)  # start header's timer
                    self._sm_proxy.ready()
                    # if constant.SIMULATOR_FIXTURE:
                    print self._current_e_travelers
                    self._sm_proxy.start(self._current_e_travelers)
                    return True
                else:
                    return False
            else:
                # if current group is empty
                return False
        else:
            self.group_finish()
            return True

    def group_finish(self):
        self.window.change_run_tool_state(False)
        self.container_c.content_c.statistic_c.group_c.enable_selected(True)
        self._running = False
        self._hand_start = False
        self.container_c.header_c.header_control_timer(False)
        # self.container_c.header_c.stop_header_timer(self.test_result)
        # check if looping
        if self._loop_c.looping and self._looping_exist:
            try:
                self._loop_c.next_round()
            except Exception as e:
                print e, traceback.format_exc()
        else:
            self._looping = False

    def app_open_pdca(self):
        if LoginController.get_password():
            self._pdca_mode = True
            self._pm.start_logger_server(pdca=self._pdca_mode, audit=self._audit_mode)
            self.container_c.header_c.switch_pdca(self._pdca_mode)
            self.window.close_pdca_action.setDisabled(False)
            self.window.open_pdca_action.setEnabled(False)

    def app_close_pdca(self):
        if LoginController.get_password():
            self._pdca_mode = False
            self._pm.start_logger_server(pdca=self._pdca_mode, audit=self._audit_mode)
            self.container_c.header_c.switch_pdca(self._pdca_mode)
            self.window.close_pdca_action.setDisabled(True)
            self.window.open_pdca_action.setEnabled(True)

    def app_open_audit(self):
        if LoginController.get_password():
            self._audit_mode = True
            self._pm.start_logger_server(pdca=self._pdca_mode, audit=self._audit_mode)
            self.container_c.header_c.switch_audit(self._audit_mode)
            self.window.close_audit_action.setDisabled(False)
            self.window.open_audit_action.setEnabled(False)

    def app_close_audit(self):
        if LoginController.get_password():
            self._audit_mode = False
            self._pm.start_logger_server(pdca=self._pdca_mode, audit=self._audit_mode)
            self.container_c.header_c.switch_audit(self._audit_mode)
            self.window.close_audit_action.setDisabled(True)
            self.window.open_audit_action.setEnabled(True)

    def app_open_debug(self):
        if LoginController.get_password():
            self.start_debugcontainer()
            # self.container_c.content_c.open_debug()
            # self.window.close_debug_action.setDisabled(False)
            # self.window.open_debug_action.setEnabled(False)
            # self.window.start_action.setDisabled(True)
            # self.window.loop_action.setDisabled(True)
            # self.window.stop_action.setDisabled(True)

    def start_debugcontainer(self):
        server_file = prmDir + "/GUi/controller/debugcontainer.py"
        self._pm.create_one_process('debug', server_file)

    def app_close_debug(self):
        if LoginController.get_password():
            self.container_c.content_c.close_debug()
            self.window.close_debug_action.setDisabled(True)
            self.window.open_debug_action.setEnabled(True)
            self.window.start_action.setEnabled(True)
            self.window.loop_action.setEnabled(True)
            self.window.stop_action.setDisabled(True)

    def display_overview(self):
        self.container_c.content_c.change_page(0)

    def display_groupview(self):
        self.container_c.content_c.change_page(1)

    def start_PRM_fixture_server(self):
        message_box = QMessageBox()
        message_box.setModal(True)
        desktop = QApplication.desktop()
        message_box.move((desktop.width() - message_box.width()) / 2, 0)

        _connected = True
        self._fixture_server = FixtureServer()
        if constant.SIMULATOR_FIXTURE:
            self._fixture_server.start()
            return True
        if self._fixture_server.fixture_connect():
            self._fixture_server.start()
        else:
            while True:
                flag = QMessageBox.critical(message_box, "Connect Fail",
                                            "CAN NOT CONNECT TO FIXTURE!!!\n"
                                            "\nPlease make sure fixture is exist.\n\n"
                                            + self._fixture_server.get_fixture_config()
                                            + "\nContinue, Anyway?",
                                            buttons=QMessageBox.Yes | QMessageBox.No | QMessageBox.Retry)
                if flag == QMessageBox.Retry:
                    if self._fixture_server.fixture_connect():
                        self._fixture_server.start()
                        _connected = True
                        break
                elif flag == QMessageBox.Yes:
                    self._fixture_server.start()
                    _connected = True
                    break
                elif flag == QMessageBox.No:
                    _connected = False
                    break
        return _connected

    def create_auto_start(self):
        self._auto_start = AutoStart(self.auto_start_signal)

    def auto_start_action(self, action):
        if self._running:
            if action == 'group_end':
                self.app_stop_clicked_action()
                # self._snscan_c.view.show()
                return
        if action == 'group_start':
            if self._hand_start:
                self._snscan_c.scan_confirm()
                self._sm_proxy.start(self._current_e_travelers)
                if self.OK:
                    self.header_timer_signal.emit(True)  # start header's timer
                return
            else:
                if constant.NO_NEED_SCAN_SN:
                    self.no_need_scan_sn_start()
                else:
                    if constant.AUTO_SCAN:
                        _e_travelers_list = self._auto_start.get_e_travelers_list()
                        self.group_start(_e_travelers_list)
                    else:
                        self._group_sn_list = []

        elif action == 'group_end':
            self.OK = True
            self.app_stop_clicked_action()
            if self._looping_exist:
                return
            else:
                self.header_timer_signal.emit(False)
                time.sleep(1)
                self.app_start_clicked_action()
                self._snscan_c.view.show()

        elif action == 'start_counting':
            self.container_c.header_c.header_control_timer(True)
            self.OK = False

    def update_group_info_to_ui(self, e_travelers_list):
        self.container_c.content_c.over_c.reset()
        self.container_c.content_c.over_c.update_e_travelers(e_travelers_list)


class ProcessManage(QObject):
    def __init__(self):
        super(ProcessManage, self).__init__()
        self._site = constant.SLOTS
        self._group = constant.GROUPS
        self._fail_limit = constant.FAIL_LIMIT
        self._stop_on_fail = constant.STOP_ON_FAIL
        self._pid_dict = dict()

        self.start_sequencer_server(self._site)
        self.start_engine_server(self._site)
        self.start_logger_server(constant.PDCA, constant.AUDIT)
        self.start_state_machine_server(fixture=1)
        # self.start_prm_log_server()
        # Gordon mark
        if constant.FIXTURE_TYPE != "PRM":
            self.start_fixture_server()

        time.sleep(3)

    def kill_by_name(self, name):
        popen = self._pid_dict.get(name)
        try:
            if popen:
                os.kill(popen.pid, signal.SIGKILL)
        except OSError, e:
            print e, traceback.format_exc()

    def killPid(self, pid):
        try:
            a = os.kill(pid, signal.SIGKILL)
            print ('killed the {0} process and the return is {1}'.format(pid, a))
        except OSError, e:
            raise ("have no {0} process".format(pid))

    def kill_all_pid_in_dict(self):
        try:
            for _, popen in self._pid_dict.iteritems():
                os.kill(popen.pid, signal.SIGKILL)
            self._pid_dict = dict()
        except OSError, e:
            print e, traceback.format_exc()

    def create_one_process(self, name, *args):
        command = ["/usr/bin/python"]
        for item in args:
            command.append(item)
        p = Popen(command)
        self._pid_dict[name] = p

    def start_logger_server(self, pdca=False, audit=False):
        self.kill_by_name('logger')
        server_file = seqDir + "/x527/loggers/logger.py"

        if pdca and audit:
            self.create_one_process('logger', server_file, '-a')
        elif pdca and not audit:
            self.create_one_process('logger', server_file)
        elif not pdca and audit:
            self.create_one_process('logger', server_file, '-a', '-p')
        elif not pdca and not audit:
            self.create_one_process('logger', server_file, '-p')

    def start_engine_server(self, site):
        server_file = prmDir + "/TestEngine/TestEngine.py"
        for i in xrange(site):
            site = "--uut={}".format(i)
            self.create_one_process("engine{}".format(i), server_file, site)

    def start_sequencer_server(self, site):
        server_file = seqDir + "/x527/sequencer/sequencer.py"
        fail_limit = "--fail_limit={}".format(self._fail_limit)
        for i in xrange(site):
            site = "--site={}".format(i)
            if self._stop_on_fail:
                self.create_one_process("sequencer{}".format(i), server_file, site, '-c', fail_limit)
            else:
                self.create_one_process("sequencer{}".format(i), server_file, site)

    def start_state_machine_server(self, fixture=1):
        server_file = prmDir + "/prmStateMachine/smrpcserver.py"
        site = "--site={}".format(self._site)
        for i in xrange(fixture):
            self.create_one_process("state_machine{}".format(i), server_file, site)

    def start_prm_log_server(self):
        if self._pid_dict.get('prmlog'):
            self.kill_by_name('prmlog')
        server_file = prmDir + "/PrmLogger/loggers/logger.py"
        self.create_one_process('prmlog', server_file)

    def start_fixture_server(self):
        server_file = prmDir + "/Fixture/stream_server.py"
        if not os.path.exists(server_file):
            server_file = prmDir + "/Fixture/stream_server.pyc"
        self.create_one_process('fixture', server_file)

if __name__ == '__main__':
    os.system("pkill -9 python")
    os.system("pkill -9 Python")
    app = Application(sys.argv)
    sys.exit(app.exec_())
