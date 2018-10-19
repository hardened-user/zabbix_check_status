#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
import os
import re
import sys
import time
import datetime
from time import sleep
#
import argparse
import backports
import backports.configparser as configparser
import logging
import signal
import ssl
import tempfile
#
from slib2.s_log import *
from slib2.s_pid import *
from slib2.s_input import *
from slib2.s_zabbix3 import *
#
ssl._create_default_https_context = ssl._create_unverified_context


_TRIGGER_EXCLUDE_ERRORS = ("no status update so far", "processes started", "agent is unavailable", "item is disabled", ": item is not supported.")


def main():
    main_return_value = True
    signal.signal(signal.SIGINT, signal_handler_sigint)
    #______________________________________________________
    # Входящие аргументы
    try:
        parser = argparse.ArgumentParser(description='Zabbix Check Status - utility for check items/triggers status via Zabbix API')
        parser.add_argument("server", action='store', default=None, nargs='?', metavar='<SERVER>',
                            help="specified server")
        parser.add_argument("host", action='store', default=None, nargs='?', metavar='<HOST>',
                            help="specified host")
        parser.add_argument('-i', action='store_true', default=False, dest="interactive",
                            help="interactive mode")
        parser.add_argument('--no-color', action='store_true', default=False, dest="nocolor",
                            help="no color mode")
        parser.add_argument('--verbose', '-v', action='count', dest="verbose",
                            help="verbose mode")
        parser.add_argument('--test', action='store_true', default=False, dest="test",
                            help="test mode")
        args = parser.parse_args()
    except SystemExit:
        return False
    ### verbose
    if args.verbose:
        log.setLevel(logging.DEBUG)
        if args.verbose > 1:
            log.setLevel(logging.DEBUG2)
    ### nocolor
    if args.nocolor:
        logging.colored = False
    #______________________________________________________
    # Подключение config файла
    try:
        self_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        config_ini = configparser.ConfigParser()
        config_ini.read(os.path.join(self_dir, 'config.ini'))
    except Exception as err:
        log.critical("Exception Err: {}".format(err))
        log.critical("Exception Inf: {}".format(sys.exc_info()))
        return False
    if not config_ini.sections() or 'default' not in config_ini.sections():
        log.error("Configuration failed")
        return False
    if not [x for x in config_ini.sections() if x != 'default']:
        log.info("Nothing to do")
        return False
    #______________________________________________________
    # Создание PID файла
    if not mkpid(pid_file_path):
        log.error("Failed to create PID file: '{}'".format(pid_file_path))
        return False
    #==============================================================================================
    #==============================================================================================
    # Start of the work cycle
    #==============================================================================================
    # WARNING: В цикле не использовать return
    for job in [x for x in config_ini.sections() if x != 'default']:
        # Только выбранный сервер
        if args.server and job.lower() != args.server.lower():
            continue
        log.info("="*95)
        log.sep("-=*=-{}-=*=-".format(job.rjust(42+int(len(job)/2)).ljust(85).upper()))
        log.info("-"*95)
        config_job = {
                'zdx_host': None,
                'zdx_user': None,
                'zdx_pass': None,
                'exclude_item_ids': [],
                'exclude_item_re': None,
                'exclude_trigger_ids': [],
                'exclude_trigger_re': None,
                'interactive': False,
            }
        ### config default
        for x in config_job:
            try:
                if config_ini['default'][x]:
                    config_job[x] = config_ini['default'][x]
            except KeyError:
                pass
            except Exception as err:
                log.critical("Exception Err: {}".format(err))
                log.critical("Exception Inf: {}".format(sys.exc_info()))
                main_return_value = False
                continue
        ### config job
        for x in config_job:
            try:
                if config_ini[job][x]:
                    config_job[x] = config_ini[job][x]
            except KeyError:
                pass
            except Exception as err:
                log.critical("Exception Err: {}".format(err))
                log.critical("Exception Inf: {}".format(sys.exc_info()))
                main_return_value = False
                continue
        ### zdx_*
        if not isinstance(config_job['zdx_host'], (unicode, str)):
            log.error("Parameter wrong: 'zdx_host'")
            continue
        if not isinstance(config_job['zdx_user'], (unicode, str)):
            log.error("Parameter wrong: 'zdx_user'")
            continue
        if not isinstance(config_job['zdx_pass'], (unicode, str)):
            log.error("Parameter wrong: 'zdx_pass'")
            continue
        ### exclude_*_ids
        if isinstance(config_job['exclude_item_ids'], (unicode, str)):
            config_job['exclude_item_ids'] = filter(lambda x: x.isdigit(), config_job['exclude_item_ids'].split())
        if isinstance(config_job['exclude_trigger_ids'], (unicode, str)):
            config_job['exclude_trigger_ids'] = filter(lambda x: x.isdigit(), config_job['exclude_trigger_ids'].split())
        ### exclude_*_re
        if isinstance(config_job['exclude_item_re'], (unicode, str)):
            try:
                config_job['exclude_item_re'] = re.compile(config_job['exclude_item_re'])
            except re.error as err:
                log.error("Parameter wrong: 'exclude_item_re'")
                continue
        if isinstance(config_job['exclude_trigger_re'], (unicode, str)):
            try:
                config_job['exclude_trigger_re'] = re.compile(config_job['exclude_trigger_re'])
            except re.error as err:
                log.error("Parameter wrong: 'exclude_trigger_re'")
                continue
        ### interactive
        if args.interactive:
            config_job['interactive'] = True
        elif isinstance(config_job['interactive'], (unicode, str)) and config_job['interactive'].lower() not in ('true', 'yes', 'on'):
            config_job['interactive'] = False
        #__________________________________________________
        zabbix_server = zabbix_connect(config_job['zdx_host'], config_job['zdx_user'], config_job['zdx_pass'])
        if not zabbix_server:
            main_return_value = False
            continue
        if args.test:
            log.info("Zabbix API connection successfully")
            continue
        #__________________________________________________
        zabbix_hosts = zabbix_get_host(zabbix_server, selectGroups=True, status=0)
        # status:
        # 0 - (default) monitored host;
        if not zabbix_hosts:
            log.warning("No one host found")
            continue
        #__________________________________________________
        for h in zabbix_hosts:
            # Только выбранный узел сети
            if args.host and h['name'].strip().lower() != args.host.lower():
                continue
            log.sep("---->{}<----".format(h['name'].rjust(42+len(h['name'])/2).ljust(85).upper()))
            ###################################################################
            # Хост должен состоять в группе "_all"
            #if not filter(lambda x: x['name'].lower() == '_all', h['groups']):
            #    log.info("Host not a member of the group '_all'")
            #    main_return_value = False
            ###################################################################
            #______________________________________________
            # Проверка правил обнаружения
            log.debug("Checking LLD rules: ...")
            zabbix_lld_rules = zabbix_get_discoveryrule(zabbix_server, int(h['hostid']))
            if not zabbix_lld_rules:
                log.debug("No one LLD rule found")
            for lld in zabbix_lld_rules:
                lld_info_str = "ID={} Name='{}' Key='{}' Error='{}'".format(lld['itemid'], lld['name'].encode('utf-8'), lld['key_'].encode('utf-8'), lld['error'].encode('utf-8'))
                if int(lld['status']) == 1:
                    # status:
                    # 0 - (default) enabled LLD rule;
                    # 1 - disabled LLD rule;
                    pass
                elif int(lld['state']) == 0:
                    # state:
                    # 0 - (default) normal;
                    # 1 - not supported;
                    pass
                else:
                    log.info("LLD: {}".format(lld_info_str))
                    main_return_value = False
            #______________________________________________
            # Проверка элементов данных
            log.debug("Checking items: ...")
            zabbix_items = zabbix_get_item(zabbix_server, int(h['hostid']))
            if not zabbix_items:
                log.debug("No one item found")
            for i in zabbix_items:
                item_info_str = "ID={} Name='{}' Key='{}' Error='{}'".format(i['itemid'], i['name'].encode('utf-8'), i['key_'].encode('utf-8'), i['error'].encode('utf-8'))
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
                    #______________________________________
                    # Исключение
                    if i['itemid'] in config_job['exclude_item_ids'] or \
                        (config_job['exclude_item_re'] and config_job['exclude_item_re'].search(i['key_'])):
                        log.debug("Skipped item: {}".format(item_info_str))
                        continue
                    #______________________________________
                    # Интерактивное отключение
                    elif config_job['interactive']:
                        if input_confirm("Disable item: {}".format(item_info_str)):
                            if not zabbix_query(zabbix_server, "item.update", {"itemid": i['itemid'], "status" : 1}):
                                log.error("Item not disabled")
                            else:
                                log.ok("Item disabled")
                    #______________________________________
                    else:
                        log.info("Item: {}".format(item_info_str))
                        main_return_value = False
            #______________________________________________
            # Проверка триггеров
            log.debug("Checking triggers: ...")
            zabbix_triggers = zabbix_get_trigger(zabbix_server, int(h['hostid']))
            if not zabbix_triggers:
                log.debug("No one trigger found")
            for t in zabbix_triggers:
                trigger_info_str = "ID={} Description='{}' Error='{}'".format(t['triggerid'], t['description'].encode('utf-8'), t['error'].encode('utf-8'))
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
                    #______________________________________
                    # Исключение
                    if filter(lambda x: t['error'].lower().find(x) > -1, _TRIGGER_EXCLUDE_ERRORS) or \
                        t['triggerid'] in config_job['exclude_trigger_ids'] or \
                        (config_job['exclude_trigger_re'] and config_job['exclude_trigger_re'].search(t['description'])):
                        log.debug("Skipped trigger: {}".format(trigger_info_str))
                    #______________________________________
                    # Интерактивное отключение
                    elif config_job['interactive']:
                        if input_confirm("Disable trigger: {}".format(trigger_info_str)):
                            if not zabbix_query(zabbix_server, "trigger.update", {"triggerid": t['triggerid'], "status" : 1}):
                                log.error("Trigger not disabled")
                            else:
                                log.ok("Trigger disabled")
                    #______________________________________
                    else:
                        log.info("Trigger: {}".format(trigger_info_str))
                        main_return_value = False
    #==============================================================================================
    # Удаление PID файла
    if not rmfile(pid_file_path):
        log.error("Failed to delete PID file: '{}'".format(pid_file_path))
        main_return_value = False
    #______________________________________________________
    return main_return_value


#==================================================================================================
# Functions
#==================================================================================================



#==================================================================================================
# Signals Handlers
#==================================================================================================
def signal_handler_sigint(signal, frame):
    log.info("KeyboardInterrupt")
    rmfile(pid_file_path)
    sys.exit(1)


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    if os.name == 'nt':
        import msvcrt
        os.system('mode con: cols=140 lines=50')
    logging_setup()
    pid_file_path = os.path.join(tempfile.gettempdir(), os.path.basename(sys.argv[0]) + '.pid')
    rc = main()
    if os.name == 'nt':
        log.info("Press any key to exit")
        msvcrt.getch()
    sys.exit(not rc) # BASH compatible return code
