# coding=utf-8
import json
import os
from Common.BBase import cBruceConfig, cConvert

pwd = os.path.dirname(__file__)
config_dir = os.path.split(__file__)[0]
constant_path = os.path.join(config_dir, "constant.json")
gh_station_info = cBruceConfig('/vault/data_collection/test_station_config/gh_station_info.json')
const = cBruceConfig(constant_path)
MONITOR_INTERVAL = const.GetConfig("monitor")
SLOTS = const.GetConfig("slots")
GROUPS = const.GetConfig("group")
ROWS = const.GetConfig("rows")

HEARTBEAT_INTERVAL = const.GetConfig("HEARTBEAT_INTERVAL")
TSID = gh_station_info.GetConfig("ghinfo").get("STATION_ID")
TSID = gh_station_info.GetConfig("ghinfo").get("STATION_ID")
SFC_URL = gh_station_info.GetConfig("ghinfo").get("SFC_URL")

# GUI parameter
_GUI = const.GetConfig("gui")

# print _GUI,type(_GUI)
FIXTURE = _GUI.get("fixture")
looping_fixture_up = _GUI.get("looping_fixture_up")
looping_fixture_out = _GUI.get("looping_fixture_out")
MATRIX_SCANNER = cConvert.autoConvert(_GUI.get("matrix_scaner"))[0]
NO_NEED_SCAN_SN = cConvert.autoConvert(_GUI.get("no_need_scan_sn"))[0]
STATISTICBYSLOT = cConvert.autoConvert(_GUI.get("statistic_by_every_slot"))[0]
DEBUG_MODE = cConvert.autoConvert(_GUI.get("debug_mode"))[0]
AUTO_START = cConvert.autoConvert(_GUI.get("auto_start"))[0]
AUTO_SCAN = cConvert.autoConvert(_GUI.get("auto_scan"))[0]
SNMODE = cConvert.autoConvert(_GUI.get("sn_mode"))[0]
TAB_STATE = cConvert.autoConvert(_GUI.get("tab_state"))[0]
SCREEN_WIDTH = _GUI.get("screen_width")
SCREEN_HEIGHT = _GUI.get("screen_height")
OVER_ALL_SHOW = cConvert.autoConvert(_GUI.get("over_all"))[0]
TP_ALL_SHOW = cConvert.autoConvert(_GUI.get("tp_all"))[0]
# Title
_TITLE = const.GetConfig("title")
SOFT_VERSION = _TITLE.get("soft_version")
LOGO = _TITLE.get("company_logo")
PROJECT = _TITLE.get("project")
DEFAULT_TESTPLAN_VERSION = _TITLE.get("default_tp_version")

# process parameter
_PROCESS = const.GetConfig("process")
PDCA = cConvert.autoConvert(_PROCESS.get("pdca"))[0]
AUDIT = cConvert.autoConvert(_PROCESS.get("audit"))[0]
AUDIT_PATH = cConvert.autoConvert(_PROCESS.get("audit_test_plan"))[0]

STOP_ON_FAIL = cConvert.autoConvert(_PROCESS.get("stop_on_fail"))[0]
FAIL_LIMIT = _PROCESS.get("fail_limit")
LOGSET = const.GetConfig("logset")
XVCHANNEL = const.GetConfig("XVCHANNEL")
LEDSTATE = const.GetConfig("LEDSTATE")

# Simulator
_SIMULATOR = const.GetConfig("simulator")
SIMULATOR_FIXTURE = cConvert.autoConvert(_SIMULATOR.get("fixture"))[0]
# PATH Parameter
# pwd = os.path.dirname(__file__)

TEMPLATE_PATH = '/'.join(pwd.split('/')[:-1]) + '/TestEngine/Driver/Regex/'
print TEMPLATE_PATH

CAP_FCT_PATH = '/Users/gdlocal/Documents/prmtester'

FIXTURE_TYPE = const.GetConfig("fixture_type")
