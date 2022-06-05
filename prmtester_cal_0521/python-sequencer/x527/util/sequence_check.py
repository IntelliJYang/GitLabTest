import argparse
from x527.sequencer.sequence import TestSequence, TestItem
import csv
import os

allowed_keys = ['GROUP', 'TID', 'DESCRIPTION', 'FUNCTION', 'TIMEOUT',
                'PARAM1', 'PARAM2', 'UNIT', 'LOW', 'HIGH', 'KEY', 'VAL',
                'VALIDATE','FAIL_COUNT']

supply_table = []  #net name from HWIO.SupplyTable
relay_table = [] #net name from HWIO.RelayTable
te_functions = ['parse', 'diags', 'detect', 'calculate',
                'datalogger', 'thdn', 'dmm', 'supply',
                'eload', 'iload', 'delay', 'measure', 'relay',
                'disconnect', 'button', 'tbat',
                'reset', 'station', 'fixturetype', 'channel',
                'getboottime', 'getbootcount', 'fatalerror', 'smokey',
                'frequency', 'amplitude', 'get_version', 'getsn', 'comparesn'
                ]

class SequenceError(Exception): pass
class SequenceWarning(Exception): pass

def check_relay_net(net_name):
    #todo: check relay net
    return

def check_supply_net(net_name):
    #todo: check supply net
    return

def check_csv_sequence(csv_file):
    reader = None
    errors = []
    warnings = []


    ts = TestSequence()
    ts.parse_file_name(csv_file)
    f = open(csv_file, 'rU')
    reader = csv.DictReader(f)

    variables = {}
    tid_dict = {}
    relay_states = {}
    i = 2
    for row in reader:
        try:
            for key in row.keys():
                if key not in allowed_keys:
                    raise SequenceError('!!!!!ERROR!!!!!!Key:'+str(key)+' is not allowed')
            test = TestItem(row)
            if len(test.tid.strip()) == 0:
                raise SequenceError('!!!!!ERROR!!!!!!on line ' + str(i) + ', TID is empty')
            if len(test.group.strip()) == 0:
                raise SequenceError('!!!!!ERROR!!!!!!on line ' + str(i) + ', GROUP is empty')
            if len(test.function.strip()) == 0:
                raise SequenceError('!!!!!ERROR!!!!!!on line ' + str(i) + ', FUNCTION is empty')
            filter = ''; filter_value = ''
            if test.filters is not None:
                filter = test.filters.keys()[0]
                filter_value = test.filters[filter]
            if test.group+test.tid in tid_dict.keys():
                tid_d = tid_dict[test.group+test.tid]
                if (filter, filter_value) in tid_d.keys():
                    previous_line = tid_d[(filter, filter_value)]
                    raise SequenceError("!!!!!ERROR!!!!!!on line " + str(i) + ', tid "' +str(test.group)+'_'+str(test.tid) + '" is repeated; KEY=' + filter + ', VAL=' + filter_value + '. Previously this tid appeared on line ' + str(previous_line))
                else:
                    tid_d[(filter, filter_value)] = i
            else:
                tid_dict[test.group+test.tid]={(filter, filter_value):i}
            if test.returned_val:
                variables[test.returned_val] = None
            if test.p_attribute:
                variables[test.p_attribute] = None
            if len(test.kwargs)>0:
                for variable_name in test.kwargs.keys():
                    if variable_name not in variables:
                        raise SequenceError('!!!!!ERROR!!!!!!on line ' + str(i) + ', in test ' + test.tid + ' variable "' + variable_name + '" used before initialized')
            if test.call_engine:
                if test.function not in te_functions:
                    raise SequenceError('!!!!!ERROR!!!!!!on line ' + str(i) + ',in test ' + test.tid +': unsupported test engnine funtion ' + test.function)
            if test.function=='relay':
                if not test.row.has_key('PARAM1'):
                    raise SequenceError('!!!!!!ERROR!!!!!!on line ' + str(i) + ',in test ' + test.tid +': no net is specified for the relay function')
                net_name = test.row['PARAM1']
                if relay_states.has_key(net_name):
                    previous_line = relay_states[net_name]
                    raise SequenceWarning('========WARNGING==========on line ' + str(i) + ',in test ' + test.tid +': relay ' + net_name + ' is connected again without being disconnected first. Last time it was connected on line ' + str(previous_line))
                check_relay_net(net_name)
                relay_states[net_name] = i
            if test.function=='disconnect':
                if not test.row.has_key('PARAM1'):
                    raise SequenceError('!!!!!!ERROR!!!!!!on line ' + str(i) + ',in test ' + test.tid +': no net is specified for the disconnect function')
                net_name = test.row['PARAM1']
                if not relay_states.has_key(net_name):
                    raise SequenceWarning('========WARNING========on line ' + str(i) + ',in test ' + test.tid +': disconnect relay ' + net_name + " before it's connected")
                relay_states.pop(net_name)
            if test.function=='supply':
                if not test.row.has_key('PARAM1'):
                    raise SequenceError('!!!!!!ERROR!!!!!!on line ' + str(i) + ',in test ' + test.tid +': no net is specified for the supply function')
                check_supply_net(net_name)
        except SequenceError as e:
            errors.append(e)
        except SequenceWarning as e:
            warnings.append(e)
        except Exception as e:
            e.message = '!!!!!ERROR!!!!!!line-'+str(i)+': Could not load this row('+e.message+')'
            errors.append(e)
        i+=1
    if len(relay_states)>0:
        for net_name, line in relay_states.iteritems():
            errors.append(SequenceError('!!!!!!ERROR!!!!!!on line ' + str(line) + ', relay ' + net_name + ' is connected but never disconnected'))
    f.close()
    return errors, warnings


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sequence_file', help='the file with the sequnce')
    parser.add_argument("-v", "--verbosity", action="count", help="increase output verbosity with more occurences of v")
    args = parser.parse_args()

    exec_path = os.path.dirname(os.path.dirname(os.path.abspath(os.path.split(__file__)[0])))
    os.environ['PYHTONPATH'] = exec_path
    try:
        errors, warnings = check_csv_sequence(args.sequence_file)
        error_count = len(errors)
        warning_count = len(warnings)
        print '\n\t' + str(error_count)  + ' errors, ' + str(warning_count) + ' warnings found.'
        if args.verbosity is None and (error_count + warning_count)>0:
            print 'use the -v option to show error informaton, and -vv to show warning information as well'
        if args.verbosity>=1:
            for e in errors:
                print e.message
        if args.verbosity>=2:
            for e in warnings:
                print e.message
    except Exception as e:
        print e.message

