import zmq
import time
import argparse
import traceback
from threading import Thread
from Configure import zmqports
from statemachine import TesterStateMachine
from Common.publisher import ZmqPublisher
from Common.rpc_client import RPCClientWrapper
from Common.rpc_server import RPCServerWrapper
from Configure.constant import SLOTS
from Fixture.fixture_client import ControlBoard
from Common.tinyrpc.protocols.jsonrpc import JSONRPCErrorResponse


class StateMachineServer(Thread):
    site_count = SLOTS

    def __init__(self, obj_fixture, obj_sequencers=None, obj_test_engines=None, publisher=None):
        super(StateMachineServer, self).__init__()
        if obj_sequencers is not None:
            self.sequencers = obj_sequencers
        else:
            self.sequencers = StateMachineServer.connect_to_sequencers(self.site_count)
        if publisher is not None:
            self.publisher = publisher
        else:
            ctx = zmq.Context().instance()
            self.publisher = ZmqPublisher(ctx, "tcp://*:" + str(zmqports.SM_RPC_PUB), "statemachine")
            time.sleep(1)  # give the publisher sometime

        self.sm = TesterStateMachine(obj_fixture, self.sequencers, obj_test_engines)

        self.rpc_server = RPCServerWrapper(zmqports.SM_PORT, self.publisher, dispatcher=self.sm).rpc_server

    def abort(self, site):
        try:
            self.sequencers[site].abort()
        except:
            pass

    @staticmethod
    def connect_to_sequencers(site_count):
        """
        This is a helper method to connect to sequencers
        """
        sites = range(site_count)
        ctx = zmq.Context().instance()
        url2 = "127.0.0.1"
        # url = "169.254.1.10"
        _sequencers = [RPCClientWrapper("tcp://" + url2 + ':' + str(zmqports.SEQUENCER_PORT + site),
                                        ZmqPublisher(ctx, "tcp://*:" + str(zmqports.SEQUENCER_PROXY_PUB + site),
                                                     "Sequencer Proxy")).remote_server() for site in sites]
        return _sequencers

    def stop_sequencers(self):
        for sequencer in self.sequencers:
            sequencer.client.transport.shutdown()
            sequencer.client.publisher.stop()

    @staticmethod
    def connect_to_testengines(site_count):
        sites = range(site_count)
        ctx = zmq.Context().instance()
        url2 = "127.0.0.1"
        _tes = [RPCClientWrapper("tcp://" + url2 + ':' + str(zmqports.TEST_ENGINE_PORT + site), None).remote_server()
                for site in sites]
        return _tes

    def run(self):
        self.publisher.publish('StateMachine Starting...')
        print 'state machine server starting'
        try:
            self.rpc_server.serve_forever()
            self.publisher.publish('StateMachine Stopped...')
            self.stop_sequencers()
            # since the thread can not be started again, I am not bothering to reset SM to a usable state.
            self.sm.log_handler.close()
        except Exception as e:
            print 'error running the state machine rpc server: ' + e.message
            print traceback.format_exc()
        print 'state machine server stopped'


class StateMachineProxy(object):

    def __init__(self, sm):
        self.sm = sm

    def ready(self):
        """get ready"""
        self.sm.dut_ready()

    def abort(self, seq):
        if seq is None:
            seq = 0
        self.sm.abort(seq)

    def start(self, e_travelers):
        assert isinstance(e_travelers, dict)
        return self.sm.start(e_travelers)

    def finish(self):
        try:
            self.sm.finish()
            return
        except Exception as e:
            print traceback.format_exc(e)

    def will_unload(self):
        """will_unload,disengage the fixture"""
        return self.sm.will_unload()

    def set_looping_state(self, state):
        self.sm.set_looping_state(state)

    def dut_removed(self):
        """dut_removed,close the serialport"""
        return self.sm.dut_removed()

    def load(self, path):
        """list test plan for sequencer[0]"""
        try:
            ret = self.sm.load_test_plan(path)
            if isinstance(ret, JSONRPCErrorResponse):
                return False, ret.error
            else:
                return ret.result[0], ret.result[1]
        except Exception as e:
            print e, traceback.format_exc()
            return False, e.message

    def list(self):
        """list test plan for sequencer[0]"""
        return self.sm.list_test_plan()

    def state(self):
        return self.sm.__getattr__('get_state')().result

    def fixture_in(self):
        try:
            ret = self.sm.fixture_in()
            if isinstance(ret, JSONRPCErrorResponse):
                return False, ret.error
            else:
                result = ret.result[0]
                msg = ret.result[1]
                return result, msg
        except Exception as e:
                print(e)
                return False, 'Fixture In Failed'



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--site', help='the site of the sequencer to connect to', type=int, default=1)
    # parser.add_argument('-g', '--group', help='the group of the sequencer', type=int, default=1)

    args = parser.parse_args()
    control_board = ControlBoard()  # Gordon mark
    sequencers = StateMachineServer.connect_to_sequencers(args.site)
    test_engines = StateMachineServer.connect_to_testengines(args.site)
    server = StateMachineServer(control_board, sequencers, test_engines)
    server.start()
