from x527.sequencer.sequencer import start_sequencer
from x527.engine.testengine import start_server
from x527.sequencer.sdb import create_sdb
from x527.sequencer.sdb import SequencerDebugger, handle_response
from x527.loggers.publisher import ZmqPublisher
from x527.loggers.reporter import ReporterProtocol
from x527.loggers.logger import LoggerServer
# from x527.loggers.logger import setup_loggers
from x527 import zmqports

import thread
import sys
import os
import zmq
import argparse
import types
import subprocess

curr_dir = os.getcwd()
git_server = curr_dir[:curr_dir.rfind("/")] + '/logserver/'
'''
if not os.path.exists(git_server):
    try:
        os.mkdir(git_server)
    except OSError as exc:
        print 'ERROR',exc
'''
curr_branch = 'test'

def git_cmd(op, params):
    if isinstance(params, list):
        cmd = ['git', op] + params
    else:
        cmd = ['git', op, params]
    p = subprocess.Popen(cmd)
    p.wait()

def do_switchbranch(self, branch):
    git_cmd('checkout', ['-b', branch])
    curr_branch = branch

def clone_repo(server):
    git_cmd('clone', [server, git_server])

def commit_log_files(log_dir):
    file_names = ['pivot.csv', 'flow_plain.txt', 'datalogger.csv', 'hw.txt', 'uart.txt', 'flow.txt', 'engine.txt', 'sequencer.log']
    log_files = os.listdir(log_dir)

    commit_msg = None

    os.chdir(log_dir)
    for _file in log_files:
        _file = _file[_file.rfind('/') + 1:]
        for name in file_names:
            if name in _file:
                if commit_msg == None:
                    commit_msg = _file[:_file.find(name)-1]
                    sn = commit_msg[:commit_msg.find('_')]
                    if len(sn) == 4:
                        sn = ''
                        folder = git_server + commit_msg[:commit_msg.rfind('_')] + '/'
                    else:
                        folder = git_server + commit_msg[commit_msg.find('_')+1:commit_msg.rfind('_')] + '/'
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                os.rename(_file, folder + sn + name)
                break


    os.chdir(folder)
    git_cmd('checkout', ['-b', curr_branch])
    for _file in file_names:
        git_cmd('add', sn + _file)

    git_cmd('commit', ["-am", commit_msg])

    git_cmd('push', ['-u', 'origin', curr_branch])

    os.chdir(curr_dir)

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Unsupported value encountered.')
    
def sdb_add_command(name, cmd):
    setattr(SequencerDebugger, name, types.MethodType(cmd, SequencerDebugger))

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='Sequencer URL', default="127.0.0.1")
    parser.add_argument('-s', '--site', help='the site of the sequencer to connect to', type=int, default=0)
    parser.add_argument('-c', '--site_count', type=int, default=4)
    parser.add_argument('-t', '--testplan', help='the test plan to load', default=None)
    parser.add_argument('-e', '--testengine', help='By default launches the dummy testengine else start the engine manually', type=str2bool, default=True)
    # parser.add_argument('loggers',
    #                     help='List of the loggers your want to enable, p=pudding, v=pivot, c=csv, f=flow, s=flow_plain,'
    #                          ' d=datalogger, a=ARM, u=UART, e=Engine'
    #                     , nargs='?', default='vcfsdaupe', const=''
    #                     )
    parser.add_argument('-d', '--directory', help='the log directory, default to "logs"', default='logs')
    parser.add_argument('-g', '--gitserver', help='git server address', default='https://hwtegit.apple.com/misfits/fct-ci.git')
    parser.add_argument('-p', '--disable_pudding', help='disable pudding logger and override config.json setting',
                        action='store_true', default=False)
    args = parser.parse_args()

    if not os.path.exists(git_server):
        clone_repo(args.gitserver)

    if not os.path.exists(args.directory):
        os.mkdir(args.directory)

    def do_commit(self, line):
        commit_log_files(args.directory)
    sdb_add_command('do_commit', do_commit)
    sdb_add_command('do_switchbranch', do_switchbranch)

    def start_logger():
        ctx = zmq.Context()
        publisher = ZmqPublisher(ctx, "tcp://*:" + str(zmqports.LOGGER_PUB), 'logger')

        logger_server = LoggerServer(publisher)
        if not logger_server.load_config(args.disable_pudding):
            print "Fail to initialize loggers"
            exit()

        logger_server.start()


    thread.start_new_thread(start_sequencer, (args.site, sys.maxint, False))
    thread.start_new_thread(start_logger, ())
    if args.testengine is True:
        print "True"
        thread.start_new_thread(start_server, (args.site, False))

    sdb = create_sdb(args.url, args.site)
    if args.testplan:
        sdb.do_load(args.testplan)
    sdb.cmdloop()
