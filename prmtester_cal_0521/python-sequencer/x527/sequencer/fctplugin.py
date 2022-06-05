import time

def runtime(params, unit, timeout, sequence):
    from datetime import datetime
    if len(unit) == 0:
        raise Exception('Unit is missing')
    if len(params[0]) == 0:
        raise Exception('Param1(group) is missing')
    for group in sequence.groups:
        if group.name == params[0]:
            start = group.start_time
            stop = group.stop_time
            if start is None or stop is None:
                return 0
            elif isinstance(start, datetime) and isinstance(stop, datetime):
                if start > stop:
                    raise Exception('time delta is minus')
                delta = stop - start
                if unit.lower() == 's':
                    return int(round(delta.total_seconds()))
                elif unit.lower() == 'ms':
                    return int(round(delta.total_seconds()*1000))
                elif unit.lower() == 'us':
                    return int(round(delta.total_seconds()*1000000))
                else:
                    raise Exception('Unit not recognized')
            else:
                raise Exception('start or stop time is not datetime instance')
    time.sleep(0.001)
    return 0


def comparesn(params, unit, timeout, sequence):
    mlbsn_scan = str(sequence.variables.get('scanned_sn', ''))
    mlbsn_diag = str(params[0]) if len(params) > 0 else ''
    if mlbsn_scan == mlbsn_diag:
        return mlbsn_scan
    else:
        return '--FAIL--'+'SCAN:'+mlbsn_scan+',DIAG:'+mlbsn_diag


def binlauncher(params, unit, timeout, sequence):
    import subprocess
    from threading import Timer
    cmd = [params[1], params[0]]
    child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    my_timer = Timer(int(timeout), child.kill)
    try:
        my_timer.start()
        stdout, stderr = child.communicate()
    finally:
        my_timer.cancel()
        return child.returncode

    
