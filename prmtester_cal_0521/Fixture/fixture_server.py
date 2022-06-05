import sys
import os

if not __package__:
    path = os.path.join(os.path.dirname(__file__), os.pardir)
    sys.path.insert(0, path)

from threading import Thread
from Configure import driver_config
from Configure import zmqports
from Common.publisher import ZmqPublisher
from Fixture.ZmqfixtureTransport import ZmqFixtureTransport
import zmq
from Common.prmdriver import KSerial



class FixtureServer(Thread):
    def __init__(self):
        super(FixtureServer, self).__init__()
        self.serving = True
        # self.heartbeat_at = 0
        # create zmq context, every process have a context
        ctx = zmq.Context()
        # create a ROUTER socket for receiving fixture action

        self.frontend = ctx.socket(zmq.ROUTER)
        endpoint = "tcp://*:{}".format(zmqports.FIXTURE_CTRL_PORT)
        self.frontend.bind(endpoint)
        self.transport = ZmqFixtureTransport(self.frontend)
        self.publisher = ZmqPublisher(ctx, "tcp://*:%s" % zmqports.FIXTURE_CTRL_PUB, "FIXTURE")
        self.transport.publisher = self.publisher
        self.fixture_config = driver_config.FIXTURE_CFG
        self._port_name = self.fixture_config.get("port")
        self._baud_rate = self.fixture_config.get("baudrate")
        self.fixture = KSerial(self.fixture_config, self.publisher)
        # self.fixture.open()
        # self.log("fixture connected  ----- {}\n".format(self.fixture_config.get("port")))
        # except Exception as e:
        #     raise e
        # self.fixture_engaged = False
        # self.serving = False
    def get_fixture_config(self):
        return "portname: " + self._port_name + '\n' + "baudrate: " + str(self._baud_rate) + '\n'


    def fixture_connect(self):
        ret = self.fixture.open()
        print "ret is",ret
        if ret:
            self.log("fixture connected  ----- {}\n".format(self._port_name))
        else:
            self.log("fixture connect fail  ----- {}\n".format(self._port_name))
        return ret

    def run(self):
        """
        run the server for accepting action; a thread for monitor fixture status
        when accept a request from client, the monitor thread should be hang up,
        so use the thread lock
        :return:
        # """
        ret=""
        while self.serving:
            context, message = self.transport.receive_message()
            # print context,message
            if message:
                cmd = self.format_cmd(message)
                try:
                    self.fixture.send(cmd)
                    ret = 'SUCCESS'
                except Exception as e:
                    ret = 'NOT SUCCESS'
                self.transport.send_reply(context, str(cmd + ret))
            else:
                reply = self.fixture.read_all()
                if reply:
                    self.log(reply)

        self.transport.shutdown()

    def stop_serving(self):
        self.serving = False

    def format_cmd(self, message):
        # cmd = message
        cmd = str(self.fixture_config.get("startstr", "") + message + self.fixture_config.get("endstr", ""))
        return cmd

    def log(self, msg):
        if self.publisher:
            # print "*"*100
            # print msg
            # print "*" * 100
            self.publisher.publish(msg)


if __name__ == '__main__':
    fs = FixtureServer()
    fs.start()
