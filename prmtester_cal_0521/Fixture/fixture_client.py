import zmq
import traceback
from Configure import zmqports
from Common.tinyrpc.transports.zmq import ZmqClientTransport
import threading
from Configure.constant import FIXTURE_TYPE


class FixtureHandler(object):
    IN = "IN"
    OUT = "OUT"
    DOWN = "DOWN"
    UP = "UP"
    RESET = "RESET"
    FIXTURE_STATUS = "FIXTURE_STATUS"
    DUT_STATUS = "DUT_STATUS"

    # IN_OK = "S:IN OK"
    # OUT_OK = "S:FIXTURE OUT OK"
    DOWN_OK = "S:FIXTURE DOWN OK"
    UP_OK = "S:FIXTURE UP OK"
    RESET_OK = "S:FIXTURE UP OK"

    def __init__(self):
        super(FixtureHandler, self).__init__()


class FixtureClient(object):
    def __init__(self):
        ctx = zmq.Context().instance()
        transport = 'tcp://localhost:' + str(zmqports.FIXTURE_CTRL_PORT)
        self.transport = ZmqClientTransport.create(ctx, transport)
        self.transport.timeout = 15000

    def send_reply(self, cmd):
        result = ''
        try:
            result = self.transport.send_reply(cmd)
        except Exception as e:
            print e, traceback.format_exc()
        if result:
            print(result.strip())
        return result

    def send(self, cmd):
        self.send_reply(cmd)

    def send_only(self, cmd):
        t = threading.Thread(target=self.send_reply, args=(cmd,))
        t.setDaemon(True)
        t.start()


class ControlBoard(FixtureClient):
    def __init__(self, ):
        super(ControlBoard, self).__init__()
        FixtureClient().__init__()

    def query(self, cmd):
        if FIXTURE_TYPE == "PRM":
            if cmd == FixtureHandler.UP:
                cmd = FixtureHandler.RESET
            else:
                return "SUCCESS"
        result = self.send_reply(cmd)
        return result

    def engage(self):
        result = self.query(FixtureHandler.IN)
        if "SUCCESS" in result:
            return True
        else:
            return False

    def disengage(self):
        return self.query(FixtureHandler.RESET)

    def fixture_in(self):
        result = self.query(FixtureHandler.IN)
        if "SUCCESS" in result:
            return True
        else:
            return False

    def fixture_out(self):
        result = self.query(FixtureHandler.OUT)
        # if "SUCCESS" in result:
        #     return True
        # else:
        #     return False

    def fixture_up(self):
        result = self.query(FixtureHandler.UP)
        if "SUCCESS" in result:
            return True
        else:
            return False

    def fixture_down(self):
        result = self.query(FixtureHandler.DOWN)
        if "SUCCESS" in result:
            return True
        else:
            return False

    def dut_status(self):
        result = self.query(FixtureHandler.DUT_STATUS)
        if result:
            if "-64" in result:
                return True
            else:
                return False
        else:
            return False

    def fixture_status(self):
        return self.query(FixtureHandler.FIXTURE_STATUS)


if __name__ == '__main__':
    fc = ControlBoard()
    fc.dut_status()
    fc.send_reply("pass_uut0")
    # fc.fixture_status()
