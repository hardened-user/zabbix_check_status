#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 29.09.2020
# ----------------------------------------------------------------------------------------------------------------------
import argparse
import configparser
import os
import re
import signal
import ssl
import sys
import tempfile

from slib3.fs import fs_rm_file
from slib3.kb import kb_confirm
from slib3.pid import pid_mk_file
from slib3.zabbix import *

# noinspection PyProtectedMember
ssl._create_default_https_context = ssl._create_unverified_context

_TRIGGER_EXCLUDE_ERRORS = (
    "no status update so far", "processes started", "agent is unavailable", "item is disabled",
    ": item is not supported.", ": not enough data.", ": cannot get values from value cache.")


def main():
    return_value = True
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = argparse.ArgumentParser(
            description='Zabbix Check Status - utility for check items/triggers status via Zabbix API')
        parser.add_argument("server", action='store', default=None, nargs='?',
                            metavar='<SERVER>', help="specified server from config")
        parser.add_argument("host", action='store', default=None, nargs='?',
                            metavar='<HOST>', help="specified host from zabbix")
        parser.add_argument('-i', '--interactive', action='store_true', default=False,
                            help="interactive mode")
        parser.add_argument('--colorama-disabled', action='store_true', default=False,
                            help="turn off color output")
        parser.add_argument('-v', '--verbose', action='count',
                            help="verbose mode")
        parser.add_argument('--test', action='store_true', default=False,
                            help="test mode")
        args = parser.parse_args()
    except SystemExit:
        return False
    # __________________________________________________________________________
    # verbose
    if args.verbose:
        log.setup(level=log.DEBUG1)
        if args.verbose > 1:
            log.setup(level=log.DEBUG2)
    # colorama disabled
    if args.colorama_disabled:
        log.setup(colorama_enabled=False)
    # __________________________________________________________________________
    # read configuration file
    try:
        self_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        config_ini = configparser.ConfigParser()
        config_ini.read(os.path.join(self_dir, 'config.ini'))
    except Exception as err:
        log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return False
    # __________________________________________________________________________
    if not [x for x in config_ini.sections() if x != 'default']:
        log.i("Nothing to do")
        return False
    # __________________________________________________________________________
    # create pid file
    if not pid_mk_file(pid_file_path):
        return False
    # __________________________________________________________________________
    # signal handlers
    signal.signal(signal.SIGINT, signal_handler_sigint)
    # ==================================================================================================================
    # ==================================================================================================================
    # Start of the work cycle
    # ==================================================================================================================
    # WARNING: В цикле не использовать return
    for job in [x for x in config_ini.sections() if x != 'default']:
        # Только выбранный сервер
        if args.server and job.lower() != args.server.lower():
            continue
        log.s("=" * 95)
        log.s("-=*=-{}-=*=-".format(job.rjust(42 + int(len(job) / 2)).ljust(85).upper()))
        log.s("-" * 95)
        config_job = {
            'zdx_host': None,
            'zdx_user': None,
            'zdx_pass': None,
            'exclude_item_ids': [],
            'exclude_item_re': None,
            'exclude_trigger_ids': [],
            'exclude_trigger_re': None,
            'include_host_groups': set(),
            'interactive': False,
        }
        # config default
        for x in config_job:
            try:
                if config_ini['default'][x]:
                    config_job[x] = config_ini['default'][x]
            except KeyError:
                pass
            except Exception as err:
                log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
                return_value = False
                continue
        # config job
        for x in config_job:
            try:
                if config_ini[job][x]:
                    config_job[x] = config_ini[job][x]
            except KeyError:
                pass
            except Exception as err:
                log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
                return_value = False
                continue
        # zdx_*
        if not isinstance(config_job['zdx_host'], str):
            log.e("Invalid value for parameter: zdx_host")
            continue
        if not isinstance(config_job['zdx_user'], str):
            log.e("Invalid value for parameter: zdx_user")
            continue
        if not isinstance(config_job['zdx_pass'], str):
            log.e("Invalid value for parameter: zdx_pass")
            continue
        # exclude_*_ids
        if isinstance(config_job['exclude_item_ids'], str):
            config_job['exclude_item_ids'] = filter(lambda x: x.isdigit(), config_job['exclude_item_ids'].split())
        if isinstance(config_job['exclude_trigger_ids'], str):
            config_job['exclude_trigger_ids'] = filter(lambda x: x.isdigit(), config_job['exclude_trigger_ids'].split())
        # exclude_*_re
        if isinstance(config_job['exclude_item_re'], str):
            try:
                config_job['exclude_item_re'] = re.compile(config_job['exclude_item_re'])
            except re.error:
                log.e("Invalid value for parameter: exclude_item_re")
                continue
        if isinstance(config_job['exclude_trigger_re'], str):
            try:
                config_job['exclude_trigger_re'] = re.compile(config_job['exclude_trigger_re'])
            except re.error:
                log.e("Invalid value for parameter: exclude_trigger_re")
                continue
        # include_host_groups
        if isinstance(config_job['include_host_groups'], str):
            config_job['include_host_groups'] = set(map(lambda x: x.lower(), config_job['include_host_groups'].split()))
        # interactive
        if args.interactive or \
                isinstance(config_job['interactive'], str) and \
                config_job['interactive'].lower() in ('true', 'yes', 'on'):
            config_job['interactive'] = True
        # ______________________________________________________________________
        zabbix_server = zabbix_connect(config_job['zdx_host'], config_job['zdx_user'], config_job['zdx_pass'])
        if not zabbix_server:
            return_value = False
            continue
        if args.test:
            log.i("Zabbix API connection successfully")
            continue
        # ______________________________________________________________________
        zabbix_hosts = zabbix_host_get(zabbix_server, extend_groups=True, status=0)
        # status:
        # 0 - (default) monitored host;
        if not zabbix_hosts:
            log.warning("No one host found")
            continue
        # ______________________________________________________________________
        for h in zabbix_hosts:
            # Только выбранный узел сети
            if args.host and h['name'].strip().lower() != args.host.lower():
                continue
            # Только выбранные группы хостов
            host_groups = set(map(lambda x: x['name'].lower(), h['groups']))
            if config_job['include_host_groups'] and not config_job['include_host_groups'] & host_groups:
                continue
            log.s("---->{}<----".format(h['name'].rjust(42 + int(len(h['name']) / 2)).ljust(85).upper()))
            # ##################################################################
            # Хост должен состоять в группе "_all"
            # if not filter(lambda x: x['name'].lower() == '_all', h['groups']):
            #    log.info("Host not a member of the group '_all'")
            #    main_return_value = False
            # ##################################################################
            # __________________________________________________________________
            # Проверка правил обнаружения
            log.d1("Checking discovery rules: ...")
            zabbix_lld_rules = zabbix_discoveryrule_get(zabbix_server, int(h['hostid']))
            log.d1("...   total: {}".format(len(zabbix_lld_rules)))
            for d in zabbix_lld_rules:
                lld_info_str = "itemid={} name='{}' key='{}' error='{}'".format(d['itemid'], d['name'].encode('utf-8'),
                                                                                d['key_'].encode('utf-8'),
                                                                                d['error'].encode('utf-8'))
                if int(d['status']) == 1:
                    # status:
                    # 0 - (default) enabled LLD rule;
                    # 1 - disabled LLD rule;
                    pass
                elif int(d['state']) == 0:
                    # state:
                    # 0 - (default) normal;
                    # 1 - not supported;
                    pass
                else:
                    log.i("Broken: {}".format(lld_info_str))
                    return_value = False
            # __________________________________________________________________
            # Проверка элементов данных
            log.d1("Checking items: ...")
            zabbix_items = zabbix_item_get(zabbix_server, int(h['hostid']))
            log.d1("...   total: {}".format(len(zabbix_items)))
            for i in zabbix_items:
                item_info_str = "itemid={} name='{}' key='{}' error='{}'".format(i['itemid'], i['name'].encode('utf-8'),
                                                                                 i['key_'].encode('utf-8'),
                                                                                 i['error'].encode('utf-8'))
                if int(i['status']) == 1:
                    # status:
                    # 0 - (default) enabled item;
                    # 1 - disabled item;
                    pass
                elif int(i['state']) == 0:
                    # state:
                    # 0 - (default) normal;
                    # 1 - not supported;
                    pass
                else:
                    # __________________________________________________________
                    # Исключение
                    if i['itemid'] in config_job['exclude_item_ids'] or \
                            (config_job['exclude_item_re'] and config_job['exclude_item_re'].search(i['key_'])):
                        log.d1("Skipped :{}".format(item_info_str))
                        continue
                    # __________________________________________________________
                    # Интерактивное отключение
                    elif config_job['interactive'] and kb_confirm("Disable item: {}".format(item_info_str)):
                        data = {"itemid": i['itemid'], "status": 1}
                        if zabbix_item_update(zabbix_server, data):
                            log.o("Item disabled")
                    # __________________________________________________________
                    # Печать
                    else:
                        log.i("Broken: {}".format(item_info_str))
                        return_value = False
            # __________________________________________________________________
            # https://www.zabbix.com/documentation/current/manual/api/reference/trigger/object
            log.d1("Checking triggers: ...")
            zabbix_triggers = zabbix_trigger_get(zabbix_server, int(h['hostid']))
            log.d1("...   total: {}".format(len(zabbix_triggers)))
            for t in zabbix_triggers:
                trigger_info_str = "triggerid: {}, description: '{}', error: '{}'".format(t['triggerid'],
                                                                                          t['description'],
                                                                                          t['error'])
                if int(t['status']) == 1:
                    # status:
                    # 0 - (default) enabled;
                    # 1 - disabled;
                    pass
                elif int(t['state']) == 0:
                    # state:
                    # 0 - (default) trigger state is up to date;
                    # 1 - current trigger state is unknown;
                    pass
                else:
                    # __________________________________________________________
                    # Исключение
                    if list(filter(lambda x: t['error'].lower().find(x) > -1, _TRIGGER_EXCLUDE_ERRORS)) or \
                            t['triggerid'] in config_job['exclude_trigger_ids'] or \
                            (config_job['exclude_trigger_re'] and config_job['exclude_trigger_re'].search(
                                t['description'])):
                        log.d1("Skipped: {}".format(trigger_info_str))
                    # __________________________________________________________
                    # Интерактивное отключение
                    elif config_job['interactive'] and kb_confirm("Disable trigger: {}".format(trigger_info_str)):
                        data = {"triggerid": t['triggerid'], "status": 1}
                        if zabbix_trigger_update(zabbix_server, data):
                            log.o("Trigger disabled")
                    # __________________________________________________________
                    # Печать
                    else:
                        log.i("Broken: {}".format(trigger_info_str))
                        return_value = False
    # ==================================================================================================================
    # ==================================================================================================================
    # Удаление PID файла
    if not fs_rm_file(pid_file_path):
        log.e("Failed to delete PID file: '{}'".format(pid_file_path))
        return_value = False
    # __________________________________________________________________________
    return return_value


# ======================================================================================================================
# Functions
# ======================================================================================================================


# ======================================================================================================================
# Signal Handlers
# ======================================================================================================================
def signal_handler_sigint(signum: int, frame):
    log.i("KeyboardInterrupt")
    fs_rm_file(pid_file_path)
    sys.exit(1)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    if os.name == 'nt':
        # noinspection PyUnresolvedReferences
        import msvcrt
        from ctypes import windll, wintypes

        os.system('mode con: cols=140 lines=40')
        chandle = windll.kernel32.GetStdHandle(-11)  # STDOUT
        # rect = wintypes.SMALL_RECT(0, 0, 100, 80) # (left, top, right, bottom)
        # noinspection PyProtectedMember
        bufsize = wintypes._COORD(140, 512)  # rows, columns
        # windll.kernel32.SetConsoleWindowInfo(chandle, True, byref(rect))
        windll.kernel32.SetConsoleScreenBufferSize(chandle, bufsize)

    # __________________________________________________________________________
    pid_file_path = os.path.join(tempfile.gettempdir(), os.path.basename(sys.argv[0]) + '.pid')
    rc = main()
    # __________________________________________________________________________
    if os.name == 'nt':
        log.i("Press any key to exit")
        msvcrt.getch()
    # __________________________________________________________________________
    sys.exit(not rc)  # Compatible return code
