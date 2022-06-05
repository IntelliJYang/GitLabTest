import json

from Configure import events


class SequencerProtocol(object):
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
