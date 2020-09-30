# -*- coding: utf-8 -*-
# 29.09.2020
# ----------------------------------------------------------------------------------------------------------------------
import traceback

from .log import log
from .zapi import ZabbixAPI, ZabbixAPIException


# ======================================================================================================================
# JSON API | Base functions
# ======================================================================================================================
def zabbix_connect(host, user, password, attempts=1) -> ZabbixAPI or None:
    cnt = 0
    while cnt < attempts:
        cnt += 1
        try:
            zabbix_server = ZabbixAPI(url=host, user=user, password=password)
            zabbix_server.login()
            return zabbix_server
        except ZabbixAPIException as err:
            log.e("ZabbixAPI Exception: {}".format(err.args[0]))
            continue
        except Exception as err:
            log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
            continue
    # __________________________________________________________________________
    return None


def zabbix_query(zabbix_server, method, params, attempts=1):
    response = None
    cnt = 0
    while cnt < attempts:
        cnt += 1
        try:
            log.d2("ZabbixAPI Req:\n-{0}\n{1}\n-{0}".format("  -" * 33, zabbix_server.json_obj(method, params)))
            response = zabbix_server.post_request(zabbix_server.json_obj(method, params))
            log.d2("ZabbixAPI Res:\n-{0}\n{1}\n-{0}".format("  -" * 33, response))
            break
        except Exception as err:
            log.c("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
            continue
    # __________________________________________________________________________
    if isinstance(response, dict):
        if "error" in response:
            log.e("ZabbixAPI Err:\n-{0}\n{1}\n-{0}".format("  -" * 33, response))
        elif "result" in response:
            return response['result']
    # __________________________________________________________________________
    return None


# ======================================================================================================================
# JSON API | Class "host"
# ======================================================================================================================
def zabbix_host_get(zabbix_server, name=None, extend_groups=False, attempts=1, **kwargs):
    params = {'output': "extend", 'sortfield': "name", 'filter': dict()}
    if name:
        params['filter'].update({'host': name})
    else:
        params['search'] = {'host': ""}
    if extend_groups:
        params['selectGroups'] = "extend"
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "host.get", params, attempts=attempts)


# ======================================================================================================================
# JSON API | Class "item"
# ======================================================================================================================
def zabbix_item_get(zabbix_server, host, attempts=1, **kwargs):
    params = {'output': "extend", 'filter': dict()}
    if isinstance(host, int):
        params['hostids'] = host
    else:
        params['host'] = host
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "item.get", params, attempts=attempts)


def zabbix_item_create(zabbix_server, data):
    return zabbix_query(zabbix_server, "item.create", data)


def zabbix_item_update(zabbix_server, data):
    return zabbix_query(zabbix_server, "item.update", data)


# ======================================================================================================================
# JSON API | Class "trigger"
# ======================================================================================================================
def zabbix_trigger_get(zabbix_server, host, attempts=1, **kwargs):
    # 'selectDependencies': "extend"
    params = {'output': "extend", 'selectFunctions': "extend", 'filter': dict()}
    if isinstance(host, int):
        params['hostids'] = host
    else:
        params['host'] = host
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "trigger.get", params, attempts=attempts)


def zabbix_trigger_create(zabbix_server, data):
    return zabbix_query(zabbix_server, "trigger.create", data)


def zabbix_trigger_update(zabbix_server, data):
    return zabbix_query(zabbix_server, "trigger.update", data)


def zabbix_trigger_adddependencies(zabbix_server, trigger, depends_on_trigger_id):
    return zabbix_query(zabbix_server, "trigger.adddependencies",
                        {'triggerid': trigger, 'dependsOnTriggerid': depends_on_trigger_id})


# def zabbix_trigger_get_by_id(zabbix_server, triggerid):
#    # Совпадение по id во всех узлах/шаблонах
#    if isinstance(triggerid, int) or (isinstance(triggerid, str) and triggerid.isdigit()):
#        result = zabbix_query(zabbix_server, "trigger.get",
#                              {'output': "extend", 'selectFunctions': "extend", 'triggerids': triggerid})
#    if result:
#        return result
#   else:
#        return list()


# ======================================================================================================================
# JSON API | Class "template"
# ======================================================================================================================
def zabbix_template_get(zabbix_server, name=None, extend_items=False, extend_discoveries=False, attempts=1, **kwargs):
    params = {'output': "extend", 'sortfield': "name", 'with_items': True, 'filter': dict()}
    if isinstance(name, int):
        params['templateids'] = name
    else:
        params['filter'].update({'host': name})
    if extend_items:
        params['with_items'] = True
    if extend_discoveries:
        params['selectDiscoveries'] = "extend"
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "template.get", params, attempts=attempts)


# ======================================================================================================================
# JSON API | Class "discoveryrule"
# ======================================================================================================================
def zabbix_discoveryrule_get(zabbix_server, host=None, extend_items=False, attempts=1, **kwargs):
    params = {'output': "extend", 'filter': dict()}
    if isinstance(host, int):
        params['hostids'] = host
    else:
        params['host'] = host
    if extend_items:
        params['selectItems'] = "extend"
    params['filter'] = kwargs
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "discoveryrule.get", params, attempts=attempts)


# ======================================================================================================================
# JSON API | Class "graph"
# ======================================================================================================================
def zabbix_graph_get(zabbix_server, attempts=1, **kwargs):
    params = {'output': "extend", 'sortfield': "name", 'filter': dict()}
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "graph.get", params, attempts=attempts)


def zabbix_graph_create(zabbix_server, data):
    return zabbix_query(zabbix_server, "graph.create", data)


def zabbix_graph_update(zabbix_server, data):
    return zabbix_query(zabbix_server, "graph.update", data)


# ======================================================================================================================
# JSON API | Class "screen"
# ======================================================================================================================
def zabbix_screen_get(zabbix_server, attempts=1, **kwargs):
    params = {'output': "extend", 'sortfield': "name", 'filter': dict()}
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "screen.get", params, attempts=attempts)


def zabbix_screen_create(zabbix_server, data):
    return zabbix_query(zabbix_server, "screen.create", data)


def zabbix_screen_update(zabbix_server, data):
    return zabbix_query(zabbix_server, "screen.update", data)


# ======================================================================================================================
# JSON API | Class "application"
# ======================================================================================================================
def zabbix_application_get(zabbix_server, attempts=1, **kwargs):
    params = {'output': "extend", 'sortfield': "name", 'filter': dict()}
    # custom filter
    params['filter'].update(kwargs)
    # __________________________________________________________________________
    return zabbix_query(zabbix_server, "application.get", params, attempts=attempts)


def zabbix_application_create(zabbix_server, hostid, name):
    return zabbix_query(zabbix_server, "application.create", {'hostid': hostid, 'name': name})
