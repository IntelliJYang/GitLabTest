from core import *
import core
from x527 import zmqports
import time
from x527.tinyrpc.dispatch import RPCDispatcher, public


class TesterStateMachine(RPCDispatcher):

    states = ['idle', 'ready_to_load', 'testing', 'done', 'ok_to_unload']

    def __init__(self, fixture, sequencers):
        super(TesterStateMachine, self).__init__()
        self.log_handler = ZMQHandler('tcp://*:' + str(zmqports.SM_PUB))
        core.logger.handlers = []  #clear out the old handlers
        core.logger.addHandler(self.log_handler)
        core.logger.setLevel(logging.DEBUG)

        self.fixture = fixture
        self.sequencers = sequencers

        # Initialize the state machine
        self.machine = Machine(model=self, states=TesterStateMachine.states, initial='idle')

        # At some point, every superhero must rise and shine.
        #question 2: what if the test for are_all_finished happen to soon?
        self.machine.add_transition('dut_ready', 'idle', 'ready_to_load', before='open')
        self.machine.add_transition('abort', 'ready_to_load', 'idle', before='close')
        self.machine.add_transition('start', 'ready_to_load', 'testing', before='engage', after='start_test')
        self.machine.add_transition('start', 'testing', 'testing', after='start_test')
        self.machine.add_transition('start', 'done', 'testing', after='start_test')
        self.machine.add_transition('abort', 'testing', 'done', before='abort_test', conditions=['are_all_finished'])
        self.machine.add_transition('finish', 'testing', 'done', conditions=['are_all_finished'])
        self.machine.add_transition('will_unload', 'done', 'ok_to_unload', before = 'disengage')
        self.machine.add_transition('abort', 'ok_to_unload', 'done', before='close')
        self.machine.add_transition('dut_removed', 'ok_to_unload', 'idle', before='close')
        #give the zmq publisher some time
        time.sleep(2)
        self.register_triggers()#this adds the trigger to the dispatcher event map


    #before and after actions, these are not the public events
    def open(self):
        self.fixture.open()

    def close(self):
        self.fixture.close()

    def abort_test(self, site):
        self.sequencers[int(site)].abort()

    def engage(self, *args):
        self.fixture.engage()

    def start_test(self, e_travelers):
        if e_travelers != None:
            for s_site in e_travelers.keys():
                site = int(s_site)
                self.sequencers[site].run(e_travelers[s_site])
        else:
            self.sequencers[0].run()

    def disengage(self):
        self.fixture.disengage()

        #conditions
    def are_all_finished(self, *args):
        test_states = [s.status().result != "RUNNING" for s in self.sequencers]
        return all(test_states)

    def __del__(self):
        self.log_handler.close()

    #register the triggers to be publicly callable RPC methods
    def register_triggers(self):
        for event_name in self.machine.events.keys():
            self.add_method(self.machine.events[event_name].trigger, event_name)
        #add the function to get states
        self.add_method(lambda : self.machine.current_state.name, 'get_state')

