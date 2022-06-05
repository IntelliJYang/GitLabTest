from ZmqLoggerTransport import LoggerClientTransport,LOGGER_PORT,LOGGER_PUB,LoggerReport
import zmq
from Configure import zmqports
import Configure.events as events


class LoggerClient(object):
    def __init__(self, site=None):
        ctx = zmq.Context()
        self.transport = LoggerClientTransport.create(ctx, "tcp://localhost:%s" % LOGGER_PORT)
        self.site = site

    def send_only(self, data, event = events.RECORE_EVENTS, site=None):
        report = LoggerReport()
        report.event = event
        report.data = data
        if site==None:
            report.site = self.site
        else:
            report.site = site
        try:
            self.transport.send_only(report.serialize())
        except Exception as e:
            raise RuntimeError("Error %s" % e)


if __name__ == '__main__':
    a = LoggerClient()
    a.send_only("dasdasd", 1)