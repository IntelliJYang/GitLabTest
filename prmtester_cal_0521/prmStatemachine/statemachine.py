import core
import thread
from core import *
from Configure import zmqports, constant
from Common.tinyrpc.dispatch import RPCDispatcher, public
from Common.tinyrpc.protocols.jsonrpc import JSONRPCErrorResponse


class TesterStateMachine(RPCDispatcher):
    states = ['idle', 'ready_to_load', 'testing', 'done', 'ok_to_unload']

    def __init__(self, fixture, sequencers, test_engines):
        super(TesterStateMachine, self).__init__()
        self.log_handler = ZMQHandler('tcp://*:' + str(zmqports.SM_PUB))
        core.logger.handlers = []  # clear out the old handlers
        core.logger.addHandler(self.log_handler)
        core.logger.setLevel(logging.DEBUG)

        self.fixture = fixture
        self.sequencers = sequencers
        self.testengines = test_engines
        self.looping_state = False

        # Initialize the state machine
        self.machine = Machine(model=self, states=TesterStateMachine.states, initial='idle')

        # At some point, every superhero must rise and shine.
        # question 2: what if the test for are_all_finished happen to soon?
        self.machine.add_transition('dut_ready', 'idle', 'ready_to_load')
        self.machine.add_transition('abort', 'ready_to_load', 'idle', before='close')
        self.machine.add_transition('start', 'ready_to_load', 'testing', after='start_test')
        self.machine.add_transition('start', 'testing', 'testing', after='start_test')
        self.machine.add_transition('start', 'done', 'testing', after='start_test')
        self.machine.add_transition('abort', 'testing', 'done', before='abort_test', conditions=['are_all_finished'])
        self.machine.add_transition('finish', 'testing', 'done', conditions=['are_all_finished'])
        self.machine.add_transition('finish', 'done', 'done')
        self.machine.add_transition('will_unload', 'done', 'ok_to_unload', before='fixture_up')
        self.machine.add_transition('abort', 'ok_to_unload', 'done', before='close')
        self.machine.add_transition('dut_removed', 'ok_to_unload', 'idle', before='close')

        self.register_triggers()  # this adds the trigger to the dispatcher event map

    # before and after actions, these are not the public events
    def open(self):
        pass
        # self.fixture.open()

    def close(self):
        # self.fixture.close()
        pass

    def fixture_in(self):
        if constant.SIMULATOR_FIXTURE:
            return True    # Gordon mark
        self.fixture.fixture_in()
        print 'fixture in .....'
        if self.fixture.fixture_down():
            print 'fixture down .....'
            return True, ''
        else:
            return False, 'Fixture Down Failed'

    def fixture_up(self):
        if constant.SIMULATOR_FIXTURE:
            return True    # Gordon mark
        if self.looping_state:
            if constant.looping_fixture_up:
                self.fixture.fixture_up()
                if constant.looping_fixture_out:
                    self.fixture.fixture_out()
        else:
            if not self.fixture.fixture_up():
                self.fixture.fixture_up()
            self.fixture.fixture_out()

    def get_fixture_status(self):
        return self.fixture.fixture_status()

    def abort_test(self, site):
        self.sequencers[int(site)].abort()
        self.testengines[int(site)].abort()

    def start_test(self, e_travelers):
        if e_travelers is not None:
            for s_site in e_travelers.keys():
                site = int(s_site)
                if not e_travelers[s_site].get("attributes", None):
                    thread.start_new_thread(self.sequencers[site].run, (None,))
                else:
                    thread.start_new_thread(self.sequencers[site].run, (e_travelers[s_site],))
        else:
            self.sequencers[0].run()

    def are_all_finished(self):
        test_states = [s.status().result != "RUNNING" for s in self.sequencers]
        return all(test_states)

    def load_test_plan(self, path):
        info = list()
        for seq in self.sequencers:
            ret = seq.load(path)
            if isinstance(ret, JSONRPCErrorResponse):
                info.append(ret.error)
            else:
                info.append(ret.result)
        load_states = [item.rfind('loaded') > 0 for item in info]
        return all(load_states), info

    def list_test_plan(self):
        return self.sequencers[0].list("all").result

    def set_looping_state(self, state):
        self.looping_state = state

    def __del__(self):
        self.log_handler.close()

    # register the triggers to be publicly callable RPC methods
    def register_triggers(self):
        for event_name in self.machine.events.keys():
            self.add_method(self.machine.events[event_name].trigger, event_name)
        # add the function to get states
        self.add_method(lambda: self.machine.current_state.name, 'get_state')
        self.add_method(self.load_test_plan)
        self.add_method(self.list_test_plan)
        self.add_method(self.set_looping_state)
        self.add_method(self.fixture_in)
