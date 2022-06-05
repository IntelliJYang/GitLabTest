import os
import zmq
from datetime import datetime

import events
import levels
import pypudding
import string
from publisher import NoOpPublisher
from reporter import ReporterProtocol


class DUT(object):
    def __init__(self, index):
        self.index = index
        self.sn = ''
        self.running_item = None


class ReportLogger(object):
    index = 0

    @staticmethod
    def next_index():
        ReportLogger.index += 1
        return ReportLogger.index


class FileLogger(ReportLogger):
    gh_info = pypudding.IPGHStation()
    product = gh_info[pypudding.IP_PRODUCT]
    station_type = gh_info[pypudding.IP_STATION_TYPE]
    station_id = gh_info[pypudding.IP_STATION_ID]
    station_num = gh_info[pypudding.IP_STATION_NUMBER]
    del gh_info

    def __init__(self, log_folder='/tmp', site_count=6, suffix='', level=levels.DEBUG):
        super(FileLogger, self).__init__()
        self.log_folder = log_folder
        self.site_count = site_count
        self.file_handles = [None for sub in range(site_count)]
        self.log_paths = [None for sub in range(site_count)]
        self.uut_sn = ['' for i in range(site_count)]
        self.suffix = suffix
        self.level = level
        self.need_timestamp = []
        self.auto_line_ending = []
        func = getattr(self, 'post_init', None)
        if callable(func):
            func()

    def get_log_path(self, site):
        if not self.log_paths:
            return ''
        elif len(self.log_paths) > site:
            return self.log_paths[site] if self.log_paths[site] else ''
        else:
            return self.log_paths[0] if self.log_paths[0] else ''

    def _attach_log(self, site, sub, handle):
        if handle:
            self.file_handles[site][sub] = handle

    def release_log(self, site, sub):
        log = self.file_handles[site][sub]
        if log and not log.closed:
            log.close()
            self.file_handles[site][sub] = None

    def _close(self):
        for site in range(self.site_count):
            for sub in range(self.sub_per_site):
                self.release_log(site, sub)

    @staticmethod
    def __timestamp(data):
        ts = str(datetime.now())
        return ts + ' ' * 10 + data

    def default_log_formatter(self, msg, threshold):
        if len(msg) == 5:
            topic, ts, level, origin, data = msg[:]
            if int(level) > threshold:
                return None
            ret = str(data)
        else:
            ret = str(msg[0])
        if '.csv' in self.suffix:
            ret = ret.replace(',', ';')
        return ret

    def default_log(self, socket, msg):
        id = int(socket.getsockopt(zmq.IDENTITY)[-1])  # IDENTITY is port number aligned to 10s
        site = id / self.sub_per_site
        sub = id % self.sub_per_site
        data = self.default_log_formatter(msg, self.level)
        if not data:
            return
        ts = str(datetime.now())
        if socket in self.auto_line_ending:
            if not data.endswith(os.linesep):
                data = data + os.linesep
            if socket in self.need_timestamp:
                data = self.__timestamp(data)
            self.write(site, sub, data)
        else:
            s = self.context_buffer[site][sub] + str(data)  # concat with last time leftover string
            self.context_buffer[site][sub] = ''
            lines = s.splitlines(True)
            for data in lines:
                if data.endswith(('\r', '\n')):
                    if socket in self.need_timestamp:
                        data = self.__timestamp(data)
                    self.write(site, sub, data)
                else:
                    self.context_buffer[site][sub] = data

    def write(self, site, sub, data):
        log = self.file_handles[site][sub]
        if log is None:
            return
        log.write(str(data))
        log.flush()

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
                return
            report = ReporterProtocol.parse_report(data)
            if report:
                func_name = sequencer_event_map.get(report.event)
                if func_name:
                    func = getattr(self, func_name, None)
                    if callable(func):
                        func(site, report.data)
                else:
                    print 'Unrecognized event; {}'.format(report.event), msg

    def on_sequence_start(self, site, data):
        ts = datetime.strftime(datetime.now(), '%m-%d-%H-%M-%S')
        for sub in range(self.sub_per_site):
            if self.sub_alias:
                mid_name = self.sub_alias[sub]
            elif self.sub_per_site == 1:
                mid_name = ''
            else:
                mid_name = 'CH{}'.format(sub)
            filename = '_'.join([self.product, self.station_type, 'UUT{}'.format(site), mid_name, ts, self.suffix])
            file_path = os.path.join(self.log_folder, filename)
            self.log_paths[site][sub] = file_path
            log_f = open(file_path, 'w+')
            self.release_log(site, sub)
            self._attach_log(site, sub, log_f)
            self.context_buffer[site][sub] = ''
        self.devices[site] = DUT(ReportLogger.next_index())
        func = getattr(self, 'post_sequence_start', None)
        if callable(func):
            func(site, data)

    def on_sequence_end(self, site, data):
        for sub in range(self.sub_per_site):
            if len(self.context_buffer[site][sub]) > 0:
                self.write(site, sub, self.context_buffer[site][sub] + os.linesep)
            self.release_log(site, sub)
        func = getattr(self, 'post_sequence_end', None)
        if callable(func):
            func(site, data)
