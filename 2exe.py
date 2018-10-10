# -*- coding: utf-8 -*-
import sys
import py2exe
from distutils.core import setup


options = {
    'py2exe': {
        'unbuffered': True,
        'compressed': True,
        'bundle_files' : 1,
        'optimize': 2,
    }
}

console = [
    {
        'script': "zabbix_check_status.py",
        'icon_resources': [(1, "img/zabbix.ico")],
    }
]

data_files = [
    "config.ini"
]

setup(
    version = "1.0",
    name = "Zabbix Check Status",
    description = "Utility for check items/triggers status via Zabbix API",
    console = console,
    options = options,
    zipfile = None,
    data_files = data_files,
)
