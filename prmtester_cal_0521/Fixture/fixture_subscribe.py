import threading
import zmq
from Configure import zmqports
import serial.tools.list_ports


class FixSub(threading.Thread):
    def __init__(self):
        super(FixSub, self).__init__()
        self.running = True
        ctx = zmq.Context()
        self.socket = ctx.socket(zmq.SUB)
        self.socket.connect("tcp://127.0.0.1:{}".format(zmqports.FIXTURE_CTRL_PUB))
        self.socket.setsockopt(zmq.SUBSCRIBE, "")

    def run(self):
        print("ready to subscribe to: \n")
        while self.running:
            topic, ts, level, origin, data = self.socket.recv_multipart()
            print(data)


if __name__ == '__main__':
    fix = FixSub()
    fix.start()
    fix.running = False
    fix.running = False
