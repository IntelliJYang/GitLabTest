import argparse
import cmd
import os
import readline
import sys
import time
import traceback
from datetime import datetime
from functools import wraps
import zmq
import Configure.zmqports as zmqports
from publisher import ZmqPublisher
from rpc_client import RPCClientWrapper
from tinyrpc.protocols.jsonrpc import RPCError
from tinyrpc.protocols.jsonrpc import JSONRPCErrorResponse


class SequencerDebugger(object):
    def __init__(self, update_signal=None):
        super(SequencerDebugger, self).__init__()
        self.update_signal = update_signal

    sequencer = None
    break_points = []
    this_run = None
    stat = ''
    continuing = True

    def update_msg(self, message):
        print message
        if self.update_signal:
            self.update_signal.emit(message)

    def do_EOF(self, line):
        """Ctrl-D to quit sdb without stopping the sequencer server"""
        return True

    def do_load(self, sequence_db):
        """
        Usage: load [sequence_db_name]
        load a sequencer database. Default loads a randomly generated database
        """
        if not sequence_db:
            return 'you must specify a sequence database name'
        rep = self.sequencer.load(sequence_db)
        if hasattr(rep, 'result'):
            return rep.result
        elif hasattr(rep, 'error'):
            return rep.error
        else:
            return None

    def do_abort(self, line):
        """abort the current running sequence"""
        reply = self.sequencer.abort()
        if hasattr(reply, 'result'):
            return reply.result
        elif hasattr(reply, 'error'):
            return reply.error

    def do_run(self, line):
        """run the whole sequence without regard for any breakpoint"""
        return self.sequencer.run()

    def _show_sequence_item(self, item, pc):
        line_no = int(item[0])
        if line_no == pc + 1:
            sys.stdout.write('-> ')
        else:
            sys.stdout.write('   ')
        test = eval(item[1])
        sys.stdout.write(str(item[0]) + ': ')
        sys.stdout.write('%s  | %s | %s | %s' % (test['GROUP'], test['TID'], test['FUNCTION'], test['DESCRIPTION']))
        if 'PARAM1' in test:
            sys.stdout.write(' | ' + test['PARAM1'])
        sys.stdout.write(os.linesep)
        if 'PARAM2' in test:
            sys.stdout.write(' | ' + test['PARAM2'])
        sys.stdout.write(
            ' | %s | %s | %s | %s | %s ' %
            (test['UNIT'], test['LOW'], test['HIGH'], test['KEY'], test['VAL'])
        )
        sys.stdout.write(os.linesep)
        line = '%s  | %s | %s | %s' % (
            test['GROUP'], test['TID'], test['FUNCTION'], test['DESCRIPTION']) + ' | %s | %s | %s | %s | %s ' % (
                   test['UNIT'], test['LOW'], test['HIGH'], test['KEY'], test['VAL'])
        return line

    # 
    def do_list(self, lines):
        """list [lines] around the current sequence item"""
        if len(lines) == 0:
            lines = '10'
        try:
            reply = self.sequencer.list(lines)
            if isinstance(reply, JSONRPCErrorResponse):
                return False
            pc, start, stop = reply.result[0]
            listings = reply.result[1:]
            if len(listings) == 0:
                return False
            for item in listings:
                self._show_sequence_item(item, pc)
        except:
            pass
        return True

    # 
    def do_break(self, line):
        """set break point at [line]"""
        if line == '':
            line = '1'
        if int(line) not in self.break_points:
            self.break_points.append(int(line))
        if self.this_run is not None:
            self.this_run.append(int(line))

    def do_clear(self):
        self.break_points = []
        self.this_run = []

    def do_all(self):
        """show all the breakpoints"""
        points = str(self.break_points)
        ret = ' '.join(points)
        return points

    # 
    def do_next(self):
        """show the next line that will be executed"""
        return self.sequencer.s_next()

    def do_skip(self, line):
        """skip the right next test, equal to jump N+1"""
        reply = self.sequencer.skip()
        if reply:
            try:
                return self._show_sequence_item(reply.result, -100)
            except Exception as e:
                print 'skip failed'
                return 'skip fail'
        else:
            print 'skip failed'
            return 'skip fail'

    def do_abortcontinue(self):
        """run the whole sequence without regard for any breakpoint"""
        self.continuing = False

    def do_continue(self, lbl=None):
        """continue execution from the current position,
        if you run continue, breakpoints are honored.
        If you use run, breakpoints are not honored"""
        self.continuing = True
        reply = ' '
        if self.this_run is None:
            self.this_run = [b for b in self.break_points]

        while self.continuing and reply is not None:
            next_p = self.sequencer.s_next().result - 1
            if lbl:
                lbl.setText(str(next_p))
            ret = self.do_list('1')
            if not ret:
                break
            if next_p in self.this_run:
                sys.stdout.write('BREAK: ')
                self.this_run.remove(next_p)
                return
            reply = self.step_op(timeout=100000)
        # we reached the end of the run
        if len(self.this_run) == 0:
            self.this_run = None

    def do_jump(self, dest):
        """jump to the destination. Destination can be line number, group name or TID"""
        reply = self.sequencer.jump(dest)
        if hasattr(reply, 'result'):
            try:
                self._show_sequence_item(reply.result, -100)
            except Exception as e:
                print 'jump fail'
        elif hasattr(reply, 'error'):
            print reply.error

    def do_print(self, var_name):
        """show the value of [var_name]"""
        ret = self.sequencer.show(var_name)
        if hasattr(ret, 'result'):
            return ret.result
        elif hasattr(ret, 'error'):
            return ret.error
        else:
            return None

    def do_status(self, line):
        """return the current running status of the sequence"""
        self.stat = self.sequencer.status()
        return self.stat.result

    def do_s(self, line):
        """short name for step"""
        self.do_step()

    def step_op(self, timeout=3000):
        self.do_list('1')
        t1 = datetime.now()
        self.sequencer.client.transport.timeout = timeout
        reply = self.sequencer.step()
        if isinstance(reply, JSONRPCErrorResponse):
            self.update_msg(reply.error)
        if reply is None:
            self.update_msg('reached the end of sequence')
        else:
            t2 = datetime.now()
            self.update_msg('execution time: ' + str((t2 - t1).total_seconds()) + ' seconds')
        return reply

    def do_step(self):
        """execute the current line, move PC to the next line"""
        self.step_op()

    def do_wait(self, timeout):
        """wait [timeout] seconds for the test sequence to finish"""
        if timeout == '':
            timeout = '0'
        return self.sequencer.wait(timeout=int(timeout))

    def do_loop(self, count):
        """wait [timeout] seconds for the test sequence to finish"""
        if count == '':
            count = '1'
        count = int(count)
        for i in range(count):
            self.do_run(None)
            start = time.time()
            time.sleep(3)
            while True:
                self.do_status(None)
                self.update_msg(
                    'Loop {0} of {1} running, time elapsed={2}s'.format(i + 1, count, int(time.time() - start)))
                if self.stat.result == 'READY':
                    self.update_msg('loop {0} of {1} finished'.format(i + 1, count))
                    break
                time.sleep(5)

    def do_quit(self, line):
        """quit sdb and stop the sequencer server. If you just want to quit sdb without stopping
        the sequencer server you should use ctrl-D"""
        self.sequencer.__getattr__('::stop::')()
        return True

    def emptyline(self):
        pass

    def create_server(self, site):
        sequencer = RPCClientWrapper("tcp://127.0.0.1:" + str(zmqports.SEQUENCER_PORT + site), None).remote_server()
        self.sequencer = sequencer
        return self.sequencer
