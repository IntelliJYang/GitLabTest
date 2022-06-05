import json
import os
from PyQt5.QtCore import QObject
from multiprocessing import Process
from subprocess import call, Popen
import signal
import time
import sys
from Configure import constant
import traceback

pwd = os.path.dirname(__file__)
config_file = os.path.join(pwd, 'ProcessConfig.json')
f = open(config_file, 'rU')
config = json.load(f)
f.close()

seqDir = '/'.join(pwd.split('/')[:-1]) + '/python-sequencer'

# seqDir = "/Library/TestSW/python-sequencer"
prmDir = '/'.join(pwd.split('/')[:-1])


TEMP_PATH = seqDir + ':' + prmDir
os.putenv("PYTHONPATH",
          TEMP_PATH + ':/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC')


class ProcessManage(QObject):
    def __init__(self, site=0, group=1, fail_limit=1, stop_on_fail=False, objStatemachine=None):
        self.site = site
        self.group = group
        self.fail_limit = fail_limit
        self.stop_on_fail = stop_on_fail
        self.pid = dict()
        self.objStatemachine = objStatemachine

    def killPid(self, pid):
        try:
            os.kill(pid, signal.SIGKILL)
            print ('killed the {0} process'.format(pid))
        except OSError, e:
            print e, traceback.format_exc()
            # raise ("have no {0} process".format(pid))

    def killAll(self):
        try:
            for index, value in self.pid.iteritems():
                print index, value
                self.killPid(value)
            self.pid = dict()
        except OSError, e:
            raise OSError

    # def kill_one_module(self,modules):
    #     assert isinstance(modules,list)
    #     for module in modules:
    #         module.killPid()

    def call_one_process(self, *args):
        process = ["/usr/bin/python"]
        for item in args:
            process.append(item)
        p = Popen(process)
        # print "process is :",process
        return p.pid

    def startup_all_server(self, switch=False, audit=False):
        # self.start_prm_log_server()
        # self.start_prm_lock_server()
        self.start_engine_server(self.site)
        self.start_sequencer_server(self.site)
        self.start_statemachine_server(fixture=1)
        self.start_pdca_server(switch, audit)
        self.start_fixture_server()
        # self.start_prm_log_server()
        # self.start_DCSD_monitor()
        # self.start_Gui()

    def start_pdca_server(self, switch=False, audit=False):
        if self.pid.get('pdca'):
            self.killPid(self.pid.get('pdca'))
        file = seqDir + "/x527/loggers/logger.py"
        if switch and audit:
            self.pid["pdca"] = self.call_one_process(file, '-a')
            # self.pdca = True
            # self.audit = True
        elif switch and not audit:
            self.pid["pdca"] = self.call_one_process(file)
            # self.pdca = True
            # self.audit = False
        elif not switch and audit:
            self.pid["pdca"] = self.call_one_process(file, '-a', '-p')
            # self.pdca = False
            # self.audit = True
        elif not switch and not audit:
            self.pid["pdca"] = self.call_one_process(file, '-p')
            # self.pdca = False
            # self.audit = False

    def start_engine_server(self, site):
        file = prmDir + "/TestEngine/TestEngine.py"
        for i in xrange(site):
            site = "--uut={}".format(i)
            self.pid["eng{}".format(i)] = self.call_one_process(file, site)

    def start_sequencer_server(self, site):
        file = seqDir + "/x527/sequencer/sequencer.py"
        fail_limit = "--fail_limit={}".format(self.fail_limit)
        for i in xrange(site):
            site = "--site={}".format(i)
            if self.stop_on_fail:
                self.pid["seq{}".format(i)] = self.call_one_process(file, site, '-c', fail_limit)
            else:
                self.pid["seq{}".format(i)] = self.call_one_process(file, site)

    def start_statemachine_server(self, fixture=1):
        file = prmDir + "/prmStateMachine/smrpcserver.py"
        site = "--site={}".format(self.site)
        for i in xrange(fixture):
            self.pid["statemachine{}".format(i)] = self.call_one_process(file, site)

    def start_fixture_server(self):
        if self.pid.get('fixture'):
            self.killPid(self.pid.get('fixture'))
        file = prmDir + "/Fixture/fixture_server.py"
        self.pid["fixture"] = self.call_one_process(file)

    def start_prm_log_server(self):
        if self.pid.get('prmlog'):
            self.killPid(self.pid.get('prmlog'))
        file = prmDir + "/PrmLogger/loggers/logger.py"
        self.pid["prmlog"] = self.call_one_process(file)

    def start_prm_lock_server(self):
        if self.pid.get('prmlock'):
            self.killPid(self.pid.get('prmlock'))
        file = prmDir + "/CommonDriver/AynsLock/LockServer.py"
        self.pid["prmlock"] = self.call_one_process(file)

    def start_DCSD_monitor(self):
        if self.pid.get('dcsd_monitor'):
            self.killPid(self.pid.get('dcsd_monitor'))
        file = prmDir + "/Plugins/dcsd_monitor.py"
        self.pid["dcsd"] = self.call_one_process(file)

    def start_Gui(self):
        if self.pid.get('gui'):
            self.killPid(self.pid.get('gui'))
        file = prmDir + "/TestUI/prmmain.py"
        self.pid["gui"] = self.call_one_process(file)


class PasswordManagement(object):
    def __init__(self):
        self._pd = config.get("Password")
        self._op = self._pd.get("op")
        self._sp = self._pd.get("sp")

    def getOppassword(self):
        return self._op

    def getSppassword(self):
        return self._sp

    def setOppassword(self, pd):
        self._pd["op"] = pd
        config["Password"] = self._pd
        self.saveToJosn(config)

    def setSppassword(self, pd):
        self._pd["op"] = pd
        config["Password"] = self._pd
        self.saveToJosn(config)

    def saveToJosn(self, file1):
        with open(file1, "w") as f:
            json.dump(file1, f)


class Singleton(type):
    """
    This is a meta class to access singleton
    """
    # def __init__(self, *args, **kwargs):
    #    self.__instance = None
    #    super(Singleton, self).__init__()
    __instance = None

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(Singleton, self).__call__(*args, **kwargs)
        return self.__instance


class OpenScript(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._path = config.get("scriptpath")

    def getpath(self):
        return self._path

    def savepath(self, path):
        config["scriptpath"] = path
        with open(config_file, "w") as f:
            f.write(json.dumps(config, sort_keys=True, indent=4, separators=(',', ':')))
            # f.write(json.dumps(config))


from Common.BBase import cShell


class ProcessManagement(cShell):

    def __init__(self):
        self.__pid = dict()

    def popen_one_process(self, *args):
        process = ["/usr/bin/python"]
        for item in args:
            process.append(item)
        print process
        return self.RunShellWithTimeout(process)

    def killPid(self, pid):
        try:
            a = os.kill(pid, signal.SIGKILL)
            print ('killed the {0} process and the return is {1}'.format(pid, a))
        except OSError, e:
            raise ("have no {0} process".format(pid))

    def killAll(self):
        try:
            for index, value in self.__pid.iteritems():
                print index, value
                self.killPid(value)
        except OSError, e:
            raise OSError

    def start_statemachine_server(self, fixture=1):
        file = prmDir + "/StateMachine/StateMachine.py"
        site = "--slots=0"
        group = '--group=1'
        return self.popen_one_process(file, site, group)
