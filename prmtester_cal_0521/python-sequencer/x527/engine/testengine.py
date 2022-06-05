import argparse
import cmd
import csv
import time
from threading import Thread

import zmq

from x527 import zmqports
from x527.loggers import StdOutPublisher, ZmqPublisher
from x527.rpc_client import RPCClientWrapper
from x527.rpc_server import RPCServerWrapper
from x527.tinyrpc.protocols import jsonrpc


class DummyDispatcher(object):
    func_list = []
    default_ret = '6000'

    def __init__(self, publisher):
        self.publisher = publisher

    def dispatch(self, request):
        self.publisher.publish(request.serialize(), 'Dispatcher received request')
        self.func_list.append(request.method)
        time.sleep(0.05)  # slow down the response a bit to avoid flooding ZMQ queue
        if request.method == jsonrpc.SERVER_READY:
            return request.respond('--PASS--')
        if request.method == 'long_test':
            time.sleep(5)
            return request.respond(True)
        if request.method == 'fixturetype':
            return request.respond('SIPFIXTURE')
        if request.method == 'station':
            return request.respond('COMBINE-FCT')
        if request.method == 'getsn':
            return request.respond('YM123456789')
        if request.method == 'measure':
            return request.respond(1.1101833258)
        if request.method == 'end_test':
            return request.respond('')
        if request.method == 'start_test':
            return request.respond('')
        if request.method == 'error':
            from x527.tinyrpc.protocols.jsonrpc import JSONRPCInvalidRequestError
            e = JSONRPCInvalidRequestError('fake error')
            return request.error_respond(e)
        if request.method == '::stop::':
            self.server.stop_server()  # this will stop the RPC server but console continues
        return request.respond(self.default_ret)


class ReplayDispatcher(object):
    def __init__(self, publisher, replay_file):
        self.publisher = publisher
        self.answers = []
        f = open(replay_file, 'rU')
        reader = csv.DictReader(f)
        for row in reader:
            self.answers.append(row['Return'])
        f.close()

    def dispatch(self, request):
        if request.method != '::stop::':
            return request.respond(self.answers.pop())


class DummyTestEngine(Thread):
    def __init__(self, site):
        super(DummyTestEngine, self).__init__()
        self.site = site

        ctx = zmq.Context().instance()
        # Ensure subscriber connection has time to complete
        time.sleep(1)
        self.publisher = ZmqPublisher(
            ctx,
            "tcp://*:" + str(zmqports.TEST_ENGINE_PUB + site),
            "DummyEngine_{}".format(site)
        )
        time.sleep(0.5)  # give time for the subscribers to connect to this publisher
        self.wrapper = RPCServerWrapper(
            zmqports.TEST_ENGINE_PORT + site,
            self.publisher,
            dispatcher=DummyDispatcher(self.publisher)
        )
        self.rpc_server = self.wrapper.rpc_server
        self.wrapper.dispatcher.server = self.wrapper

    def run(self):
        self.publisher.publish('Test Engine {} Starting...'.format(self.site))
        self.rpc_server.serve_forever()
        self.publisher.publish('Test Engine {} Stopped...'.format(self.site))


def client_routine(site, method, params, timeout=1000):
    try:
        client = RPCClientWrapper(
            'tcp://localhost' + ':' + str(zmqports.TEST_ENGINE_PORT+site),
            StdOutPublisher('TE')
        ).remote_server()
        client.__getattr__(method)(params, timeout=timeout)
    except jsonrpc.RPCError as e:
        print e.message


def test_engine(site):
    te = DummyTestEngine(site)
    te.start()
    t1 = Thread(target=client_routine, args=(site, jsonrpc.SERVER_READY, None, 500))
    t1.start()
    t2 = Thread(target=client_routine, args=(site, 'short', None))
    t2.start()
    time.sleep(0.5)
    # if the server receives the stop request first, the other client will hang waiting for reply
    t3 = Thread(target=client_routine, args=(site, '::stop::', None))
    t3.start()

    time.sleep(0.1)
    t4 = Thread(target=client_routine, args=(site, 'test_retry', None))
    t4.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    te.join()


class EngineCLI(cmd.Cmd):
    prompt = 'test engine>'
    intro = 'Dummy Engine driver'

    def default(self, line):
        self.proxy.__getattr__(line)()

    def do_quit(self, line):
        self.proxy.__getattr__('::stop::')()
        return True


def start_client(site):
    cli = EngineCLI()
    cli.proxy = RPCClientWrapper(
        'tcp://localhost' + ':' + str(zmqports.TEST_ENGINE_PORT+site),
        StdOutPublisher('TEProxy')
    ).remote_server()

    cli.cmdloop()


def start_server(site, doreturn=True):
    te = DummyTestEngine(site)
    te.start()
    if doreturn:
        return te


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', help='run a test', action='store_true')
    parser.add_argument('-s', '--site', help='the site of the sequencer to connect to', type=int, default=0)
    parser.add_argument('-o', '--server_only', help='only start the server', action='store_true', default=False)
    parser.add_argument('-c', '--client_only', help='only start the client', action='store_true', default=False)
    args = parser.parse_args()

    if args.test:
        test_engine(args.site)
        exit()

    site = args.site
    if args.client_only:
        start_client(site)
        exit()
    if args.server_only:
        server = start_server(site)
        server.join()
        exit()

    server = start_server(site)
    time.sleep(1)
    start_client(site)

    server.join()
