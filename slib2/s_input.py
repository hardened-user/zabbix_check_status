# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
import sys
import logging


log = logging.getLogger()


#==================================================================================================
# Functions
#==================================================================================================
def input_confirm(msg):
    log.query(msg)
    sys.stdout.flush()
    if raw_input('$:').lower() not in ('y', 'yes'):
        return False
    else:
        return True
