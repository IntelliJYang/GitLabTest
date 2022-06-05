import argparse
import cmd
import os
import time
from threading import Thread

import zmq

from x527.loggers import StdOutPublisher, ZmqPublisher
from x527.rpc_client import RPCClientWrapper
from x527.rpc_server import RPCServerWrapper
from x527.tinyrpc.protocols import jsonrpc


class DummyDispatcher(object):
    func_list = []

    def __init__(self, publisher):
        self.publisher = publisher

    def dispatch(self, request):
        self.publisher.publish(request.serialize(), 'Dispatcher received request')
        self.func_list.append(request.method)
        time.sleep(0.05)  # slow down the response a bit to avoid flooding ZMQ queue
        if request.method == '::stop::':
            self.server.stop_server()  # this will stop the RPC server but console continues
        return request.respond('--PASS--')


class DummyPublisher(Thread):
    def __init__(self, port, text, ending):
        super(DummyPublisher, self).__init__()
        self.port = port
        self.text = text
        self.ending = ending

        ctx = zmq.Context().instance()
        # Ensure subscriber connection has time to complete
        time.sleep(1)
        self.publisher = ZmqPublisher(
            ctx,
            "tcp://*:" + str(self.port),
            "Pub_{}".format(self.port)
        )
        time.sleep(0.5)  # give time for the subscribers to connect to this publisher
        self.wrapper = RPCServerWrapper(
            50 + self.port,
            self.publisher,
            dispatcher=DummyDispatcher(self.publisher)
        )
        self.rpc_server = self.wrapper.rpc_server
        self.wrapper.dispatcher.server = self.wrapper

    def run(self):
        while self.rpc_server.serving:
            time.sleep(0.2)
            if self.ending:
                self.publisher.publish(self.text + os.linesep)
            else:
                self.publisher.publish(self.text)


def start_server(port, text, ending, doreturn=True):
    dp = DummyPublisher(port, text, ending)
    dp.start()
    if doreturn:
        return dp


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='pub port', type=int, default=0)
    parser.add_argument('-t', '--text', help='text to emit', type=str, default='hello world,')
    parser.add_argument('-n', '--ending', help='line ending', action='store_true', default=False)
    args = parser.parse_args()

    port = args.port
    text = args.text
    ending = args.ending

    server = start_server(port, text, ending)
    raw_input()
    server.rpc_server.serving = False
    server.join()
