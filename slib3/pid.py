# -*- coding: utf-8 -*-
# 11.08.2020
# ----------------------------------------------------------------------------------------------------------------------
import os
import traceback

from .log import log
from .ps import ps_check_pid


# ======================================================================================================================
# Functions
# ======================================================================================================================
def pid_mk_file(path):
    """
    Create pid file.
    """
    if os.path.exists(path):
        try:
            f = open(path, 'r')
            pid = f.readline().strip()
            f.close()
        except Exception as err:
            log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
            return False
        if pid.isdigit():
            if ps_check_pid(int(pid)):
                log.e("Pid file already exist. Process already running :: pid: {}".format(pid))
                return False
            else:
                log.w("Pid file already exist. Process does not exist :: pid: {} ".format(pid))
        else:
            log.e("Pid file already exist. Content incorrect. Remove pid file manually and check running processes")
            return False
    # __________________________________________________________________________
    try:
        f = open(path, 'w')
        f.write('{}\n'.format(os.getpid()))
        f.close()
        log.d2("Pid file created :: {}".format(path))
    except Exception as err:
        log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return False
    # __________________________________________________________________________
    return True
