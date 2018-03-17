#!/usr/bin/env python
#-*-coding:utf-8 -*-
#
#Author: tony - birdaccp at gmail.com
#Create by:2015-08-11 15:50:21
#Last modified:2017-05-11 16:16:49
#Filename:server.py
#Description:
from __future__ import absolute_import
import sys

from tornado.log import app_log
from tornado.options import define
from core import Application, context
from config import settings
from config import DEFAULT_MODULE, DEFAULT_PORT

def shutdown_handler():
    pass

def log_function(handler):
    if "debug" in settings and settings["debug"]:
        request_time = 1000.0 * handler.request.request_time()
        if handler.request.method != "OPTIONS":
            app_log.info("%d %s %.2fms", handler.get_status(), handler._request_summary(), request_time)

def set_service_status():
    from constant import CACHE_SERVER_UP, DATABASE_SERVER_UP
    from core import SystemStatus
    SystemStatus.set_cache_server_status(CACHE_SERVER_UP)
    SystemStatus.set_database_server_status(DATABASE_SERVER_UP)

def before_start(app):
    app.reg_shutdown_hook(shutdown_handler)
    set_service_status()
    app.settings["log_function"] = log_function
    from concurrent.futures.thread import ThreadPoolExecutor
    works = app.settings["executor_number"]
    app.settings["executor"] = ThreadPoolExecutor(max_workers=works)
    context["executor"] = app.settings["executor"]

def main():
    define("address", default='0.0.0.0', help="run server as address")
    define("port", default=DEFAULT_PORT, help="run server as port", type=int)
    define("debug", default=False, help="run as a debug model", type=bool)
    define("module", default=DEFAULT_MODULE, help="load specifical modules")
    Application().before(before_start).start()

main()
