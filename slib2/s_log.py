# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
import logging
import sys
try:
    import colorama
    colorama.init(autoreset=True)
    colorama_imported = True
except Exception:
    colorama_imported = False


logging.DEBUG2 = 9
logging.OK = 21
logging.SEP = 22
logging.QUERY = 61
logging.colored = True


#==================================================================================================
# Functions
#==================================================================================================
def debug2(self, message, *args, **kws):
    self.log(logging.DEBUG2, message, *args, **kws)
def ok(self, message, *args, **kws):
    self.log(logging.OK, message, *args, **kws)
def sep(self, message, *args, **kws):
    self.log(logging.SEP, message, *args, **kws)
def query(self, message, *args, **kws):
    self.log(logging.QUERY, message, *args, **kws)


def logging_setup(**kwargs):
    if 'filename' not in kwargs:
        kwargs['filename'] = None
    if 'level' not in kwargs:
        kwargs['level'] = logging.INFO
    if 'datefmt' not in kwargs:
        kwargs['datefmt'] = "%Y/%m/%d %H:%M:%S"
    if 'format' not in kwargs:
        kwargs['format'] = "[%(levelname)s] %(message)s"
        #kwargs['format'] = "%(module)-20s %(lineno)-3d %(funcName)-20s [%(levelname)s] %(message)s"
    #______________________________________________________
    logging.addLevelName(logging.DEBUG2,    '  ')
    logging.Logger.debug2 = debug2
    logging.addLevelName(logging.DEBUG,     '..')
    logging.addLevelName(logging.INFO,      '..')
    logging.addLevelName(logging.OK,        'OK')
    logging.Logger.ok = ok
    logging.addLevelName(logging.SEP,       '--')
    logging.Logger.sep = sep
    logging.addLevelName(logging.WARNING,   'WW')
    logging.addLevelName(logging.ERROR,     'EE')
    logging.addLevelName(logging.CRITICAL,  '!!')
    logging.addLevelName(logging.QUERY,     '??')
    logging.Logger.query = query
    #
    log.setLevel(kwargs['level'])
    #
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter(kwargs['format'], kwargs['datefmt']))
    log.addHandler(handler)
    #______________________________________________________
    return True


#==================================================================================================
# Classes
#==================================================================================================
class CustomFormatter(logging.Formatter):
    #def __init__(self, fmt=None, datefmt=None):
        #super(CustomFormatter, self).__init__()
    def format(self, record):
        if colorama_imported and logging.colored:
            #print dir(record)
            #print type(record.levelno), record.levelno, logging.ERROR
            #print record.getMessage()
            # debug
            if record.levelno == logging.DEBUG or record.levelno == logging.DEBUG2:
                record.levelname =colorama.Style.DIM +  colorama.Fore.WHITE + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Style.DIM + colorama.Fore.WHITE + record.msg + colorama.Style.RESET_ALL
            # info
            elif record.levelno == logging.INFO:
                record.levelname = colorama.Fore.WHITE + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.WHITE + record.msg + colorama.Style.RESET_ALL
            # ok
            elif record.levelno == logging.OK:
                record.levelname = colorama.Fore.GREEN + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.GREEN + record.msg + colorama.Style.RESET_ALL
            # separator
            elif record.levelno == logging.SEP:
                record.levelname = colorama.Style.BRIGHT + colorama.Fore.BLUE + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Style.BRIGHT + colorama.Fore.BLUE + record.msg + colorama.Style.RESET_ALL
            # warning
            elif record.levelno == logging.WARNING:
                record.levelname = colorama.Fore.YELLOW + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.YELLOW + record.msg + colorama.Style.RESET_ALL
            # error
            elif record.levelno == logging.ERROR:
                record.levelname = colorama.Fore.RED + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.RED + record.msg + colorama.Style.RESET_ALL
            # critical
            elif record.levelno == logging.CRITICAL:
                record.levelname = colorama.Style.BRIGHT + colorama.Fore.RED + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Style.BRIGHT + colorama.Fore.RED + record.msg + colorama.Style.RESET_ALL
            # query
            elif record.levelno == logging.QUERY:
                record.levelname = colorama.Fore.MAGENTA + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.MAGENTA + record.msg + colorama.Style.RESET_ALL
        #__________________________________________________
        return super(CustomFormatter, self).format(record)


#==================================================================================================
# Objects
#==================================================================================================
log = logging.getLogger()
