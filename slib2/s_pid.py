# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
import os
import sys
import re
import datetime
from time import sleep
import logging


log = logging.getLogger()


#==================================================================================================
# Functions
#==================================================================================================
def mkpid(path):
    #______________________________________________________
    if os.path.exists(path):
        try:
            f = open(path, 'r')
            pid = f.readline().strip()
            f.close()
        except Exception as err:
            log.critical("Exception Err: {}".format(err))
            log.critical("Exception Inf: {}".format(sys.exc_info()))
            return False
        if pid.isdigit():
            #______________________________________________
            # Проверка состояния процесса по PID'у
            try:
                os.kill(int(pid), 0)
            except OSError:
                log.warning("Pid file alredy exist, but process with PID:{} does not exist".format(pid))
            else:
                log.error("Pid file alredy exist, but process with PID:{} is launched".format(pid))
                return False
        else:
            #______________________________________________
            # Ошибка содержимого файла
            log.error("Pid file alredy exist, but PID incorrect. Remove file manually: '{}'".format(path))
            return False
    #______________________________________________________
    try:
        f = open(path, 'w')
        f.write('{}\n'.format(os.getpid()))
        f.close()
    except Exception as err:
        log.critical("Exception Err: {}".format(err))
        log.critical("Exception Inf: {}".format(sys.exc_info()))
        return False
    #______________________________________________________
    return True


def rmfile(path):
    try:
        os.remove(path)
    except Exception as err:
        log.critical("Exception Err: {}".format(err))
        log.critical("Exception Inf: {}".format(sys.exc_info()))
        return False
    #______________________________________________________
    return True
