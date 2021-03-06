try:
    from builtins import object
except ImportError:
    # python2
    pass
from functools import partial
from collections import defaultdict, OrderedDict
from six import string_types
import inspect
import logging
import zmq
import datetime
from Configure import levels
import Configure.zmqports as zmqports
import threading


class ZMQHandler(logging.Handler):
    def __init__(self, endpoint, ctx=None, socktype=zmq.PUB, identity='statemachine'):
        logging.Handler.__init__(self)
        self.ctx = ctx or zmq.Context().instance()
        self.socket = self.ctx.socket(socktype)
        self.socket.setsockopt(zmq.IDENTITY, identity)
        self.socket.bind(endpoint)
        self.identity = identity
        self.level = levels.DEBUG
        # self.lock = threading.Lock() Not necessary, handler is already thread safe

    def close(self):
        if zmq is None:  # the zmq module may have been released by this time
            return
        if not self.socket.closed:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

    def emit(self, record):
        t = datetime.datetime.now()
        ts = datetime.datetime.strftime(t, '%m-%d_%H:%M:%S.%f')
        id_str = self.identity + '_core'
        self.socket.send_multipart([str(zmqports.PUB_CHANNEL), str(ts), str(self.level), str(id_str), str(record.msg)])


logger = logging.getLogger('Statemachine_core')


def listify(obj):
    if obj is None:
        return []
    else:
        return obj if isinstance(obj, (list, type(None))) else [obj]


class State(object):

    def __init__(self, name, on_enter=None, on_exit=None,
                 ignore_invalid_triggers=False):
        """
        Args:
            name (string): The name of the state
            on_enter (string, list): Optional callable(s) to trigger when a
                state is entered. Can be either a string providing the name of
                a callable, or a list of strings.
            on_exit (string, list): Optional callable(s) to trigger when a
                state is exited. Can be either a string providing the name of a
                callable, or a list of strings.
            ignore_invalid_triggers (Boolean): Optional flag to indicate if
                unhandled/invalid triggers should raise an exception

        """
        self.name = name
        self.ignore_invalid_triggers = ignore_invalid_triggers
        self.on_enter = listify(on_enter) if on_enter else []
        self.on_exit = listify(on_exit) if on_exit else []

    def enter(self, event_data):
        """ Triggered when a state is entered. """
        for oe in self.on_enter:
            event_data.machine.callback(
                getattr(event_data.model, oe), event_data)
        logger.info("Entered state %s" % self.name)

    def exit(self, event_data):
        """ Triggered when a state is exited. """
        for oe in self.on_exit:
            event_data.machine.callback(
                getattr(event_data.model, oe), event_data)
        logger.info("Exited state %s" % self.name)

    def add_callback(self, trigger, func):
        """ Add a new enter or exit callback.
        Args:
            trigger (string): The type of triggering event. Must be one of
                'enter' or 'exit'.
            func (string): The name of the callback function.
        """
        callback_list = getattr(self, 'on_' + trigger)
        callback_list.append(func)


class Transition(object):
    class Condition(object):

        def __init__(self, func, target=True):
            self.func = func
            self.target = target

        def check(self, event_data):
            """ Check whether the condition passes.
            Args:
                event_data (EventData): An EventData instance to pass to the
                condition (if event sending is enabled) or to extract arguments
                from (if event sending is disabled). Also contains the data
                model attached to the current machine which is used to invoke
                the condition.
            """
            predicate = getattr(event_data.model, self.func)
            if event_data.machine.send_event:
                return predicate(event_data) == self.target
            else:
                return predicate(
                    *event_data.args, **event_data.kwargs) == self.target

    def __init__(self, source, dest, conditions=None, unless=None, before=None,
                 after=None):
        """
        Args:
            source (string): The name of the source State.
            dest (string): The name of the destination State.
            conditions (string, list): Condition(s) that must pass in order for
                the transition to take place. Either a string providing the
                name of a callable, or a list of callables. For the transition
                to occur, ALL callables must return True.
            unless (string, list): Condition(s) that must return False in order
                for the transition to occur. Behaves just like conditions arg
                otherwise.
            before (string or list): callbacks to trigger before the
                transition.
            after (string or list): callbacks to trigger after the transition.
        """
        self.source = source
        self.dest = dest
        self.before = [] if before is None else listify(before)
        self.after = [] if after is None else listify(after)

        self.conditions = []
        if conditions is not None:
            for c in listify(conditions):
                self.conditions.append(self.Condition(c))
        if unless is not None:
            for u in listify(unless):
                self.conditions.append(self.Condition(u, target=False))

    def execute(self, event_data):
        """ Execute the transition.
        Args:
            event: An instance of class EventData.
        """
        machine = event_data.machine
        for func in self.before:
            machine.callback(getattr(event_data.model, func), event_data)
            logger.info("Executing callback '%s' before transition." % func)

        # ww:before functions should be called before we check the conditions
        # ww:however, state exit function can only be called after we check the conditions
        logger.info("Initiating transition from state " + self.source + ' to state ' + self.dest + '...')
        for c in self.conditions:
            if not c.check(event_data):
                logger.info(
                    "Transition condition failed: %s() does not return %s. Transition halted." % (c.func, c.target))
                return False

        machine.get_state(self.source).exit(event_data)
        machine.set_state(self.dest)
        event_data.update()
        machine.get_state(self.dest).enter(event_data)
        for func in self.after:
            machine.callback(getattr(event_data.model, func), event_data)
            logger.info("Executed callback '%s' after transition." % func)
        return True

    def add_callback(self, trigger, func):
        """ Add a new before or after callback.
        Args:
            trigger (string): The type of triggering event. Must be one of
                'before' or 'after'.
            func (string): The name of the callback function.
        """
        callback_list = getattr(self, trigger)
        callback_list.append(func)


class EventData(object):

    def __init__(self, state, event, machine, model, args, kwargs):
        """
        Args:
            state (State): The State from which the Event was triggered.
            event (Event): The triggering Event.
            machine (Machine): The current Machine instance.
            model (object): The model/object the machine is bound to.
            args (list): Optional positional arguments from trigger method
                to store internally for possible later use.
            kwargs (dict): Optional keyword arguments from trigger method
                to store internally for possible later use.
        """
        self.state = state
        self.event = event
        self.machine = machine
        self.model = model
        self.args = args
        self.kwargs = kwargs

    def update(self):
        """ Updates the current State to accurately reflect the Machine. """
        self.state = self.machine.current_state


class Event(object):

    def __init__(self, name, machine):
        """
        Args:
            name (string): The name of the event, which is also the name of the
                triggering callable (e.g., 'advance' implies an advance()
                method).
            machine (Machine): The current Machine instance.
        """
        self.name = name
        self.machine = machine
        self.transitions = defaultdict(list)

    def add_transition(self, transition):
        """ Add a transition to the list of potential transitions.
        Args:
            transition (Transition): The Transition instance to add to the
                list.
        """
        self.transitions[transition.source].append(transition)

    def trigger(self, *args, **kwargs):
        """ Serially execute all transitions that match the current state,
        halting as soon as one successfully completes.
        Args:
            args and kwargs: Optional positional or named arguments that will
                be passed onto the EventData object, enabling arbitrary state
                information to be passed on to downstream triggered functions.
        """
        state_name = self.machine.current_state.name
        if state_name not in self.transitions:
            if not self.machine.current_state.ignore_invalid_triggers:
                raise MachineError(
                    "Can't trigger event %s from state %s!" % (self.name,
                                                               state_name))
        event = EventData(self.machine.current_state, self, self.machine,
                          self.machine.model, args=args, kwargs=kwargs)
        for t in self.transitions[state_name]:
            event.transition = t
            if t.execute(event):
                return True
        return False


class Machine(object):

    def __init__(self, model=None, states=None, initial=None, transitions=None,
                 send_event=False, auto_transitions=True,
                 ordered_transitions=False, ignore_invalid_triggers=None,
                 before_state_change=None, after_state_change=None):
        """
        Args:
            model (object): The object whose states we want to manage. If None,
                the current Machine instance will be used the model (i.e., all
                triggering events will be attached to the Machine itself).
            states (list): A list of valid states. Each element can be either a
                string or a State instance. If string, a new generic State
                instance will be created that has the same name as the string.
            initial (string): The initial state of the Machine.
            transitions (list): An optional list of transitions. Each element
                is a dictionary of named arguments to be passed onto the
                Transition initializer.
            send_event (boolean): When True, any arguments passed to trigger
                methods will be wrapped in an EventData object, allowing
                indirect and encapsulated access to data. When False, all
                positional and keyword arguments will be passed directly to all
                callback methods.
            auto_transitions (boolean): When True (default), every state will
                automatically have an associated to_{state}() convenience
                trigger in the base model.
            ordered_transitions (boolean): Convenience argument that calls
                add_ordered_transitions() at the end of initialization if set
                to True.
            ignore_invalid_triggers: when True, any calls to trigger methods
                that are not valid for the present state (e.g., calling an
                a_to_b() trigger when the current state is c) will be silently
                ignored rather than raising an invalid transition exception.
            before_state_change: A callable called on every change state before
                the transition happened. It receives the very same args as normal
                callbacks
            after_state_change: A callable called on every change state after
                the transition happened. It receives the very same args as normal
                callbacks
        """
        self.model = self if model is None else model
        self.states = OrderedDict()
        self.events = {}
        self.current_state = None
        self.send_event = send_event
        self.auto_transitions = auto_transitions
        self.ignore_invalid_triggers = ignore_invalid_triggers
        self.before_state_change = before_state_change
        self.after_state_change = after_state_change

        if initial is None:
            self.add_states('initial')
            initial = 'initial'
        self._initial = initial

        if states is not None:
            self.add_states(states)

        self.set_state(self._initial)

        if transitions is not None:
            transitions = listify(transitions)
            for t in transitions:
                if isinstance(t, list):
                    self.add_transition(*t)
                else:
                    self.add_transition(**t)

        if ordered_transitions:
            self.add_ordered_transitions()

    @property
    def initial(self):
        """ Return the initial state. """
        return self._initial

    def is_state(self, state):
        """ Check whether the current state matches the named state. """
        return self.current_state.name == state

    def get_state(self, state):
        """ Return the State instance with the passed name. """
        if state not in self.states:
            raise ValueError("State '%s' is not a registered state." % state)
        return self.states[state]

    def set_state(self, state):
        """ Set the current state. """
        if isinstance(state, string_types):
            state = self.get_state(state)
        self.current_state = state
        self.model.state = self.current_state.name

    def add_state(self, *args, **kwargs):
        """ Alias for add_states. """
        self.add_states(*args, **kwargs)

    def add_states(self, states, on_enter=None, on_exit=None,
                   ignore_invalid_triggers=None):
        """ Add new state(s).
        Args:
            state (list, string, dict, or State): a list, a State instance, the
                name of a new state, or a dict with keywords to pass on to the
                State initializer. If a list, each element can be of any of the
                latter three types.
            on_enter (string or list): callbacks to trigger when the state is
                entered. Only valid if first argument is string.
            on_exit (string or list): callbacks to trigger when the state is
                exited. Only valid if first argument is string.
            ignore_invalid_triggers: when True, any calls to trigger methods
                that are not valid for the present state (e.g., calling an
                a_to_b() trigger when the current state is c) will be silently
                ignored rather than raising an invalid transition exception.
                Note that this argument takes precedence over the same
                argument defined at the Machine level, and is in turn
                overridden by any ignore_invalid_triggers explicitly
                passed in an individual state's initialization arguments.
        """

        ignore = ignore_invalid_triggers
        if ignore is None:
            ignore = self.ignore_invalid_triggers

        states = listify(states)
        for state in states:
            if isinstance(state, string_types):
                state = State(
                    state, on_enter=on_enter, on_exit=on_exit,
                    ignore_invalid_triggers=ignore)
            elif isinstance(state, dict):
                if 'ignore_invalid_triggers' not in state:
                    state['ignore_invalid_triggers'] = ignore
                state = State(**state)
            self.states[state.name] = state
            setattr(self.model, 'is_%s' %
                    state.name, partial(self.is_state, state.name))
            state_name = state.name
            #  Add enter/exit callbacks if there are existing bound methods
            enter_callback = 'on_enter_' + state_name
            if hasattr(self.model, enter_callback) and \
                    inspect.ismethod(getattr(self.model, enter_callback)):
                state.add_callback('enter', enter_callback)
            exit_callback = 'on_exit_' + state_name
            if hasattr(self.model, exit_callback) and \
                    inspect.ismethod(getattr(self.model, exit_callback)):
                state.add_callback('exit', exit_callback)
        # Add automatic transitions after all states have been created
        if self.auto_transitions:
            for s in self.states.keys():
                self.add_transition('to_%s' % s, '*', s)

    def add_transition(self, trigger, source, dest, conditions=None,
                       unless=None, before=None, after=None):
        """ Create a new Transition instance and add it to the internal list.
        Args:
            trigger (string): The name of the method that will trigger the
                transition. This will be attached to the currently specified
                model (e.g., passing trigger='advance' will create a new
                advance() method in the model that triggers the transition.)
            source(string): The name of the source state--i.e., the state we
                are transitioning away from.
            dest (string): The name of the destination State--i.e., the state
                we are transitioning into.
            conditions (string or list): Condition(s) that must pass in order
                for the transition to take place. Either a list providing the
                name of a callable, or a list of callables. For the transition
                to occur, ALL callables must return True.
            unless (string, list): Condition(s) that must return False in order
                for the transition to occur. Behaves just like conditions arg
                otherwise.
            before (string or list): Callables to call before the transition.
            after (string or list): Callables to call after the transition.

        """
        if trigger not in self.events:
            self.events[trigger] = Event(trigger, self)
            setattr(self.model, trigger, self.events[trigger].trigger)

        if isinstance(source, string_types):
            source = list(self.states.keys()) if source == '*' else [source]

        if self.before_state_change:
            before = listify(before) + listify(self.before_state_change)

        if self.after_state_change:
            after = listify(after) + listify(self.after_state_change)

        for s in source:
            t = Transition(s, dest, conditions, unless, before, after)
            self.events[trigger].add_transition(t)

    def add_ordered_transitions(self, states=None, trigger='next_state',
                                loop=True, loop_includes_initial=True):
        """ Add a set of transitions that move linearly from state to state.
        Args:
            states (list): A list of state names defining the order of the
                transitions. E.g., ['A', 'B', 'C'] will generate transitions
                for A --> B, B --> C, and C --> A (if loop is True). If states
                is None, all states in the current instance will be used.
            trigger (string): The name of the trigger method that advances to
                the next state in the sequence.
            loop (boolean): Whether or not to add a transition from the last
                state to the first state.
            loop_includes_initial (boolean): If no initial state was defined in
                the machine, setting this to True will cause the _initial state
                placeholder to be included in the added transitions.
        """
        if states is None:
            states = list(self.states.keys())  # need to listify for Python3
        if len(states) < 2:
            raise MachineError("Can't create ordered transitions on a Machine "
                               "with fewer than 2 states.")
        for i in range(1, len(states)):
            self.add_transition(trigger, states[i - 1], states[i])
        if loop:
            if not loop_includes_initial:
                states.remove(self._initial)
            self.add_transition(trigger, states[-1], states[0])

    def callback(self, func, event_data):
        """ Trigger a callback function, possibly wrapping it in an EventData
        instance.
        Args:
            func (callable): The callback function.
            event_data (EventData): An EventData instance to pass to the
                callback (if event sending is enabled) or to extract arguments
                from (if event sending is disabled).
        """
        if self.send_event:
            func(event_data)
        else:
            func(*event_data.args, **event_data.kwargs)

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError
        terms = name.split('_')
        if terms[0] in ['before', 'after']:
            name = '_'.join(terms[1:])
            if name not in self.events:
                raise MachineError('Event "%s" is not registered.' % name)
            return partial(self.events[name].add_callback, terms[0])

        elif name.startswith('on_enter') or name.startswith('on_exit'):
            state = self.get_state('_'.join(terms[2:]))
            return partial(state.add_callback, terms[1])
        else:
            raise AttributeError


class MachineError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
