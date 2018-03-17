#!/usr/bin/env python
#-*-coding:utf-8 -*-
#
#Author: tony - birdaccp at gmail.com
#Create by:2014-09-19 15:28:46
#Last modified:2017-05-23 11:13:20
#Filename:urls.py
#Description:

import os
from tornado.log import app_log

from core import context
module = context['module'].split(",")
# module = [m.capitalize() for m in module]
# module = [m.lower() for m in module]

# import pdb; pdb.set_trace()

handlers = [
    #(r"/(?P<filename>.*\.txt)", StaticHandler),
    #(r".*", PageNotFoundHandler),
]

# app_log.info(module)
# 检查输入的模块是否存在
# filepath = os.path.join(os.path.abspath(os.path.curdir), 'handlers')
# module = filter(lambda x : os.path.exists(os.path.join(filepath, x)), module)
# app_log.info(module)

if module:
    from handlers import Route
    __import__("handlers", fromlist=module)
    handlers.extend(Route.urls)
else:
    app_log.error('not found module')
    exit(0)
