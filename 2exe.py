# -*- coding: utf-8 -*-
from cx_Freeze import setup, Executable

options = {
    'build_exe': {
        'include_files': ['config.ini'],
        "optimize": 2
    }
}

executables = [
    Executable(
        script="zabbix_check_status.py",
        base="Console",
        icon="img/zabbix.ico",
    )
]

setup(
    name="Zabbix Check Status",
    version="3.0",
    description="Utility for check items/triggers status via Zabbix API",
    options=options,
    executables=executables
)
