import sys
import os

if not __package__:
    path = os.path.join(os.path.dirname(__file__), os.pardir)
    sys.path.insert(0, path)

from threading import Thread
import time
from Common.publisher import ZmqPublisher
from ZmqLoggerTransport import LoggerServerTransport, LOGGER_PORT, LOGGER_PUB, ReporterProtocol
import zmq
import Configure.events as events
from Configure.constant import SLOTS
from Common.BBase import GetSN


class PrmLoggerServer(Thread):
    def __init__(self, log_folder='/tmp'):
        super(PrmLoggerServer, self).__init__()
        self.log_folder = log_folder
        self.log_paths = [None for sub in range(SLOTS)]
        self.file_handles = [None for sub in range(SLOTS)]
        ctx = zmq.Context()
        self.frontend = ctx.socket(zmq.ROUTER)
        endpoint = "tcp://*:{}".format(LOGGER_PORT)
        self.frontend.bind(endpoint)
        self.transport = LoggerServerTransport(self.frontend)
        self.publisher = ZmqPublisher(ctx, "tcp://*:%s" % (LOGGER_PUB), "PRMLogger")
        self.transport.publisher = self.publisher

    def run(self):
        """
        run the server for accepting action; a thread for monitor fixture status
        when accept a request from client, the monitor thread should be hang up,
        so use the thread lock
        :return:
        # """
        sequencer_event_map = {
            events.SEQUENCE_START: 'on_sequence_start',
            events.SEQUENCE_END: 'on_sequence_end',
            events.ITEM_START: 'on_item_start',
            events.ITEM_FINISH: 'on_item_finish',
            events.ATTRIBUTE_FOUND: 'on_attribute_found',
            events.SEQUENCE_LOADED: 'on_sequence_loaded',
            events.RECORE_EVENTS: "on_recode_handle"
        }
        print "server is running"
        while True:
            contex, message = self.transport.receive_message()
            if message:
                report = ReporterProtocol.parse_report(message)
                if report:
                    func_name = sequencer_event_map.get(report.event)
                    site = report.site
                    if func_name:
                        func = getattr(self, func_name, None)
                        if callable(func):
                            func(site, report.data)
                    else:
                        print 'Unrecognized event; {}'.format(report.event)
        self.transport.shutdown()

    def on_sequence_start(self, site, data):
        pass
        # # ts = datetime.datetime.strftime(datetime.now(),'%m-%d-%H-%M-%S')
        # sn = GetSN.get_mlbsn(site)
        # filename = '_'.join([sn,'UUT{}'.format(site)])
        # file_path = os.path.join(self.log_folder, filename)
        # self.log_paths[site] = file_path
        # log_f = open(file_path, 'w+')
        # self.release_log(site)
        # self._attach_log(site,log_f)
        # # func = getattr(self, 'post_sequence_start', None)
        # # if callable(func):
        # #     func(site, data)

    def on_item_start(self, site, data):
        self.write(site, self.__timestamp(data))

    def on_recode_handle(self, site, data):
        self.write(site, self.__timestamp(data))

    def _attach_log(self, site, handle):
        if handle:
            self.file_handles[site] = handle

    def release_log(self, site):
        log = self.file_handles[site]
        if log and not log.closed:
            log.close()
            self.file_handles[site] = None

    def write(self, site, data):
        log = self.file_handles[site]
        if log is None:
            return
        log.write(str(data))
        log.flush()

    @staticmethod
    def __timestamp(data):
        ts = str(time.strftime("%Y-%m-%d %H:%M:%2S", time.localtime()))
        return ts + ' ' * 10 + data + '\n'


if __name__ == '__main__':
    fs = PrmLoggerServer()
    fs.start()
