import os
import traceback
from functools import wraps

MISSING_ENOUGH_PARA = "--FAIL--MISSING_ENOUGH_PARA"
PARA_ERROR = "--FAIL--PARA_ERROR"


def handle_response(afunc):
    @wraps(afunc)
    def _(*args, **kwargs):
        try:
            reply = afunc(*args, **kwargs)
            if reply is not None:
                if reply is True:
                    return "--PASS--"
                elif reply is False:
                    return "--FAIL--"
                elif reply == "done":
                    return "--PASS--"
                else:
                    return reply
            else:
                return "--FAIL--"
        except Exception as e:
            print e.message, os.linesep, traceback.format_exc()
            return "--FAIL--{}".format(e)
    return _



