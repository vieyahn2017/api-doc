#!/usr/bin/env python
# -*-coding:utf-8 -*-
# @author:yanghao
# @created:
## Description:

from __future__ import absolute_import
from tornado.gen import coroutine
from handlers import BaseProxyHandler, Route
from config import BASE_URL
import json


@Route("m")
class ApiSaveHandler(BaseProxyHandler):
    def get(self):
        base_url = BASE_URL

        api = [
            'm/api/type',
            'm/api/param',
            'm/api/record',
            'm/api',
            'm/api/exist',
        ]

        test = [
            'm/api/save',
            'm/api/test',
        ]

        route = {
            "update_time": "2018-03-17",
            "test": [base_url + "/api/v1/" + url for url in test],
            "api": [base_url + "/api/v1/" + url for url in api]
        }

        self.write(route)


@Route("m/api/save")
class ApiSaveHandler(BaseProxyHandler):
    @coroutine
    def post(self):
        body = json.loads(self.request.body)
        print body


@Route("m/api/test")
class ApiTestHandler(BaseProxyHandler):
    @coroutine
    def get(self):
        self.write_rows()
