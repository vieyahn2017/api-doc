#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao
# @created:20170426
## Description: http_fetch

import json
import traceback

from tornado.gen import coroutine, Return
from tornado.log import app_log
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado import escape

class Fetcher(object):
    def __init__(self, host):
        self.host = host

    @coroutine
    def _fetch(self, url, method='get', body=None, is_log=True):
        fetch_url = "%s/%s" % (self.host, url)
        request = HTTPRequest(url=fetch_url, method=method.upper(), body=body)
        if is_log:
            app_log.info("fetch_%s at: %s" % (method, fetch_url))
        try:
            response = yield AsyncHTTPClient().fetch(request)
            response_body = escape.json_decode(response.body)
            code = response_body.get('code')
            rows = response_body.get('rows')
            if is_log:
                app_log.info(("receive_rows:" , rows, type(rows), "code: ", code, "msg: ", response_body.get("msg")))
            # app_log.debug("receive_rows:%s %s" % (rows, type(rows)))
            results = {
                "rows": rows,
                "msg": response_body.get("msg"),
                "code": code,
                "url": response.request.url
            }
        except HTTPError as e:
            app_log.error('{0}: {1}  Msg: {2}'.format(method.upper(), fetch_url, e))
            raise Return({"url": fetch_url, "code": -1, "msg": e})
        else:
            app_log.debug("{0}: {1}  Code: {2}  MSG: {3}".format(method.upper(), fetch_url, code, response_body.get('msg')))
            if is_log and body:
                app_log.info(escape.json_decode(body))
            raise Return(results)


    @coroutine
    def fetch_rows(self, url, is_log=False):
        results = yield self._fetch(url, is_log=is_log)
        raise Return(results)

    @coroutine
    def fetch_delete(self, url, is_log=False):
        results = yield self._fetch(url, 'delete', is_log=is_log)
        raise Return(results)

    @coroutine
    def fetch_post(self, url, body={}, is_log=False):
        results = yield self._fetch(url, 'post', body=json.dumps(body), is_log=is_log)
        if is_log:
            app_log.info(("the data of POST:", body))
        raise Return(results)

    @coroutine
    def fetch_put(self, url, body={}, is_log=False):
        results = yield self._fetch(url, 'put', body=json.dumps(body), is_log=is_log)
        if is_log:
            app_log.info(("the data of PUT:", body))
        raise Return(results)




LOCALHOST = '10.0.0.161'

MICROCLOUD_HOST = '10.0.0.119'

MICROCLOUD_HOST_S = {
    '10.0.0.118': '10.0.0.118',
    '10.0.0.119': '10.0.0.119',
    '10.0.0.252': '10.0.0.252',
}




CC_MODULES = {
    "compute": (LOCALHOST, 30001),
    "network": (LOCALHOST, 30002), 
    "api": (LOCALHOST, 30003),
    "webservices": (LOCALHOST, 30004)
}


def get_module_url(PART, module):
    _url, _port = PART[module]
    return "http://%s:%s/api/v1" %(_url, _port)


def get_microcloud_url(handler, module):
    remote_ip = handler.request.remote_ip
    fetch_host = MICROCLOUD_HOST_S.get(remote_ip, MICROCLOUD_HOST)

    MICROCLOUD_MODULES = {
        "webservices": (fetch_host, 30001),
        "compute": (fetch_host, 30002),
        "network": (fetch_host, 30003),
        "storage": (fetch_host, 30004),
        "images": (fetch_host, 30005)
    }
    _url, _port = MICROCLOUD_MODULES[module]
    return "http://%s:%s/api/v1" %(_url, _port)



# CC_MODULES 固定来着161
# from handlers.fetcher import cc_compute_fetcher, cc_network_fetcher
cc_compute_fetcher = Fetcher(get_module_url(CC_MODULES, "compute"))
cc_network_fetcher = Fetcher(get_module_url(CC_MODULES, "network"))
cc_api_fetcher = Fetcher(get_module_url(CC_MODULES, "api"))



# MICROCLOUD_MODULES 要根据请求的主机分发请求
# 在用到的文件夹中：在该handler里面使用
# 还是写到BaseProxyCCHandler作为内部属性使用吧！
# 这样还是没成功额

"""
from handlers.fetcher import Fetcher, get_microcloud_url

webservices_fetcher =  Fetcher(get_microcloud_url(self, 'webservices'))
compute_fetcher = Fetcher(get_microcloud_url(self, "compute"))
network_fetcher = Fetcher(get_microcloud_url(self, "network"))
storage_fetcher = Fetcher(get_microcloud_url(self, "storage"))
images_fetcher = Fetcher(get_microcloud_url(self, "images"))

"""


def webservices_fetcher(handler):
    return Fetcher(get_microcloud_url(handler, 'webservices'))

def compute_fetcher(handler):
    return Fetcher(get_microcloud_url(handler, 'compute'))

def network_fetcher(handler):
    return Fetcher(get_microcloud_url(handler, 'network'))

def storage_fetcher(handler):
    return Fetcher(get_microcloud_url(handler, 'storage'))

def images_fetcher(handler):
    return Fetcher(get_microcloud_url(handler, 'images'))
