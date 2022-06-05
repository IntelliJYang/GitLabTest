# Put user customized logger callback functions or message formatters here
import os
from datetime import datetime

import zmq

from reportlogger import FileLogger


def blob_extra_files(self, site, data):
    """

    :param self:
    :param args:
    """
    self.log_paths = [
        [
            '/Users/Intelli_log/changedFileList.txt',
            '/vault/Intelli_log/fwupload.txt',
        ],
    ]


def pivot_item_finish_fail(self, site, data):
    res = data['result']
    if res == False or res == -1:
        dut = self.devices[site]
        item = dut.running_item
        self.write(
            site, 0,
            '%d,%s,%s,%s,%s,%s,%s,' % (
                site, dut.sn, item['group'], item['tid'], item['unit'], item['low'], item['high'])
        )
        self.write(site, 0, datetime.strftime(datetime.now(), '%m,%d,%H,%M,%S,%f,'))
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


class PwrSeqLogger(FileLogger):

    def on_sequence_start(self, site, data):
        self.tid = ''
        self.log_paths = [[] for i in range(self.site_count)]

    def on_item_start(self, site, data):
        self.tid = data['tid']

    def on_powerseq_data(self, socket, msg):
        if not self.tid:
            return
        data = self.default_log_formatter(msg, self.level)
        id = int(socket.getsockopt(zmq.IDENTITY)[-1])  # IDENTITY is port number aligned to 10s
        site = id / self.sub_per_site
        ts = datetime.strftime(datetime.now(), '%m-%d-%H-%M-%S')
        if 'Time' in data:
            filename = '_'.join([self.product, self.station_type, 'UUT{}'.format(site), ts, self.tid, self.suffix])
            log_path = os.path.join(self.log_folder, filename)
            log_f = open(log_path, 'w+')
            self.log_paths[site].append(log_path)
            self.release_log(site, 0)
            self._attach_log(site, 0, log_f)
            self.write(site, 0, data)
        else:
            self.write(site, 0, data)


def fpga_ts_log(self, socket, msg):
    def fpga_timestamp(ts):
        sec = ts[:8]
        usec = ts[8:]
        str_ts = str(int(sec, 16))
        return str(datetime.fromtimestamp(float(str_ts))) + '.' + str(int(usec, 16)).rjust(3, '0')

    import re
    ts_pattern = re.compile('([A-F0-9]{12})@R[01] (.*)', re.DOTALL)

    id = int(socket.getsockopt(zmq.IDENTITY)[-1])     # IDENTITY is port number aligned to 10s
    site = id / self.sub_per_site
    sub = id % self.sub_per_site
    data = self.default_log_formatter(msg, self.level)
    if not data:
        return
    if socket in self.auto_line_ending:
        data = str(data) + os.linesep
        if socket in self.need_timestamp:
            data = self._FileLogger__timestamp(data)
        self.write(site, sub, data)
    else:
        s = self.context_buffer[site][sub] + str(data)  # concat with last time leftover string
        self.context_buffer[site][sub] = ''
        lines = s.splitlines(True)
        for data in lines:
            if data.endswith(('\r', '\n')):
                if socket in self.need_timestamp:
                    data = self._FileLogger__timestamp(data)
                else:
                    m = ts_pattern.search(data)
                    if m:
                        data = fpga_timestamp(m.group(1)) + ' ' * 10 + m.group(2)
                self.write(site, sub, data)
            else:
                self.context_buffer[site][sub] = data
