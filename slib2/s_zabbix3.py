# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
import os
import re
import sys
import datetime
from time import sleep
import logging
#
from slib2.zabbix3_api import ZabbixAPI, ZabbixAPIException


log = logging.getLogger()


#==================================================================================================
# JSON API | Base functions
#==================================================================================================
def zabbix_connect(host, user, password, attempts=1):
    cnt = 0
    while cnt < attempts:
        cnt += 1
        try:
            zabbix_server = ZabbixAPI(url=host, user=user, password=password)
            zabbix_server.login()
            return zabbix_server
        except ZabbixAPIException as err:
            log.error("ZabbixAPI Err: {}".format(err.message))
            continue
        except Exception as err:
            log.critical("Exception Err: {}".format(err))
            log.critical("Exception Inf: {}".format(sys.exc_info()))
            continue
    #______________________________________________________
    return None


def zabbix_query(zabbix_server, method, params, attempts=1):
    cnt = 0
    while cnt < attempts:
        cnt += 1
        try:
            log.debug2("ZabbixAPI Req:\n-{0}\n{1}\n-{0}".format("  -"*33, zabbix_server.json_obj(method, params)))
            result = zabbix_server.postRequest(zabbix_server.json_obj(method, params))
            log.debug2("ZabbixAPI Res:\n-{0}\n{1}\n-{0}".format("  -"*33, result))
            break
        except Exception as err:
            log.critical("Exception Err: {}".format(err))
            log.critical("Exception Inf: {}".format(sys.exc_info()))
            result = None
            continue
    #______________________________________________________
    if result is None:
        return None
    if "error" in result.keys():
        log.error("ZabbixAPI Err:\n-{0}\n{1}\n-{0}".format("  -"*33, result))
        return None
    if "result" in result.keys():
        return result['result']


#==================================================================================================
# JSON API | Get functions
#==================================================================================================
def zabbix_get_host(zabbix_server, name=None, selectGroups=False, attempts=1):
    params =  {'output': "extend", 'sortfield': "name"}
    if selectGroups:
        params['selectGroups'] = "extend"
    if name:
        params['filter'] = {'host': name}
    else:
        params['search'] = {'host': ""}
    #______________________________________________________
    return zabbix_query(zabbix_server, "host.get", params, attempts=attempts)


def zabbix_get_template(zabbix_server, name=None, selectDiscoveries=False, attempts=1, **kwargs):
    params = {'output': "extend", 'sortfield': "name", 'with_items':True, 'filter': {}}
    if isinstance(name, int):
        params['templateids'] = name
    else:
        params['filter'].update({'host': name})
    if selectDiscoveries:
        params['selectDiscoveries'] = "extend"
    params['filter'].update(kwargs)
    #______________________________________________________
    return zabbix_query(zabbix_server, "template.get", params, attempts=attempts)


def zabbix_get_discoveryrule(zabbix_server, host=None, selectItems=False, attempts=1, **kwargs):
    params = {'output': "extend", 'filter': {}}
    if isinstance(host, int):
        params['hostids'] = host
    else:
        params['host'] = host
    if selectItems:
        params['selectItems'] = "extend"
    params['filter'] = kwargs
    #______________________________________________________
    return zabbix_query(zabbix_server, "discoveryrule.get", params, attempts=attempts)


def zabbix_get_item(zabbix_server, host, attempts=1, **kwargs):
    params =  {'output': "extend"}
    if isinstance(host, int):
        params['hostids'] = host
    else:
        params['host'] = host
    params['filter'] = kwargs
    #______________________________________________________
    return zabbix_query(zabbix_server, "item.get", params, attempts=attempts)


def zabbix_get_trigger(zabbix_server, host, attempts=1, **kwargs):
    # 'selectDependencies': "extend"
    params = {'output': "extend", 'selectFunctions': "extend"}
    if isinstance(host, int):
        params['hostids'] = host
    else:
        params['host'] = host
    params['filter'] = kwargs
    #______________________________________________________
    return zabbix_query(zabbix_server, "trigger.get", params, attempts=attempts)


def zabbix_trigger_get_by_id(zabbix_server, triggerid):
    # Совпадение по id во всех узлах/шаблонах
    if isinstance(triggerid, int) or (isinstance(triggerid, str) and triggerid.isdigit()):
        result = zabbix_query(zabbix_server, "trigger.get", {'output': "extend", 'selectFunctions': "extend", 'triggerids': triggerid})
    if result:
        return result
    else:
        return list()


def zabbix_get_graph(zabbix_server, attempts=1, **kwargs):
    params =  {'output': "extend", 'sortfield': "name"}
    params['filter'] = kwargs
    #______________________________________________________
    return zabbix_query(zabbix_server, "graph.get", params, attempts=attempts)


def zabbix_get_screen(zabbix_server, attempts=1, **kwargs):
    params =  {'output': "extend", 'sortfield': "name"}
    params['filter'] = kwargs
    #______________________________________________________
    return zabbix_query(zabbix_server, "screen.get", params, attempts=attempts)


def zabbix_get_application(zabbix_server, attempts=1, **kwargs):
    params =  {'output': "extend", 'sortfield': "name"}
    params['filter'] = kwargs
    #______________________________________________________
    return zabbix_query(zabbix_server, "application.get", params, attempts=attempts)


def zabbix_get_hostinterface(zabbix_server, hostid, main=True):
    if main:
        # Интерфейс по умолчанию
        result = zabbix_query(zabbix_server, "hostinterface.get", {'output': "extend", 'hostids': hostid, 'filter': {'main': 1}})
    else:
        # Все интерфейсы
        result = zabbix_query(zabbix_server, "hostinterface.get", {'output': "extend", 'hostids': hostid})
    if result:
        return result
    else:
        return list()


def zabbix_get_history(zabbix_server, attempts=1, **kwargs):
    params =  {'output': "extend", 'sortfield': "clock"}
    params.update(kwargs)
    #______________________________________________________
    return zabbix_query(zabbix_server, "history.get", params, attempts=attempts)


#==================================================================================================
# JSON API | Create functions
#==================================================================================================
def zabbix_create_trigger(zabbix_server, trigger):
    result = zabbix_query(zabbix_server, "trigger.create", trigger)
    if result:
        return result
    else:
        return list()


def zabbix_trigger_adddependencies(zabbix_server, trigger, dependsOnTriggerid):
    result = zabbix_query(zabbix_server, "trigger.adddependencies", {'triggerid': trigger, 'dependsOnTriggerid': dependsOnTriggerid})
    if result:
        return result
    else:
        return list()


def zabbix_create_item(zabbix_server, item):
    result = zabbix_query(zabbix_server, "item.create", item)
    if result:
        return result
    else:
        return list()


def zabbix_create_application(zabbix_server, hostid, name):
    result = zabbix_query(zabbix_server, "application.create", {'hostid': hostid, 'name': name})
    if result:
        return result
    else:
        return list()


def zabbix_create_graph(zabbix_server, graph):
    result = zabbix_query(zabbix_server, "graph.create", graph)
    if result:
        return result
    else:
        return list()


def zabbix_create_screen(zabbix_server, screen):
    result = zabbix_query(zabbix_server, "screen.create", screen)
    if result:
        return result
    else:
        return list()


def zabbix_get_configuration(zabbix_server):
    result = zabbix_query(zabbix_server, "configuration.export", {'format': "xml", 'options': "groups"})
    if result:
        return result
    else:
        return list()


def zabbix_get_proxy(zabbix_server, proxy=None, attempts=1):
    params =  {'output': "extend", 'selectInterface': "extend"}
    if proxy and isinstance(proxy, int):
        params['proxyids'] = proxy
    elif proxy and (isinstance(proxy, str) or isinstance(proxy, unicode)):
        params['filter'] = {'host': proxy}
    #______________________________________________________
    return zabbix_query(zabbix_server, "proxy.get", params, attempts=attempts)


#==================================================================================================
# JSON API | Update functions
#==================================================================================================
def zabbix_update_item(zabbix_server, item):
    result = zabbix_query(zabbix_server, "item.update", item)
    if result:
        return result
    else:
        return list()


def zabbix_update_graph(zabbix_server, graph):
    result = zabbix_query(zabbix_server, "graph.update", graph)
    if result:
        return result
    else:
        return list()


def zabbix_update_screen(zabbix_server, screen):
    result = zabbix_query(zabbix_server, "screen.update", screen)
    if result:
        return result
    else:
        return list()


def zabbix_update_trigger(zabbix_server, trigger):
    result = zabbix_query(zabbix_server, "trigger.update", trigger)
    if result:
        return result
    else:
        return list()
