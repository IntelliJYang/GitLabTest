import os
import sys
import shutil
import time
import json
from datetime import datetime

def update_test_env():
    # update zmqports.json with current branch version
    path = os.path.dirname(__file__)
    src = os.path.join(path, 'x527_test/test_config/zmqports.json')
    dst = os.path.expanduser('~/testerconfig/zmqports.json')
    print 'copy file {0} to {1}'.format(src, dst)
    shutil.copy(src, dst)

    # refresh station_health_check.json timestamp to resolve InstantPudding commit error
    config = '/vault/data_collection/test_station_config/station_health_check.json'
    if not os.path.exists(config):
        sys.exit('file not exists')

    now = int(time.time())
    str_now = datetime.strftime(datetime.fromtimestamp(now), '%Y-%m-%d %H:%M:%S')

    # js = None
    with open(config, 'rU') as src:
        js = json.load(src, encoding='ascii')
        for key, val in js.iteritems():
            if val == 0 or val == 1:
                continue
            if type(val) is int:
                js[key] = now
            else:
                js[key] = str_now
    with open(config, 'w') as dst:
        dst.writelines(json.dumps(js, sort_keys=True, indent=4))
    print 'OK'

if __name__ == '__main__':

    update_test_env()