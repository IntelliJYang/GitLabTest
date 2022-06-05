from x527.loggers import ZmqPublisher
from x527.rpc_server import RPCServerWrapper
from x527.rpc_client import RPCClientWrapper
from x527.fixture import Fixture
from threading import Thread
import zmq
from x527 import zmqports
from statemachine import TesterStateMachine
import time
import traceback
import argparse

class StatemachineServer(Thread):

    site_count = 4 #site_count defaults to 4. This number is only used if sequencers is nto specified

    def __init__(self, fixture, sequencers=None, publisher=None):
        super(StatemachineServer, self).__init__()

        self.sequencers = sequencers
        if sequencers is None:
            self.sequencers = StatemachineServer.connect_to_sequencers(self.site_count)


        if publisher:
            self.publisher = publisher
        else:
            ctx = zmq.Context().instance()
            self.publisher = ZmqPublisher(ctx, "tcp://*:" + str(zmqports.SM_RPC_PUB), "SM_RPC_SERVER")
            time.sleep(1)#give the publisher sometime
        self.sm = TesterStateMachine(fixture, self.sequencers)
        self.dispatcher = self.sm

        self.rpc_server = RPCServerWrapper(
            zmqports.SM_PORT,
            self.publisher,
            dispatcher=self.dispatcher
        ).rpc_server

    @staticmethod
    def connect_to_sequencers(site_count):
        '''
        This is a helper method to connect to sequencers
        '''
        sites = range(site_count)
        ctx = zmq.Context().instance()
        url2 = "127.0.0.1"
        url = "169.254.1.10"
        sequencers = [RPCClientWrapper("tcp://" + url2 + ':' + str(zmqports.SEQUENCER_PORT + site), 
                                        ZmqPublisher(ctx, "tcp://*:" + str(zmqports.SEQUENCER_PROXY_PUB + site),
                                                "Sequencer Proxy")).remote_server() for site in sites]
        return sequencers

    def stop_sequencers(self):
        for sequencer in self.sequencers:
            sequencer.client.transport.shutdown()
            sequencer.client.publisher.stop()

    def run(self):
        self.publisher.publish('Sequencer Starting...')
        print 'statemachine server starting'
        try:
            self.rpc_server.serve_forever()
            self.publisher.publish('Sequencer Stopped...')
            self.stop_sequencers()
            self.sm.log_handler.close() #since the thread can not be started again, I am not bothering to reset SM to a usable state.
        except Exception as e:
            print 'error running the state machine rpc server: ' + e.message
            print traceback.format_exc()
        print 'state machine server stoping'

import cmd
import os
from datetime import datetime
import readline
from x527.tinyrpc.protocols.jsonrpc import RPCError
readline.parse_and_bind("bind ^I rl_complete")

def handle_response(afunc):

    def _(*args, **kwargs):
        try:
            reply = afunc(*args, **kwargs)
            if reply is not None:
                print reply.result
        except RPCError as e:
            print e.message, os.linesep, traceback.format_exc()

    _.__doc__ = afunc.__doc__
    return _

class StateMachineCmdline(cmd.Cmd):
    prompt = 'sm>'
    intro = 'state machine'
    def __init__(self, sm):
        cmd.Cmd.__init__(self)
        self.sm = sm

    def do_EOF(self, line):
        '''Ctrl-D to quit sm without stopping the sm server'''
        return True

    @handle_response
    def do_abort(self, seq):
        '''abort the current running sequence'''
        if seq == None:
            seq = 0
        return self.sm.abort(seq)

    @handle_response
    def do_run(self, func):
        '''run the whole sequence without regard for any breakpoint'''
        return self.sm.__getattr__(func)()

    @handle_response
    def do_start(self, line):
        '''start'''
        e_travelers = {0:{'attributes':{'sn':000}}}
        return self.sm.start(e_travelers)

    @handle_response
    def do_finish(self, seq):
        '''finish'''
        return self.sm.finish(seq)

    @handle_response
    def do_state(self, line):
        '''get current state'''
        return self.sm.__getattr__('get_state')()

    def do_quit(self, line):
        '''quit sm and stop the sequencer server. If you just want to quit sm without stopping
        the sequencer server you shoudl use ctrl-D'''
        self.sm.__getattr__('::stop::')()
        return True


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--site', help='the site of the sequencer to connect to', type=int, default=0)

    args = parser.parse_args()

    fixture = Fixture()
    sequencers = StatemachineServer.connect_to_sequencers(1)
    server = StatemachineServer(fixture, sequencers=sequencers)
    server.start()
    sm_proxy = RPCClientWrapper('tcp://localhost' + ':' + str(zmqports.STATEMACHINE_PORT), 
                                ZmqPublisher(zmq.Context().instance(), "tcp://*:" + str(zmqports.SM_PROXY_PUB), 'SMProxy'))
    assert server.rpc_server.serving

    sm = StateMachineCmdline(sm_proxy.remote_server())
    sm.cmdloop()
