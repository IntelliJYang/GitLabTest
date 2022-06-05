import zmq
from Common.publisher import ZmqPublisher
from Common.rpc_client import RPCClientWrapper
from Fixture.fixture_client import ControlBoard
import Configure.zmqports as zmqports
from prmStatemachine.smrpcserver import StateMachineServer
import traceback
import argparse
import cmd
import os
import readline
from Common.tinyrpc.protocols.jsonrpc import RPCError

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
        e_travelers = {0: {'attributes': {'sn': 000}}}
        return self.sm.start(e_travelers)

    @handle_response
    def do_finish(self, seq):
        '''finish'''
        return self.sm.finish(seq)

    @handle_response
    def do_state(self, line):
        '''get current state'''
        return self.sm.__getattr__('get_state')()

    @handle_response
    def do_ready(self, line):
        """get ready"""
        return self.sm.dut_ready()

    @handle_response
    def do_load(self, path):
        """load test plan for every sequencer"""
        return self.sm.load_test_plan()

    @handle_response
    def do_list(self, line):
        """list test plan for sequencer[0]"""
        return self.sm.list_test_plan()

    def do_quit(self, line):
        '''quit sm and stop the sequencer server. If you just want to quit sm without stopping
        the sequencer server you shoudl use ctrl-D'''
        self.sm.__getattr__('::stop::')()
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--site', help='the site of the sequencer to connect to', type=int, default=1)

    args = parser.parse_args()
    fixture = ControlBoard()
    sequencers = StateMachineServer.connect_to_sequencers(5)
    server = StateMachineServer(fixture, sequencers=sequencers)
    server.start()
    sm_proxy = RPCClientWrapper('tcp://localhost' + ':' + str(zmqports.SM_PORT),
                                ZmqPublisher(zmq.Context().instance(), "tcp://*:" + str(14000), 'SMProxy'))
    assert server.rpc_server.serving
    sm = StateMachineCmdline(sm_proxy.remote_server())
    sm.cmdloop()
    # zmqports.SM_PROXY_PUB
