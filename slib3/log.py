# -*- coding: utf-8 -*-
# 26.08.2020
# ----------------------------------------------------------------------------------------------------------------------
import logging
import os
import sys

# noinspection PyBroadException
try:
    import colorama

    colorama.init(autoreset=True)
    _COLORAMA_INIT = True
except Exception:
    _COLORAMA_INIT = False

_DEBUG2 = logging.DEBUG - 1
_DEBUG1 = logging.DEBUG
_INFO = logging.INFO
_OK = logging.INFO + 1
_SEPARATOR = logging.INFO + 2
_WARNING = logging.WARNING
_ERROR = logging.ERROR
_CRITICAL = logging.CRITICAL
_REQUEST = logging.CRITICAL + 1


# ======================================================================================================================
# Classes
# ======================================================================================================================
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if _COLORAMA_INIT and log.colorama_enabled:
            # debug2
            if record.levelno == _DEBUG2:
                record.levelname = colorama.Style.DIM + colorama.Fore.WHITE + record.levelname + \
                                   colorama.Style.RESET_ALL
                record.msg = colorama.Style.DIM + colorama.Fore.WHITE + record.msg + colorama.Style.RESET_ALL
            # debug1
            elif record.levelno == _DEBUG1:
                record.levelname = colorama.Style.DIM + colorama.Fore.WHITE + record.levelname + \
                                   colorama.Style.RESET_ALL
                record.msg = colorama.Style.DIM + colorama.Fore.WHITE + record.msg + colorama.Style.RESET_ALL
            # info
            elif record.levelno == _INFO:
                record.levelname = colorama.Fore.LIGHTWHITE_EX + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.LIGHTWHITE_EX + record.msg + colorama.Style.RESET_ALL
            # ok
            elif record.levelno == _OK:
                record.levelname = colorama.Fore.GREEN + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.GREEN + record.msg + colorama.Style.RESET_ALL
            # separator
            elif record.levelno == _SEPARATOR:
                record.levelname = colorama.Fore.LIGHTBLUE_EX + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.LIGHTBLUE_EX + record.msg + colorama.Style.RESET_ALL
            # warning
            elif record.levelno == _WARNING:
                record.levelname = colorama.Fore.YELLOW + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.YELLOW + record.msg + colorama.Style.RESET_ALL
            # error
            elif record.levelno == _ERROR:
                record.levelname = colorama.Fore.RED + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.RED + record.msg + colorama.Style.RESET_ALL
            # critical
            elif record.levelno == _CRITICAL:
                record.levelname = colorama.Fore.LIGHTRED_EX + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.LIGHTRED_EX + record.msg + colorama.Style.RESET_ALL
            # request
            elif record.levelno == _REQUEST:
                record.levelname = colorama.Fore.MAGENTA + record.levelname + colorama.Style.RESET_ALL
                record.msg = colorama.Fore.MAGENTA + record.msg + colorama.Style.RESET_ALL
        # ______________________________________________________________________
        return super(CustomFormatter, self).format(record)


class CustomLogger(object):
    def __init__(self):
        self.colorama_enabled = True
        self.logger = logging.getLogger('slib3')
        # ______________________________________________________________________
        self.DEBUG2 = _DEBUG2
        self.DEBUG1 = _DEBUG1
        self.INFO = _INFO
        self.OK = _OK
        self.SEPARATOR = _SEPARATOR
        self.WARNING = _WARNING
        self.ERROR = _ERROR
        self.CRITICAL = _CRITICAL
        self.REQUEST = _REQUEST
        # ______________________________________________________________________
        logging.addLevelName(_DEBUG2, 'D2')
        logging.addLevelName(_DEBUG1, 'D1')
        logging.addLevelName(_INFO, '..')
        logging.addLevelName(_OK, 'OK')
        logging.addLevelName(_SEPARATOR, '--')
        logging.addLevelName(_WARNING, 'WW')
        logging.addLevelName(_ERROR, 'EE')
        logging.addLevelName(_CRITICAL, '!!')
        logging.addLevelName(_REQUEST, '??')
        # ______________________________________________________________________
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CustomFormatter())
        self.logger.addHandler(handler)
        # ______________________________________________________________________
        self.setup(level=self.get_env_level(), datetime_enabled=self.get_env_datetime())

    def setup(self, **kwargs) -> None:
        if 'level' in kwargs:
            self.logger.setLevel(kwargs['level'])
        if 'colorama_enabled' in kwargs:
            self.colorama_enabled = kwargs['colorama_enabled']
        if 'datetime_enabled' in kwargs:
            if kwargs['datetime_enabled']:
                self.logger.handlers[0].setFormatter(
                    CustomFormatter("%(asctime)s [%(levelname)s] %(message)s", "%Y.%m.%d %H:%M:%S"))
            else:
                self.logger.handlers[0].setFormatter(CustomFormatter("[%(levelname)s] %(message)s"))
        # ______________________________________________________________________
        return None

    @staticmethod
    def get_env_level() -> int:
        d = {
            'debug2': _DEBUG2,
            'debug1': _DEBUG1, 'debug': _DEBUG1,
            'information': _INFO, 'info': _INFO,
            'warning': _WARNING, 'warn': _WARNING,
            'error': _ERROR,
            'critical': _CRITICAL, 'crit': _CRITICAL
        }
        # ______________________________________________________________________
        return d.get(os.environ.get('LOG_LEVEL', "").lower(), _INFO)

    @staticmethod
    def get_env_datetime() -> bool:
        d = {
            'true': True, '1': True,
            'false': False, '0': False
        }
        # ______________________________________________________________________
        return d.get(os.environ.get('LOG_DATETIME', "").lower(), False)

    def d2(self, message, *args, **kwargs):
        self.logger.log(_DEBUG2, message, *args, **kwargs)

    def d1(self, message, *args, **kwargs):
        self.logger.log(_DEBUG1, message, *args, **kwargs)

    def i(self, message, *args, **kwargs):
        self.logger.log(_INFO, message, *args, **kwargs)

    def o(self, message, *args, **kwargs):
        self.logger.log(_OK, message, *args, **kwargs)

    def s(self, message, *args, **kwargs):
        self.logger.log(_SEPARATOR, message, *args, **kwargs)

    def w(self, message, *args, **kwargs):
        self.logger.log(_WARNING, message, *args, **kwargs)

    def e(self, message, *args, **kwargs):
        self.logger.log(_ERROR, message, *args, **kwargs)

    def c(self, message, *args, **kwargs):
        self.logger.log(_CRITICAL, message, *args, **kwargs)

    def r(self, message, *args, **kwargs):
        self.logger.log(_REQUEST, message, *args, **kwargs)


# ======================================================================================================================
# Objects
# ======================================================================================================================
log = CustomLogger()
