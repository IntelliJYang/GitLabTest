import os
from datetime import datetime

import levels
from reportlogger import FileLogger
SKIP_ITEM = 2
from publisher import NoOpPublisher
import time


class CSVLogger(FileLogger):

    class CSVRun(object):
        def __init__(self, ts):
            self.sn = ''
            self.items = []
            self.start_ts = ts
            self.result = ''
            self.fail_list = ''

    def post_init(self):
        self.header_written = False
        # self.create_log('NA')
        # initial log with empty sequence name as sequence_load event could happen before logger is ready
        self.runs = [None for i in range(self.site_count)]

    def create_log(self, seq_name):
        ts = datetime.strftime(datetime.now(), '%m-%d-%H-%M-%S')
        filename = self.product + '_' + self.station_type + '_' + seq_name + '_' + ts + '_all.csv'
        if not os.path.exists(os.path.join(self.log_folder, 'CSV')):
            os.mkdir(os.path.join(self.log_folder, 'CSV'))
        log_path = os.path.join(self.log_folder, 'CSV', filename)
        self.log_paths[0][0] = log_path
        log_f = open(log_path, 'w+')
        self.file_handles[0][0] = log_f
        log_f.write('Product,SerialNumber,Station_ID,Site_ID,PASS/FAIL,Error_Message,Failed_List,Test Start Time,'
                         'Test Stop Time,')
        log_f.flush()
        self.header_written = False

    def on_sequence_start(self, site, data):
        self.runs[site] = None
        self.runs[site] = self.CSVRun(datetime.strftime(datetime.now(), "\t%Y-%m-%d %X\t"))

    def on_item_start(self, site, data):
        item = dict(tid=data['group']+'@'+data['tid'],
                    low=data['low'], high=data['high'], unit=data['unit'], result='')
        self.runs[site].items.append(item)

    def on_item_finish(self, site, data):
        run = self.runs[site]
        item = run.items[-1]
        if 'value' in data:
            result = str(data['value'])
        else:
            result = str(data['error'])
        item['result'] = result.replace(',', ';')
        if data['result'] < 1:
            run.fail_list += item['tid'] + ';'

    def on_attribute_found(self, site, data):
        if 'MLBSN' in data['name'].upper():
            self.runs[site].sn = data['value']

    def on_sequence_end(self, site, data):
        run = self.runs[site]
        log_f = self.file_handles[0][0]
        if not self.header_written:
            skip_fields = ',,,,,,,,,'
            for item in run.items:
                log_f.write(item['tid'] + ',')
            log_f.write(os.linesep + 'Upper Limited----------->' + skip_fields)
            for item in run.items:
                log_f.write(item['high'] + ',')
            log_f.write(os.linesep + 'Lower Limited----------->' + skip_fields)
            for item in run.items:
                log_f.write(item['low'] + ',')
            log_f.write(os.linesep + 'Measurement unit------>' + skip_fields)
            for item in run.items:
                log_f.write(item['unit'] + ',')
            log_f.write(os.linesep)
            log_f.flush()
            self.header_written = True

        if data['result'] > 0:
            run.result = 'PASS'
        else:
            run.result = 'FAIL'
        msg = ''
        if 'error_msg' in data:
            msg = data.get('error_msg', '')
        if ',' in msg:
            msg = msg.replace(',', ';')

        # if site == 0:
        #     Site_ID = "Left"
        # else:
        #     Site_ID = "Right"

        Site_ID = site
        line = '{0},{1},{2},{3},{4},{5},{6},{7},{8},'.format(
                                                            self.product,     # Product
                                                            run.sn,           # SerialNumber
                                                            self.station_id,  # Station_ID
                                                            Site_ID,             # Site_ID
                                                            run.result,       # PASS/FAIL
                                                            msg,              # Error_Message
                                                            run.fail_list,    # Failed_List
                                                            run.start_ts,     # Test Start Time
                                                            datetime.strftime(datetime.now(), "\t%Y-%m-%d %X\t"),# Test Stop Time
                                                            )
        for item in run.items:
            line += str(item['result']) + ','
        log_f.write(line + os.linesep)
        log_f.flush()

    def on_sequence_loaded(self, site, data):
        self.release_log(0, 0)
        self.create_log(data['name'])

    def get_log_path(self, site):
        return ''


class PivotLogger(FileLogger):

    def post_sequence_start(self, site, data):
        self.write(site, 0, 'site,sn,group,tid,unit,low,high,month,day,hour,minute,second,microsec,timecount,result,value,fail_msg\n')

    def on_item_start(self, site, data):
        item = dict(group=data['group'], tid=data['tid'], unit=data['unit'],
                    low=data['low'], high=data['high'], result='', msg='')
        self.devices[site].running_item = item
        self.start_time=time.time()

    def on_item_finish(self, site, data):
        dut = self.devices[site]
        item = dut.running_item
        self.write(
            site, 0,
            '%d,%s,%s,%s,%s,%s,%s,' % (site, dut.sn, item['group'], item['tid'], item['unit'], item['low'], item['high'])
        )
        self.write(site, 0, datetime.strftime(datetime.now(), '%m,%d,%H,%M,%S,%f,'))
        self.write(site, 0, '{}'.format(round(time.time()-self.start_time, 4)) + ',')
        res = data['result']
        if res == True:
            self.write(site, 0, 'Pass' + ',')
        elif res == SKIP_ITEM:
            self.write(site, 0, 'Skip' + ',')
        else:
            self.write(site, 0, 'Fail' + ',')
        if 'error' in data:
            error = str(data['error'])
            if ',' in error:
                error = error.replace(',', ';')
            self.write(site, 0, ',' + error)
        else:
            value = str(data['value'])
            if ',' in value:
                value = value.replace(',', ';')
            self.write(site, 0, value + ',')
        self.write(site, 0, os.linesep)
        self.uut_sn[site] = str(dut.sn)

    def on_attribute_found(self, site, data):
        if 'MLBSN' in data['name'].upper():
            self.devices[site].sn = data['value']


def flow_log_item_start(self, site, data):
    """

    :param self:
    :param site:
    :param data:
    """
    item = dict(group=data['group'], tid=data['tid'], unit=data['unit'], low=data['low'], high=data['high'],
                result='', msg='')
    self.devices[site].running_item = item
    self.devices[site].time = time.time()

    # self.write(site, 0, '==Test: ' + item['group'] + os.linesep)
    self.write(site, 0, str(datetime.now()) + ' '*3 + '==SubTest: ' + item['tid'] + ' '*3+ '-'+' '*3 + 'Titem_{}'.format(self.devices[site].current_index)+ os.linesep)
    self.devices[site].current_index += 1
    return


def flow_log_item_finish(self, site, data):
    """
    :param self:
    :param site:
    :param data:
    """
    item = self.devices[site].running_item
    start_time = self.devices[site].time
    if 'error' in data:
        value = str(data['error'])
    else:
        value = str(data['value'])
    self.write(site, 0,  str(datetime.now()) + ' '* 3 + 'lower:{0}; upper:{1}; value:{2}'.format(item['low'], item['high'], value) + os.linesep)
    res = data['result']
    if res == True:
        result = 'PASS'
    elif res == SKIP_ITEM:
        result = 'SKIP'
    else:
        result = 'FAIL'
    self.write(site, 0, str(datetime.now()) + ' '*3 + '[Result  :]' + result + '==> ' + value + os.linesep)
    self.write(site, 0, str(datetime.now()) + ' '*3 + 'Cycle  Time  :' + str(round(float((time.time()-start_time)),3))+ os.linesep+ os.linesep)
    return
