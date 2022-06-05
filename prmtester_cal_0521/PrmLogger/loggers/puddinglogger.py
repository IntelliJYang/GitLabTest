import shutil
import time
import traceback
import types
import zipfile
from decimal import *
from functools import wraps
import types

import events
import reporter
from pypudding import IPUUT, IPTestSpec, IPTestResult
from reporter import Reporter
from reportlogger import *
import thread

# refer to https://hwtewiki.apple.com:8443/display/dc/PDCA+Data+Structure+Definition
TEST = 1
SUBTEST = 2
UNIT = 3
FAIL_MSG = 4
VERSION = 5
LIMIT = 6
CHECK_UOP_INTERVAL = 5
special_results = ['--PASS--', '--FAIL--']
pdca_data_max_len = {
                    TEST: 48,
                    SUBTEST: 64,
                    UNIT: 10,
                    FAIL_MSG: 512,
                    VERSION: 48,
                    LIMIT: 48
                 }


def pdca_check(str_data, type):
    if len(str_data) <= pdca_data_max_len[type]:
        return str_data
    else:
        return str_data[:pdca_data_max_len[type]]


def check_pudding_exception(aFunc):
    """decorator to assert the reply represents a successful operation"""

    @wraps(aFunc)
    def asserted_func(*args, **kwargs):
        try:
            aFunc(*args, **kwargs)
        except pypudding.InstantPuddingError as e:
            sf = args[0]
            site = args[1]
            sf.reporter.report(events.REPORT_ERROR, site=site,
                               error_code=reporter.InstantPuddingError, error_msg=e.message)
            upload_log_file = sf.duts[site].log_file
            upload_log_file.write(e.message + os.linesep + traceback.format_exc())
    return asserted_func


def get_all_files(root_path):
    if root_path is None:
        return []
    if os.path.isfile(root_path):
        return [root_path]
    if os.path.isdir(root_path):
        return_list = []
        files = os.listdir(root_path)
        for file in files:
            if file.startswith('.'):
                continue  # ignore hidden files
            file = os.path.join(root_path, file)
            if os.path.isdir(file):
                return_list.extend(get_all_files(file))
            elif os.path.isfile(file):
                return_list.append(file)
            else:
                continue
        return return_list
    # if the input is not a file nor a folder, returns an empty list
    return []


def ispdata(str_data):
    try:
        if 'x' in str_data.lower():
            return False
        data_type = type(eval(str_data))
        if data_type is types.IntType or data_type is types.FloatType:
            return True
        else:
            return False
    except:
        return False


def pdca_numerical(str_data):
    try:
        data_type = type(eval(str_data))
        if data_type is types.IntType:
            return str(int(str_data))
        if data_type is types.FloatType:
            if 'e' not in str_data.lower():
                return str(float(str_data))
            else:
                prec = Decimal(str_data)._exp
                fmt_str = '{0:.'+str(abs(prec))+'f}'
                new = fmt_str.format(Decimal(str_data))
                return new
    except:
        print 'None integer/float value:', str_data
        return ''


class PuddingLogger(FileLogger):

    class PuddingUUT(object):
        def __init__(self, site):
            self.site = site
            self.uut = None
            self.current_spec = None
            self.log_file = None
            self.log_file_name = None
            self.log_paths = []

    def post_init(self):
        self.log_paths = []
        self.result = [None for i in range(self.site_count)]
        self.duts = [self.PuddingUUT(i) for i in range(self.site_count)]
        self.reporter = Reporter(self.publisher)
        self.check_uop_at = time.time() + CHECK_UOP_INTERVAL
        self.vendor_id = ''
        self.priority = pypudding.IP_PRIORITY_REALTIME

    def check_UOP(self, site, force=False):
        if self.priority is pypudding.IP_PRIORITY_STATION_CALIBRATION_AUDIT:
            return

        if not force and self.duts[site].uut.sn:
            if time.time() < self.check_uop_at:
                return
            else:
                self.check_uop_at = time.time() + CHECK_UOP_INTERVAL
        try:
            uut = self.duts[site].uut
            if uut is not None:
                uut.amIOkay()
        except pypudding.InstantPuddingError as e:
            self.reporter.report(events.REPORT_ERROR, site=site, error_code=reporter.AMIOK_ERROR,
                                 error_msg='AMIOK ERROR: '+e.message)

    def zip_logs(self, log_files, log_folder, sn, log, result):
        if len(log_files) == 0:
            return None
        if sn is None:
            sn = ''
        sn = sn.strip()
        ts = datetime.strftime(datetime.now(), '%m-%d-%H-%M-%S')
        dst = os.path.join(log_folder, 'Log', sn + '_' + ts + '_' + result)
        if not os.path.exists(os.path.join(log_folder, 'Log')):
            os.mkdir(os.path.join(log_folder, 'Log'))
        if len(sn) > 0:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            os.mkdir(dst)
        zf_path = os.path.join(self.log_folder, 'Log', sn + '_' + ts + '_' + result + '.zip')
        files = []
        for log_path in log_files:
            files.extend(get_all_files(log_path))
        if len(files) == 0:
            return None
        zf = zipfile.ZipFile(zf_path, 'w')
        for f in files:
            f_path, f_name = os.path.split(f)
            f_name = sn + '_' + f_name
            dest = os.path.join(dst, f_name)
            if os.path.exists(f):
                log.write('=======================>found log:' + str(f) + '\n')
                log.flush()
                if self.log_folder == f_path:
                    shutil.move(str(f), str(dest))
                else:
                    shutil.copy(str(f), str(dest))
            else:
                log.write('=======================>not found log:' + str(f) + '\n')
                log.flush()
            zf.write(dest, arcname=os.path.join(sn + '_' + ts + '_' + result, f_name), compress_type=zipfile.ZIP_DEFLATED)
        zf.close()
        return zf_path

    @check_pudding_exception
    def on_sequence_start(self, site, data):
        site_dut = self.duts[site]
        old_uut = site_dut.uut
        site_dut.uut = None
        if old_uut is not None:
            del old_uut
        uut = IPUUT()
        ts = datetime.strftime(datetime.now(), '%m-%d-%H-%M-%S')
        filename = self.product + '_' + self.station_type + '_UUT{}_'.format(site) + ts + '_pudding_upload.log'
        site_dut.log_file_name = os.path.join(self.log_folder, filename)
        site_dut.log_file = open(site_dut.log_file_name, 'w+')
        try:
            uut.start()
        except Exception as e:
            self.reporter.report(events.REPORT_ERROR, site=site, error_code=reporter.IP_START_ERROR,
                                 error_msg='IP_START_ERROR: '+str(e.message))
        site_dut.uut = uut
        uut.add_attribute(pypudding.IP_ATTRIBUTE_STATIONSOFTWARENAME, data['name'])
        version = data['version'] + '__' + data['name']
        uut.add_attribute(pypudding.IP_ATTRIBUTE_STATIONSOFTWAREVERSION, pdca_check(version, VERSION))
        self.vendor_id = ''

    @check_pudding_exception
    def on_item_start(self, site, data):
        self.check_UOP(site)
        self.publisher.publish('in item start: ' + str(data))

        test = pdca_check(str(data['group']).strip(), TEST)
        subtest = pdca_check(str(data['tid']).strip(), SUBTEST)
        unit = pdca_check(str(data['unit']).strip(), UNIT)
        low = pdca_check(str(data['low']).strip(), LIMIT)
        high = pdca_check(str(data['high']).strip(), LIMIT)

        if data['to_pdca']:
            if ispdata(low) and ispdata(high):
                spec = IPTestSpec(test,
                              subtest_name=subtest,
                              limits={'low_limit': low, 'high_limit': high},
                              unit=unit,
                              priority=self.priority)
            else:
                spec = IPTestSpec(test,
                              subtest_name=subtest,
                              priority=self.priority)
        old_spec = self.duts[site].current_spec
        self.duts[site].current_spec = None
        if old_spec is not None:
            del old_spec
        self.duts[site].current_spec = spec
        self.publisher.publish('in item start, spec=' + str(spec))

    @check_pudding_exception
    def on_item_finish(self, site, data):
        self.check_UOP(site)
        result = None
        value = str(data['value']).strip()
        if not data['to_pdca']:
            return
        self.publisher.publish('in item fish: ' + str(data))
        spec_str = str(self.duts[site].current_spec)
        if data['result'] < 0:
            error_msg = pdca_check(str(data['error']).strip()+' '+spec_str, FAIL_MSG)
            result = IPTestResult(pypudding.IP_FAIL, None, error_msg)
        if data['result'] == False:
            if 'error' in data:
                error_msg = pdca_check(str(data['error']).strip()+' '+spec_str, FAIL_MSG)
                if not ispdata(value):
                    result = IPTestResult(pypudding.IP_FAIL, '', error_msg)
                else:
                    result = IPTestResult(pypudding.IP_FAIL, value, error_msg)
            else:
                error_msg = pdca_check(str(data['value']).strip()+' '+spec_str, FAIL_MSG)
                if not ispdata(value):
                    result = IPTestResult(pypudding.IP_FAIL, '', error_msg)
                else:
                    result = IPTestResult(pypudding.IP_FAIL, value, error_msg)
        if data['result'] == True:
            if not ispdata(value):
                result = IPTestResult(pypudding.IP_PASS)
            else:
                result = IPTestResult(pypudding.IP_PASS, value)
        self.publisher.publish('spec='+str(self.duts[site].current_spec))
        self.publisher.publish('result='+str(data['value']))

        self.duts[site].uut.add_result(self.duts[site].current_spec, result)
        old_spec = self.duts[site].current_spec
        self.duts[site].current_spec = None
        del old_spec
        del result

    @check_pudding_exception
    def on_attribute_found(self, site, data):
        self.publisher.publish(str(data))
        attr_name = data['name'].upper()
        value = str(data['value'])
        if 'MLBSN' in attr_name:
            if len(value) > 0 and self.duts[site].uut.sn is None:
                self.duts[site].uut.set_sn(value)
                time.sleep(2)
                self.check_UOP(site, force=True)
                return
        if 'VENDOR_ID' in attr_name:
            self.vendor_id = value.split(':')[1]
        self.duts[site].uut.add_attribute(data['name'], value)

    def find_log_folder(self, site, file_list):
        if not isinstance(file_list, types.StringTypes):
            self.reporter.report(events.REPORT_ERROR, site=site, error_code=reporter.ZIPPED_FILE_ERROR,
                                 error_msg=str(file_list) + ' is not a string')
            upload_log_file = self.duts[site].log_file
            upload_log_file.write("=======================>Warning: file_list: " + str(file_list) + ", type: " + str(
                type(file_list)) + ", not string, set default ['']\n")
            return self.log_folder, ['']
        log_files = file_list.split(",")
        log_files = [fn for fn in log_files if len(fn.strip()) > 0]
        return self.log_folder, log_files

    def on_sequence_end(self, site, data):
        self.result[site] = int(data['result'])
        site_dut = self.duts[site]
        upload_log_file = site_dut.log_file
        log_folder, log_files = self.find_log_folder(site, data['logs'])
        site_dut.log_paths.extend(log_files)
        upload_log_file.write('=======================>engine log_folder:' + log_folder + '\n')
        upload_log_file.write('=======================>engine log_files:' + str(log_files) + '\n')
        upload_log_file.flush()

    def event_dispatch(self, socket, msg):
        sequencer_event_map = {
            events.SEQUENCE_START: 'on_sequence_start',
            events.SEQUENCE_END: 'on_sequence_end',
            events.ITEM_START: 'on_item_start',
            events.ITEM_FINISH: 'on_item_finish',
            events.ATTRIBUTE_FOUND: 'on_attribute_found',
            events.SEQUENCE_LOADED: 'on_sequence_loaded'
        }
        site = int(socket.getsockopt(zmq.IDENTITY)[-1])  # IDENTITY is port number aligned to 10s
        if len(msg) == 5:
            topic, ts, level, origin, data = msg[:]
            if int(level) > levels.REPORTER:
                return None
            report = ReporterProtocol.parse_report(data)
            if report:
                func_name = sequencer_event_map.get(report.event)
                if func_name:
                    func = getattr(self, func_name, None)
                    if callable(func):
                        func(site, report.data)
                else:
                    print 'Unrecognized event; {}'.format(report.event), msg
                if report.event == events.SEQUENCE_END:
                    # time.sleep(2) comment out this for csv copy in Korea 1107
                    thread.start_new_thread(self.on_logs_ready, (site, self.server.get_log_paths(site)))


    def on_logs_ready(self, site, data):
        site_dut = self.duts[site]
        uut = site_dut.uut
        sn = uut.sn
        upload_log_file = site_dut.log_file
        uut.set_DUT_position(self.vendor_id + str(self.station_num), str(site + 1))

        if self.result[site] >= 0:
            upload_log_file.write('=======================>add log:' + str(data) + '\n')
            upload_log_file.flush()
            site_dut.log_paths.extend(data)
            site_dut.log_paths.append(self.duts[site].log_file_name)

            upload_log_file.write('=======================>total logs:' + str(site_dut.log_paths) + '\n')
            upload_log_file.flush()
            if sn is None or len(sn) == 0:
                upload_log_file.write('=======================>UUT cancelled due to empty SN')
                upload_log_file.flush()
                upload_log_file.close()
                uut.cancel()
                self.cleanup(site)
                return
            try:
                if self.result[site]:
                    zipped_logs = self.zip_logs(site_dut.log_paths, self.log_folder, sn, upload_log_file, 'PASS')
                    blob_file_name = self.station_type + '_' + sn + '_' + 'PASS'
                else:
                    zipped_logs = self.zip_logs(site_dut.log_paths, self.log_folder, sn, upload_log_file, 'FAIL')
                    blob_file_name = self.station_type + '_' + sn + '_' + 'FAIL'
                upload_log_file.write('=======================>zipped_logs:' + str(zipped_logs) + '\n')
                upload_log_file.flush()
                if zipped_logs:
                    uut.add_blob_file(blob_file_name, zipped_logs)
                    shutil.rmtree(os.path.splitext(zipped_logs)[0])
                else:
                    self.reporter.report(events.REPORT_ERROR, site=site, error_code=reporter.ZIPPED_FILE_ERROR,
                                         error_msg=str(site_dut.log_paths) + ' not found in ' + str(self.log_folder))
            except Exception as e:
                upload_log_file.write('=======================>error creating zipped file: ' + e.message)
                upload_log_file.write(traceback.format_exc())
                upload_log_file.flush()
                self.reporter.report(events.REPORT_ERROR, site=site, error_code=reporter.ZIPPED_FILE_ERROR,
                                     error_msg=e.message)
            finally:
                upload_log_file.close()
            try:
                uut.done()
                if self.result[site]:
                    uut.commit(pypudding.IP_PASS)
                else:
                    uut.commit(pypudding.IP_FAIL)
            except pypudding.InstantPuddingError as e:
                self.reporter.report(events.REPORT_ERROR, site=site, error_code=reporter.COMMIT_ERROR,
                                     error_msg=e.message)
        else:
            uut.cancel()
        self.cleanup(site)

    def cleanup(self, site):
        site_dut = self.duts[site]
        site_dut.log_paths = []
        self.result[site] = None
