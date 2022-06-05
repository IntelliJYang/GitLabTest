import json
import time
from threading import Thread

import zmq

import events
import levels
from Configure import zmqports
from Common.tinyrpc.exc import RPCError

FATAL_ERROR = -10001
COMMIT_ERROR = -10002
ZIPPED_FILE_ERROR = -10003
InstantPuddingError = -10004
AMIOK_ERROR = -10005
IP_START_ERROR = -10006

error_codes_map = {
               FATAL_ERROR: 'fatal error',
               COMMIT_ERROR: 'commit error',
               ZIPPED_FILE_ERROR: 'zipped file error',
               InstantPuddingError: 'InstantPudding error',
               AMIOK_ERROR: 'AMIOK error',
               IP_START_ERROR: 'IP Start error'
              }


class ReportDataError(RPCError):
    def __init__(self, msg):
        self.msg = msg

    @classmethod
    def create(cls, event_type, key_error):
        msg = 'Missing Data field in report for event: ' + events.get_name(event_type) + '; ' + key_error.message
        return cls(msg)


class Report(object):

    event = None
    data = None

    def _to_dict(self):
        jdata = dict(event=self.event, data=self.data)
        return jdata

    def serialize(self):
        return json.dumps(self._to_dict())

    def __repr__(self):
        r_str = 'event=' + events.get_name(self.event) + '; data=' + str(self.data)
        return r_str


class ReporterProtocol(object):

    @staticmethod
    def create_report(event_type, **kwargs):
        report = Report()
        report.event = event_type
        try:
            if event_type == events.SEQUENCE_START:
                report.data = dict(name=kwargs['name'], version=kwargs['version'])
            elif event_type == events.SEQUENCE_END or event_type == events.UOP_DETECT or event_type == events.IP_START_FAIL_DETECT:
                r = kwargs['result']
                data = dict(result=r)
                if 'logs' in kwargs:
                    data['logs'] = kwargs['logs']
                else:
                    data['logs'] = ''
                if r == -1:
                    data['error'] = kwargs['error']
                report.data = data
            elif event_type == events.ITEM_START:
                names = ['index', 'group', 'GROUP', 'TID', 'tid', 'low', 'LOW',
                         'high', 'HIGH', 'unit', 'UNIT', 'description', 'DESCRIPTION']
                report.data = {k.lower(): v for k, v in kwargs.items() if k in names}
                report.data['to_pdca'] = kwargs['to_pdca']
            elif event_type == events.ITEM_FINISH:
                data = dict(result=kwargs['result'], tid=kwargs['tid'])
                if 'error' in kwargs:
                    data['error'] = kwargs['error']
                    data['value'] = kwargs['value']
                else:
                    data['value'] = kwargs['value']
                report.data = data
                report.data['to_pdca'] = kwargs['to_pdca']
            elif event_type == events.ATTRIBUTE_FOUND:
                data = dict(name=kwargs['name'], value=kwargs['value'])
                report.data = data
            elif event_type == events.REPORT_ERROR:
                error_code = kwargs['error_code']
                error_msg = error_codes_map[error_code]
                if 'error_msg' in kwargs:
                    error_msg = kwargs['error_msg']
                data = dict(error_code=kwargs['error_code'], error_msg=error_msg, site=kwargs['site'])
                report.data = data
            elif event_type == events.SEQUENCE_LOADED:
                report.data = dict(name=kwargs['name'])
            else:
                raise ReportDataError('unknown event_type ' + str(event_type))
        except KeyError as e:
            raise ReportDataError.create(event_type, e)

        return report

    @staticmethod
    def parse_report(msg):
        if 'data' in msg and 'event' in msg:
            report_dict = json.loads(msg)
            report = Report()
            report.event = report_dict['event']
            report.data = report_dict['data']
            return report
        else:
            print 'illegal report: {}'.format(msg)
            return None


class Reporter(object):

    def __init__(self, publisher):
        self.publisher = publisher
        self.protocol = ReporterProtocol()

    def report(self, event_type, **kwargs):
        report = self.protocol.create_report(event_type, **kwargs)
        self.publisher.publish(report.serialize(), level=levels.REPORTER)


class ReportListener(Thread):
    def __init__(self, port, url=None):
        super(ReportListener, self).__init__()
        ctx = zmq.Context.instance()
        self.subscriber = ctx.socket(zmq.SUB)
        if url is None:
            url = 'tcp://localhost:' + str(port)
        self.subscriber.connect(url)
        self.url = url
        self.subscriber.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self.receiving = True
        self.level = levels.REPORTER
        self.listeners = []

    def run(self):
        protocol = ReporterProtocol()
        self.receiving = True
        print 'ready to subscribe to ' + str(self.url)
        while self.receiving:
            try:
                topic, ts, level, origin, data = self.subscriber.recv_multipart(zmq.NOBLOCK)
                if int(level) == self.level:    # process Reporter message only
                    for listener in self.listeners:
                        listener.received(protocol.parse_report(data))
            except zmq.ZMQError:
                pass
            time.sleep(0.02)
        self.subscriber.setsockopt(zmq.LINGER, 0)
        self.subscriber.close()
